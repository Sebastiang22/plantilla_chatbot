"""API endpoints para la gestión de órdenes."""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from models.user import User
from sqlmodel import select
from uuid import UUID
import logging

from services.order_service import order_service

router = APIRouter(tags=["orders"])

logger = logging.getLogger(__name__)

class OrderStatusUpdate(BaseModel):
    """Modelo para actualizar el estado de una orden."""
    order_id: str
    state: str

class OrderResponse(BaseModel):
    """Modelo de respuesta para una orden."""
    id: str
    address: str
    customer_name: str
    products: List[Dict[str, Any]]
    created_at: str
    updated_at: str
    state: str

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
        
        return {
            "stats": {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "complete_orders": complete_orders
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
            "pendiente", "preparando", "completado",  # Estados en español
            "en preparación"  # Agregamos el nuevo estado
        ]
        
        if status_update.state.lower() not in [s.lower() for s in valid_states]:
            logger.error(
                f"Estado inválido: {status_update.state}. Estados permitidos: {', '.join(valid_states)}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Estado inválido. Estados permitidos: {', '.join(valid_states)}"
            )

        # Intentar actualizar el estado
        try:
            order = await order_service.update_order_status(order_uuid, status_update.state)
            logger.info(
                f"Estado de orden actualizado exitosamente: {str(order.id)} - Nuevo estado: {order.status}"
            )
            return {
                "message": "Estado actualizado correctamente",
                "order": {
                    "id": str(order.id),
                    "state": order.status,
                    "updated_at": order.updated_at.isoformat()
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

@router.get("/ws-status")
async def check_websocket_status():
    """Verifica el estado del servidor WebSocket.
    
    Returns:
        Dict[str, bool]: Estado del servidor
    """
    try:
        # Aquí podrías implementar una verificación real del estado del WebSocket
        return {"status": "online"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 