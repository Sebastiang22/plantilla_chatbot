"""Endpoints for order management."""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from models.user import User
from models.order import Order
from sqlmodel import select, Session
from uuid import UUID
import logging
import httpx
import asyncio

from services.order_service import order_service
from services.database import database_service
from core.config import settings
from core.limiter import limiter
from core.logging import logger
from utils.utils import current_colombian_time
from schemas.order import OrderStatusUpdate, OrderResponse

router = APIRouter(tags=["orders"])

logger = logging.getLogger(__name__)

# URL del API de WhatsApp (configurado en settings o hardcoded por ahora)
WHATSAPP_API_URL = "http://localhost:3001/api/send-message"

async def send_whatsapp_notification(phone: str, message: str) -> bool:
    """Envía una notificación por WhatsApp al usuario.
    
    Args:
        phone: Número de teléfono del usuario (sin el prefijo @s.whatsapp.net)
        message: Mensaje a enviar
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        logger.info(f"Enviando notificación WhatsApp a {phone}: {message}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                WHATSAPP_API_URL,
                json={"number": phone, "message": message}
            )
            
            if response.status_code == 200:
                logger.info(f"Notificación WhatsApp enviada exitosamente a {phone}")
                return True
            else:
                logger.error(f"Error al enviar notificación WhatsApp: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Excepción al enviar notificación WhatsApp: {str(e)}")
        return False

@router.get("/by-date", response_model=Dict[str, Any])
async def get_orders_by_date(
    start_date: str = None,
    end_date: str = None
):
    """Obtiene las órdenes en un rango de fechas específico.
    
    Args:
        start_date: Fecha inicial en formato ISO (YYYY-MM-DD). Si no se especifica, 
                   se usará la fecha actual menos 30 días.
        end_date: Fecha final en formato ISO (YYYY-MM-DD). Si no se especifica,
                 se usará la fecha actual.
    
    Returns:
        Dict[str, Any]: Diccionario con estadísticas y lista de órdenes
    """
    try:
        # Convertir fechas o usar valores predeterminados (últimos 30 días)
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            # Usar la función current_colombian_time para obtener la fecha actual de Colombia
            current_time = current_colombian_time()
            # Convertir a objeto datetime para poder restar días
            current_datetime = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
            start = current_datetime - timedelta(days=30)
            
        if end_date:
            end = datetime.fromisoformat(end_date) + timedelta(days=1)  # Añadir 1 día para incluir toda la fecha final
        else:
            # Usar la función current_colombian_time para obtener la fecha actual de Colombia
            current_time = current_colombian_time()
            # Convertir a objeto datetime para poder sumar días
            current_datetime = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
            end = current_datetime + timedelta(days=1)  # Incluir órdenes de hoy
        
        # Obtener órdenes en el rango de fechas
        orders_data = await order_service.get_orders_by_date_range(start, end)
        
        # Obtener los nombres de los usuarios relacionados
        customer_phones = [order["customer_id"] for order in orders_data]
        with order_service.db.engine.connect() as conn:
            users = conn.execute(select(User).where(User.phone.in_(customer_phones))).fetchall()
            user_map = {user.phone: user.name for user in users}
        
        # Calcular estadísticas
        total_orders = len(orders_data)
        pending_orders = len([o for o in orders_data if o["status"] == "pendiente"])
        complete_orders = len([o for o in orders_data if o["status"] == "completado"])
        
        # Calcular ventas totales sumando los subtotales de los pedidos completados
        total_sales = 0
        for order in orders_data:
            if order["status"] == "completado":
                for product in order["products"]:
                    total_sales += float(product["subtotal"])
        
        return {
            "stats": {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "complete_orders": complete_orders,
                "total_sales": total_sales
            },
            "orders": [
                {
                    "id": order["order_id"],
                    "address": order["address"],
                    "customer_name": user_map.get(order["customer_id"], order["customer_id"]),
                    "products": [
                        {
                            "name": product["name"],
                            "quantity": product["quantity"],
                            "price": product["unit_price"],
                            "subtotal": product["subtotal"],
                            "details": product["details"]
                        }
                        for product in order["products"]
                    ],
                    "created_at": order["created_at"],
                    "updated_at": order["updated_at"],
                    "state": order["status"]
                }
                for order in orders_data
            ]
        }
    except Exception as e:
        logger.error(f"Error al obtener órdenes por fecha: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/today", response_model=Dict[str, Any])
async def get_today_orders():
    """Obtiene las órdenes del día actual.
    
    Returns:
        Dict[str, Any]: Diccionario con estadísticas y lista de órdenes
    """
    try:
        # Obtener todas las órdenes del día
        orders = await order_service.get_orders_today()
        
        # Obtener los nombres de los usuarios relacionados
        customer_phones = [order.customer_id for order in orders]
        with order_service.db.engine.connect() as conn:
            users = conn.execute(select(User).where(User.phone.in_(customer_phones))).fetchall()
            user_map = {user.phone: user.name for user in users}
        
        # Calcular estadísticas
        total_orders = len(orders)
        pending_orders = len([o for o in orders if o.status == "pendiente"])
        complete_orders = len([o for o in orders if o.status == "completado"])
        
        # Calcular ventas totales sumando los subtotales de los pedidos completados
        total_sales = 0
        for order in orders:
            if order.status == "completado":
                for item in order.items:
                    total_sales += item.unit_price * item.quantity
        
        return {
            "stats": {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "complete_orders": complete_orders,
                "total_sales": total_sales
            },
            "orders": [
                {
                    "id": str(order.id),
                    "address": order.address,
                    "customer_name": user_map.get(order.customer_id, order.customer_id),
                    "products": [
                        {
                            "name": item.product_name,
                            "quantity": item.quantity,
                            "price": item.unit_price
                        }
                        for item in order.items
                    ],
                    "created_at": order.created_at.isoformat(),
                    "updated_at": order.updated_at.isoformat(),
                    "state": order.status
                }
                for order in orders
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update_state")
async def update_order_state(status_update: OrderStatusUpdate):
    """Actualiza el estado de una orden.
    
    Args:
        status_update: Datos para actualizar el estado
        
    Returns:
        Dict[str, Any]: Respuesta con el resultado de la actualización
    """
    try:
        # Log de los datos recibidos
        logger.info(
            f"Actualizando estado de orden: {status_update.order_id} a {status_update.state}"
        )

        # Validar que el order_id sea un UUID válido
        try:
            order_uuid = UUID(status_update.order_id)
        except ValueError as e:
            logger.error(
                f"ID de orden inválido: {status_update.order_id} - Error: {str(e)}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"ID de orden inválido: {str(e)}"
            )

        # Validar que el estado sea uno de los permitidos
        valid_states = [
            "pending", "preparing", "completed",  # Estados en inglés
            "pendiente", "completado",  # Estados en español
            "en preparación", "en reparto"  # Agregamos los estados con formato español
        ]
        
        if status_update.state.lower() not in [s.lower() for s in valid_states]:
            logger.error(
                f"Estado inválido: {status_update.state}. Estados permitidos: {', '.join(valid_states)}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Estado inválido. Estados permitidos: {', '.join(valid_states)}"
            )

        # Obtener primero los datos de la orden para tener el número de teléfono
        with Session(order_service.db.engine) as session:
            order_before_update = session.get(Order, order_uuid)
            if not order_before_update:
                raise HTTPException(status_code=404, detail="Orden no encontrada")
            
            # Guardamos el customer_id (teléfono) y el estado anterior
            customer_phone = order_before_update.customer_id
            previous_state = order_before_update.status

        # Intentar actualizar el estado
        try:
            order = await order_service.update_order_status(order_uuid, status_update.state)
            
            # Obtener el nombre del cliente para personalizar el mensaje
            user_details = await database_service.get_user_details_with_latest_order(customer_phone)
            client_name = user_details.get("name") if user_details else "Cliente"
            
            # Crear mensaje según el nuevo estado
            status_name = order.status
            
            # Mapeo de estados a mensajes amigables
            status_messages = {
                "pendiente": f"¡Hola {client_name}! 👋 Tu pedido ha sido recibido y está pendiente de preparación. Te notificaremos cuando comience a prepararse.",
                "en preparación": f"¡Buenas noticias {client_name}! 👨‍🍳 Tu pedido ya está en preparación. Pronto estará listo para entrega.",
                "en reparto": f"¡Excelentes noticias {client_name}! 🚚 Tu pedido está en camino. Pronto llegará a tu dirección."
            }
            
            # Mensaje por defecto si no está en el mapeo
            notification_message = status_messages.get(
                status_name.lower(), 
                f"Hola {client_name}, el estado de tu pedido ha sido actualizado a: {status_name}"
            )
            
            # Solo enviar notificación si el estado cambió y NO es completado
            if previous_state.lower() != status_name.lower() and status_name.lower() != "completado":
                # Enviar notificación WhatsApp en segundo plano
                asyncio.create_task(send_whatsapp_notification(customer_phone, notification_message))
                notification_sent = True
            else:
                notification_sent = False
            
            logger.info(
                f"Estado de orden actualizado exitosamente: {str(order.id)} - Nuevo estado: {order.status}"
            )
            
            return {
                "message": "Estado actualizado correctamente",
                "order": {
                    "id": str(order.id),
                    "state": order.status,
                    "updated_at": order.updated_at.isoformat(),
                    "notification_sent": notification_sent
                }
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(
                f"Error al actualizar estado de orden {status_update.order_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Error al actualizar el estado de la orden: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error inesperado: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )

@router.delete("/{order_id}")
async def delete_order(order_id: str):
    """Elimina una orden.
    
    Args:
        order_id: ID de la orden a eliminar
        
    Returns:
        Dict[str, str]: Mensaje de confirmación
    """
    try:
        success = await order_service.delete_order(order_id)
        if not success:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        return {"message": f"Orden {order_id} eliminada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
