"""Modelo de administrador para la autenticación en la aplicación."""

from datetime import datetime
from typing import Optional
from sqlmodel import Field
from passlib.hash import bcrypt
from models.base import BaseModel

class Admin(BaseModel, table=True):
    """Modelo de administrador para autenticación del sistema.

    Attributes:
        id: Clave primaria
        username: Nombre de usuario para el inicio de sesión (único)
        password_hash: Hash de la contraseña del administrador
        is_active: Indica si la cuenta está activa
        last_login: Última vez que inició sesión
    """
    
    __tablename__ = "admin"

    id: int = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str = Field()
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = Field(default=None, nullable=True)
    
    def verify_password(self, password: str) -> bool:
        """Verifica si la contraseña proporcionada coincide con el hash almacenado.

        Args:
            password: Contraseña en texto plano a verificar

        Returns:
            bool: True si la contraseña es correcta, False en caso contrario
        """
        return bcrypt.verify(password, self.password_hash)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Genera un hash seguro para la contraseña.

        Args:
            password: Contraseña en texto plano

        Returns:
            str: Hash de la contraseña
        """
        return bcrypt.hash(password) 