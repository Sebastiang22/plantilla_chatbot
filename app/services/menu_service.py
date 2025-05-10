from typing import Optional, List, Dict
from sqlmodel import Session, select, delete

from models.menu_image import MenuImage, MenuType
from models.product import Product
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

    async def get_menu(self, tipo_menu: MenuType = None) -> List[MenuImage]:
        """
        Obtiene todas las imágenes del menú, ordenadas por fecha de creación.
        Si se especifica un tipo de menú, filtra por ese tipo.

        Args:
            tipo_menu (MenuType, optional): Tipo de menú a filtrar. Si es None, obtiene todos los tipos.

        Returns:
            List[MenuImage]: Lista de imágenes del menú ordenadas por fecha de creación (más reciente primero)
        """
        try:
            with Session(self.db.engine) as session:
                query = select(MenuImage)
                
                # Solo aplicar el filtro si se especifica un tipo de menú
                if tipo_menu is not None:
                    query = query.where(MenuImage.tipo_menu == tipo_menu)
                
                # Ordenar por fecha de creación (más reciente primero)
                query = query.order_by(MenuImage.created_at.desc())
                
                result = session.exec(query)
                return list(result.all())
        except Exception as e:
            print(f"Error al obtener menú: {str(e)}")
            return []

    async def process_menu_data(self, menu_data: Dict) -> bool:
        """
        Procesa los datos del menú y los guarda en la tabla de productos.
        Primero elimina todos los productos existentes con categoría 'Menú Ejecutivo'.

        Args:
            menu_data (Dict): Datos del menú extraídos por OpenAI

        Returns:
            bool: True si la operación fue exitosa, False en caso contrario
        """
        try:
            with Session(self.db.engine) as session:
                # Eliminar productos existentes con categoría 'Menú Ejecutivo'
                stmt = delete(Product).where(Product.category == 'Menú Ejecutivo')
                session.execute(stmt)

                # Obtener la lista de menús
                menu_items = menu_data.get('menu', [])
                if not menu_items:
                    print("No se encontraron elementos en el menú")
                    return False

                # Crear nuevos productos
                for item in menu_items:
                    # Intentar obtener los datos con diferentes nombres de campos
                    name = item.get('name') or item.get('nombre')
                    description = item.get('description') or item.get('descripcion')
                    price = item.get('price') or item.get('precio')
                    category = item.get('category') or item.get('categoria')

                    # Verificar que todos los campos necesarios estén presentes
                    if not all([name, description, price, category]):
                        print(f"Faltan campos requeridos en el item: {item}")
                        continue

                    try:
                        new_product = Product(
                            name=name,
                            description=description,
                            price=float(price),
                            category=category,
                            stock=100,  # Stock por defecto
                            is_available=True
                        )
                        session.add(new_product)
                    except (ValueError, TypeError) as e:
                        print(f"Error al procesar el item {item}: {str(e)}")
                        continue

                session.commit()
                return True
        except Exception as e:
            print(f"Error al procesar datos del menú: {str(e)}")
            return False


# Crear una instancia singleton del servicio
menu_service = MenuService() 