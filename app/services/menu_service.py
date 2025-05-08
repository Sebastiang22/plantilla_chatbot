from typing import Optional
from sqlmodel import Session, select, delete

from models.menu_image import MenuImage, MenuType
from services.database import database_service


class MenuService:
    """
    Servicio para manejar las operaciones relacionadas con el menú
    """
    
    def __init__(self):
        """
        Inicializa el servicio de menú.
        """
        self.db = database_service

    async def insert_menu(self, image_hex: str, tipo_menu: MenuType = MenuType.EJECUTIVO) -> bool:
        """
        Inserta una nueva imagen de menú en la base de datos.
        Primero elimina los registros existentes del tipo especificado.

        Args:
            image_hex (str): Imagen del menú en formato hexadecimal
            tipo_menu (MenuType): Tipo de menú (carta o ejecutivo)

        Returns:
            bool: True si la operación fue exitosa, False en caso contrario
        """
        try:
            with Session(self.db.engine) as session:
                # Eliminar registros existentes del tipo especificado
                stmt = delete(MenuImage).where(MenuImage.tipo_menu == tipo_menu)
                session.execute(stmt)

                # Crear nuevo registro
                new_menu = MenuImage(
                    tipo_menu=tipo_menu,
                    image_hex=image_hex
                )
                session.add(new_menu)
                session.commit()
                return True
        except Exception as e:
            print(f"Error al insertar menú: {str(e)}")
            return False

    async def get_menu(self, tipo_menu: MenuType = MenuType.EJECUTIVO) -> Optional[MenuImage]:
        """
        Obtiene la imagen del menú más reciente del tipo especificado.

        Args:
            tipo_menu (MenuType): Tipo de menú a obtener

        Returns:
            Optional[MenuImage]: Imagen del menú o None si no existe
        """
        try:
            with Session(self.db.engine) as session:
                stmt = select(MenuImage).where(
                    MenuImage.tipo_menu == tipo_menu
                ).order_by(MenuImage.created_at.desc())
                result = session.exec(stmt)
                return result.first()
        except Exception as e:
            print(f"Error al obtener menú: {str(e)}")
            return None


# Crear una instancia singleton del servicio
menu_service = MenuService() 