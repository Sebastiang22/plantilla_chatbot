"""Servicio para la gestión de pedidos del restaurante."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select
from fastapi import HTTPException

from models.order import Order, OrderItem
from services.database import database_service

class OrderService:
    """Servicio para la gestión de pedidos.
    
    Este servicio maneja todas las operaciones relacionadas con pedidos,
    incluyendo creación, consulta, actualización y eliminación.
    """
    
    def __init__(self):
        """Inicializa el servicio de pedidos."""
        self.db = database_service
    
    async def create_order(self, customer_id: str, product_name: str, quantity: int, unit_price: float, subtotal: float) -> Order:
        """Crea un nuevo pedido con un item.
        
        Args:
            customer_id: ID del cliente
            product_name: Nombre del producto
            quantity: Cantidad del producto
            unit_price: Precio unitario del producto
            subtotal: Subtotal del item (quantity * unit_price)
                  
        Returns:
            Order: El pedido creado con su item
            
        Raises:
            HTTPException: Si hay un error al crear el pedido
        """
        try:
            with Session(self.db.engine) as session:
                # Crear el pedido
                order = Order(customer_id=customer_id)
                session.add(order)
                session.flush()  # Para obtener el ID del pedido
                
                # Crear el item del pedido
                order_item = OrderItem(
                    order_id=order.id,
                    product_id="",  # No tenemos el ID del producto, solo el nombre
                    product_name=product_name,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=subtotal
                )
                session.add(order_item)
                
                # Actualizar el monto total del pedido
                order.total_amount = subtotal
                session.add(order)
                
                session.commit()
                session.refresh(order)
                return order
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear el pedido: {str(e)}")
    
    async def get_order(self, order_id: UUID) -> Optional[Order]:
        """Obtiene un pedido por su ID.
        
        Args:
            order_id: ID del pedido a consultar
            
        Returns:
            Optional[Order]: El pedido si existe, None en caso contrario
        """
        with Session(self.db.engine) as session:
            return session.get(Order, order_id)
    
    async def get_customer_orders(self, customer_id: str) -> List[Order]:
        """Obtiene todos los pedidos de un cliente.
        
        Args:
            customer_id: ID del cliente
            
        Returns:
            List[Order]: Lista de pedidos del cliente
        """
        with Session(self.db.engine) as session:
            statement = select(Order).where(Order.customer_id == customer_id)
            return session.exec(statement).all()
    
    async def update_order_status(self, order_id: UUID, status: str) -> Order:
        """Actualiza el estado de un pedido.
        
        Args:
            order_id: ID del pedido
            status: Nuevo estado del pedido
            
        Returns:
            Order: El pedido actualizado
            
        Raises:
            HTTPException: Si el pedido no existe o hay un error al actualizarlo
        """
        with Session(self.db.engine) as session:
            order = session.get(Order, order_id)
            if not order:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")
            
            order.status = status
            order.updated_at = datetime.utcnow()
            session.add(order)
            session.commit()
            session.refresh(order)
            return order
    
    async def delete_order(self, order_id: UUID) -> bool:
        """Elimina un pedido y sus items.
        
        Args:
            order_id: ID del pedido a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False si no existe
            
        Raises:
            HTTPException: Si hay un error al eliminar el pedido
        """
        try:
            with Session(self.db.engine) as session:
                order = session.get(Order, order_id)
                if not order:
                    return False
                
                # Eliminar los items del pedido
                statement = select(OrderItem).where(OrderItem.order_id == order_id)
                items = session.exec(statement).all()
                for item in items:
                    session.delete(item)
                
                # Eliminar el pedido
                session.delete(order)
                session.commit()
                return True
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al eliminar el pedido: {str(e)}")

# Crear una instancia singleton del servicio
order_service = OrderService() 