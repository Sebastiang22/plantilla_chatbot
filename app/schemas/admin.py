"""Esquemas para la autenticación de administradores."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, SecretStr

class AdminCreate(BaseModel):
    """Esquema para crear un nuevo administrador."""
    username: str = Field(..., min_length=3, max_length=50)
    password: SecretStr = Field(..., min_length=8)

class AdminResponse(BaseModel):
    """Esquema para respuestas con datos de administrador."""
    id: int
    username: str
    is_active: bool

class LoginRequest(BaseModel):
    """Esquema para solicitud de inicio de sesión."""
    username: str
    password: SecretStr

class TokenData(BaseModel):
    """Datos contenidos en el token JWT."""
    admin_id: int
    username: str
    exp: datetime 