"""Esquemas Pydantic para las operaciones de órdenes."""

from typing import List, Dict, Any
from pydantic import BaseModel

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