"""Modelos para la gestión de pedidos del restaurante."""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from uuid import UUID, uuid4

class Order(SQLModel, table=True):
    """Modelo para la tabla de pedidos.
    
    Attributes:
        id: Identificador único del pedido
        customer_id: ID del cliente que realizó el pedido
        status: Estado actual del pedido (pending, preparing, ready, delivered, cancelled)
        total_amount: Monto total del pedido
        created_at: Fecha y hora de creación del pedido
        updated_at: Fecha y hora de última actualización del pedido
    """
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_id: str = Field(index=True)
    status: str = Field(default="pending")
    total_amount: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relación con los items del pedido
    items: list["OrderItem"] = Relationship(back_populates="order")

class OrderItem(SQLModel, table=True):
    """Modelo para la tabla de items de pedido.
    
    Attributes:
        id: Identificador único del item
        order_id: ID del pedido al que pertenece
        product_id: ID del producto
        product_name: Nombre del producto
        quantity: Cantidad del producto
        unit_price: Precio unitario del producto
        subtotal: Subtotal del item (quantity * unit_price)
    """
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_id: UUID = Field(foreign_key="order.id", index=True)
    product_id: str = Field(index=True)
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    
    # Relación con el pedido
    order: Order = Relationship(back_populates="items") 