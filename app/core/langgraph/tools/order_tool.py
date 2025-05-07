"""Herramienta para confirmar productos en la base de datos."""

from langchain_core.tools import tool
from services.order_service import OrderService
import asyncio

@tool
def confirm_product(
    phone: str,
    product_name: str,
    quantity: int,
    unit_price: float,
    subtotal: float
) -> dict:
    """
    Confirma un producto en la base de datos creando un nuevo pedido.
    
    Args:
        phone: Teléfono del usuario
        product_name: Nombre del producto
        quantity: Cantidad del producto
        unit_price: Precio unitario del producto
        subtotal: Subtotal del item (quantity * unit_price)
        
    Returns:
        dict: Información del pedido creado
    """
    order_service = OrderService()
    order = asyncio.run(
        order_service.create_order(
            customer_id=phone,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal
        )
    )
    
    return {
        "order_id": str(order.id),
        "status": order.status,
        "total_amount": order.total_amount,
        "product": {
            "name": product_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": subtotal
        }
    } 