"""Modelo de usuario para la aplicación."""

from typing import List
from sqlmodel import Field, Relationship
from models.base import BaseModel

class User(BaseModel, table=True):
    """Modelo de usuario para almacenar cuentas de usuarios.
    
    Attributes:
        id: Clave primaria
        name: Nombre del usuario
        phone: Número de celular del usuario (único)
        threads: Relación con los hilos de conversación del usuario
    """
    
    __tablename__ = "user"  # Explicitly set table name
    
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    phone: str = Field(unique=True, index=True)
    threads: List["Thread"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

# Evitar importaciones circulares
from models.thread import Thread  # noqa: E402
