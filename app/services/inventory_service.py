"""Servicio para la gestión del inventario de productos del restaurante."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select
from fastapi import HTTPException

from models.product import Product
from services.database import database_service

class InventoryService:
    """Servicio para la gestión del inventario.
    
    Este servicio maneja todas las operaciones relacionadas con el inventario
    de productos, incluyendo creación, consulta, actualización y eliminación
    de productos.
    """
    
    def __init__(self):
        """Inicializa el servicio de inventario."""
        self.db = database_service
    
    async def create_product(self, product_data: Dict[str, Any]) -> Product:
        """Crea un nuevo producto en el inventario.
        
        Args:
            product_data: Diccionario con los datos del producto:
                         name, description, price, category, stock
                  
        Returns:
            Product: El producto creado
            
        Raises:
            HTTPException: Si hay un error al crear el producto
        """
        try:
            with Session(self.db.engine) as session:
                product = Product(**product_data)
                session.add(product)
                session.commit()
                session.refresh(product)
                return product
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear el producto: {str(e)}")
    
    async def get_product(self, product_id: UUID) -> Optional[Product]:
        """Obtiene un producto por su ID.
        
        Args:
            product_id: ID del producto a consultar
            
        Returns:
            Optional[Product]: El producto si existe, None en caso contrario
        """
        with Session(self.db.engine) as session:
            return session.get(Product, product_id)
    
    async def get_available_products(self) -> List[Product]:
        """Obtiene todos los productos disponibles.
        
        Returns:
            List[Product]: Lista de productos disponibles
        """
        with Session(self.db.engine) as session:
            statement = select(Product).where(Product.is_available == True)
            return session.exec(statement).all()
    
    async def get_products_by_category(self, category: str) -> List[Product]:
        """Obtiene todos los productos de una categoría específica.
        
        Args:
            category: Categoría de los productos a consultar
            
        Returns:
            List[Product]: Lista de productos de la categoría
        """
        with Session(self.db.engine) as session:
            statement = select(Product).where(
                Product.category == category,
                Product.is_available == True
            )
            return session.exec(statement).all()
    
    async def update_product(self, product_id: UUID, product_data: Dict[str, Any]) -> Product:
        """Actualiza los datos de un producto.
        
        Args:
            product_id: ID del producto
            product_data: Diccionario con los datos a actualizar
            
        Returns:
            Product: El producto actualizado
            
        Raises:
            HTTPException: Si el producto no existe o hay un error al actualizarlo
        """
        with Session(self.db.engine) as session:
            product = session.get(Product, product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            
            for key, value in product_data.items():
                setattr(product, key, value)
            
            product.updated_at = datetime.utcnow()
            session.add(product)
            session.commit()
            session.refresh(product)
            return product
    
    async def update_stock(self, product_id: UUID, quantity: int) -> Product:
        """Actualiza el stock de un producto.
        
        Args:
            product_id: ID del producto
            quantity: Nueva cantidad en stock
            
        Returns:
            Product: El producto actualizado
            
        Raises:
            HTTPException: Si el producto no existe o hay un error al actualizarlo
        """
        with Session(self.db.engine) as session:
            product = session.get(Product, product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            
            product.stock = quantity
            product.updated_at = datetime.utcnow()
            session.add(product)
            session.commit()
            session.refresh(product)
            return product
    
    async def delete_product(self, product_id: UUID) -> bool:
        """Elimina un producto del inventario.
        
        Args:
            product_id: ID del producto a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False si no existe
            
        Raises:
            HTTPException: Si hay un error al eliminar el producto
        """
        try:
            with Session(self.db.engine) as session:
                product = session.get(Product, product_id)
                if not product:
                    return False
                
                session.delete(product)
                session.commit()
                return True
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al eliminar el producto: {str(e)}")

# Crear una instancia singleton del servicio
inventory_service = InventoryService() 