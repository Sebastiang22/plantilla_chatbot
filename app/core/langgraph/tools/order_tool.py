"""Herramienta para confirmar productos en la base de datos."""

from langchain_core.tools import tool
from services.order_service import OrderService
from services.database import database_service
import asyncio
from typing import List, Dict, Any
from sqlmodel import Session
from uuid import UUID

@tool
def confirm_product(
    phone: str,
    name: str,
    address: str,
    products: List[Dict[str, Any]]
) -> dict:
    """Confirma un pedido con los productos seleccionados.
    
    Args:
        phone: Número de teléfono del cliente
        name: Nombre del cliente
        address: Dirección de entrega
        products: Lista de productos con sus detalles
            Cada producto debe contener: product_name, quantity, unit_price, subtotal, details (opcional)
    
    Returns:
        dict: Resultado de la operación con los detalles del pedido
    """
    try:
        print(f"\033[96m[confirm_product] Procesando pedido para {name} (tel: {phone})\033[0m")
        
        # Validar la dirección - asegurar que no esté vacía
        if not address or address.strip() == "" or address.lower() == "no disponible":
            print(f"\033[93m[confirm_product] Dirección vacía o no disponible: '{address}'. Solicitando al usuario.\033[0m")
            return {
                "message": "Para completar tu pedido, necesito una dirección de entrega válida. ¿Podrías proporcionarme tu dirección por favor?",
                "status": "address_required"
            }
            
        print(f"\033[96m[confirm_product] Dirección recibida: '{address}'\033[0m")
        print(f"\033[96m[confirm_product] Productos: {products}\033[0m")
        
        # Actualizar el nombre del usuario
        user = asyncio.run(database_service.get_user_by_phone(phone))
        if user:
            asyncio.run(database_service.update_user_name(user.id, name))
        
        order_service = OrderService()
        order = asyncio.run(
            order_service.create_order(
                customer_id=phone,
                address=address,
                products=products
            )
        )
        
        # Cargar los items dentro de una nueva sesión
        with Session(database_service.engine) as session:
            session.add(order)
            session.refresh(order)
            items_data = [
                {
                    "name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal,
                    "details": item.details
                }
                for item in order.items
            ]
        
        # Loguear información de orden creada con dirección
        print(f"\033[96m[confirm_product] Orden creada - ID: {order.id}, Address: '{order.address}'\033[0m")
        
        return {
            "order_id": str(order.id),
            "status": order.status,
            "total_amount": order.total_amount,
            "address": order.address,
            "products": items_data
        }
    except Exception as e:
        print(f"\033[91m[confirm_product] Error: {str(e)}\033[0m")
        return {"message": f"Error al procesar el pedido: {str(e)}", "status": "error"}

@tool
def get_last_order(phone: str) -> dict:
    """
    Obtiene el estado y los productos de la última orden de un cliente.
        
    Returns:
        dict: Información de la última orden del cliente o mensaje indicando que no hay órdenes
    """
    order_service = OrderService()
    last_order = asyncio.run(order_service.get_last_order(phone))
    
    if not last_order:
        return {
            "message": "No se encontraron órdenes para este cliente",
            "has_orders": False
        }
    
    return {
        "message": "Se encontró la última orden del cliente",
        "has_orders": True,
        "order": last_order
    }

@tool
def add_products_to_order(phone: str, products: List[Dict[str, Any]]) -> dict:
    """
    Añade productos a la última orden existente del cliente.
    
    Args:
        phone: Teléfono del cliente
        products: Lista de diccionarios con la información de cada producto
                 Cada diccionario debe contener:
                 - product_name: Nombre del producto
                 - quantity: Cantidad del producto
                 - unit_price: Precio unitario del producto
                 - subtotal: Subtotal del item (quantity * unit_price)
                 - details: Observaciones o detalles específicos del producto (opcional)
        
    Returns:
        dict: Información actualizada de la orden con todos sus productos
    """
    try:
        order_service = OrderService()
        
        # Obtener la última orden del cliente
        last_order = asyncio.run(order_service.get_last_order(phone))
        if not last_order:
            return {
                "message": "No se encontró ninguna orden pendiente para este cliente",
                "error": True
            }
            
        # Verificar que la orden no esté en estado 'completed' o 'cancelled'
        if last_order['status'] in ['completed', 'cancelled']:
            return {
                "message": f"No se pueden añadir productos a una orden en estado '{last_order['status']}'",
                "error": True
            }
            
        # Añadir productos a la orden
        updated_order = asyncio.run(
            order_service.add_products_to_order(
                order_id=UUID(last_order['order_id']),
                products=products
            )
        )

        return {
            "message": "Productos añadidos exitosamente a la orden",
            "order": updated_order
        }
    except Exception as e:
        return {
            "message": f"Error al añadir productos a la orden: {str(e)}",
            "error": True
        }

@tool
def update_order_product(phone: str, product_name: str, new_data: Dict[str, Any]) -> dict:
    """
    Modifica los datos de un producto específico en la última orden del cliente.
    
    Args:
        phone: Teléfono del cliente
        product_name: Nombre del producto a modificar
        new_data: Diccionario con los nuevos datos del producto. Puede contener:
                 - quantity: Nueva cantidad (opcional)
                 - unit_price: Nuevo precio unitario (opcional)
                 - details: Nuevas observaciones (opcional)
        
    Returns:
        dict: Información actualizada de la orden con el producto modificado
    """
    try:
        order_service = OrderService()
        
        # Obtener la última orden del cliente
        last_order = asyncio.run(order_service.get_last_order(phone))
        if not last_order:
            return {
                "message": "No se encontró ninguna orden pendiente para este cliente",
                "error": True
            }
            
        # Verificar que la orden no esté en estado 'completed' o 'cancelled'
        if last_order['status'] in ['completed', 'cancelled']:
            return {
                "message": f"No se pueden modificar productos en una orden en estado '{last_order['status']}'",
                "error": True
            }
            
        # Modificar el producto en la orden
        updated_order = asyncio.run(
            order_service.update_order_product(
                order_id=UUID(last_order['order_id']),
                product_name=product_name,
                new_data=new_data
            )
        )

        return {
            "message": "Producto modificado exitosamente en la orden",
            "order": updated_order
        }
    except Exception as e:
        return {
            "message": f"Error al modificar el producto en la orden: {str(e)}",
            "error": True
        }