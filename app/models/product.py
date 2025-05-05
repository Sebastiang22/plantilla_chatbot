"""Modelos para la gestión de productos del restaurante."""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from uuid import UUID, uuid4

class Product(SQLModel, table=True):
    """Modelo para la tabla de productos.
    
    Attributes:
        id: Identificador único del producto
        name: Nombre del producto
        description: Descripción detallada del producto
        price: Precio del producto
        category: Categoría del producto (entrada, plato principal, postre, bebida, etc.)
        stock: Cantidad disponible en inventario
        is_available: Indica si el producto está disponible para pedidos
        created_at: Fecha y hora de creación del registro
        updated_at: Fecha y hora de última actualización del registro
    """
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    description: str
    price: float
    category: str = Field(index=True)
    stock: int = Field(default=0)
    is_available: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) 