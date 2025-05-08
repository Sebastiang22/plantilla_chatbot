from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import Text


class MenuType(str, Enum):
    """
    Enum para los tipos de menú disponibles
    """
    CARTA = "carta"
    EJECUTIVO = "ejecutivo"


class MenuImage(SQLModel, table=True):
    """
    Modelo para almacenar las imágenes del menú en formato hexadecimal
    """
    __tablename__ = "menu_images"

    id: Optional[int] = Field(default=None, primary_key=True)
    tipo_menu: MenuType = Field(sa_column_kwargs={"nullable": False})
    image_hex: str = Field(sa_type=Text)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"nullable": False}) 