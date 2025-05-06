"""Herramienta para obtener el menú de un restaurante de comidas rápidas."""

from langchain_core.tools import tool
from services.inventory_service import InventoryService
import asyncio

@tool
def get_menu() -> dict:
    """
    Obtiene el menú de productos desde la base de datos, organizado por categorías.
    Retorna un diccionario con las categorías como claves y listas de productos como valores.
    """
    inventory_service = InventoryService()
    products = asyncio.run(inventory_service.get_menu_products())
    
    # Organizar productos por categoría
    menu_by_category = {}
    for product in products:
        category = product["category"]
        if category not in menu_by_category:
            menu_by_category[category] = []
        menu_by_category[category].append(product)
    
    return menu_by_category