"""Herramienta para confirmar productos en la base de datos."""

from langchain_core.tools import tool
from services.order_service import OrderService
from services.database import database_service
import asyncio
from typing import List, Dict, Any
from sqlmodel import Session

@tool
def confirm_product(
    phone: str,
    name: str,
    address: str,
    products: List[Dict[str, Any]]
) -> dict:
    """
    Confirma múltiples productos en la base de datos creando un nuevo pedido.
    
    Args:
        phone: Teléfono del usuario
        name: Nombre del cliente
        address: Dirección de entrega
        products: Lista de diccionarios con la información de cada producto
                 Cada diccionario debe contener:
                 - product_name: Nombre del producto
                 - quantity: Cantidad del producto
                 - unit_price: Precio unitario del producto
                 - subtotal: Subtotal del item (quantity * unit_price)
        
    Returns:
        dict: Información del pedido creado con todos sus productos
    """
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
                "subtotal": item.subtotal
            }
            for item in order.items
        ]
    
    return {
        "order_id": str(order.id),
        "status": order.status,
        "total_amount": order.total_amount,
        "address": order.address,
        "products": items_data
    }

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