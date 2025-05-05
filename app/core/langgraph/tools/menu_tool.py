"""Herramienta para obtener el menú de un restaurante de comidas rápidas."""

from langchain_core.tools import tool

@tool
def get_menu() -> dict:
    """
    Devuelve el menú de un restaurante de comidas rápidas para pruebas.
    El menú incluye hamburguesas, papas, bebidas y combos.
    """
    return {
        "burgers": [
            {"name": "Hamburguesa Clásica", "price": 5.99},
            {"name": "Hamburguesa con Queso", "price": 6.49},
            {"name": "Hamburguesa Doble", "price": 7.99},
        ],
        "fries": [
            {"name": "Papas Pequeñas", "price": 2.49},
            {"name": "Papas Medianas", "price": 2.99},
            {"name": "Papas Grandes", "price": 3.49},
        ],
        "drinks": [
            {"name": "Gaseosa", "price": 1.99},
            {"name": "Jugo", "price": 2.49},
            {"name": "Agua", "price": 1.49},
        ],
        "combos": [
            {"name": "Combo Clásico", "items": ["Hamburguesa Clásica", "Papas Medianas", "Gaseosa"], "price": 9.99},
            {"name": "Combo Queso", "items": ["Hamburguesa con Queso", "Papas Grandes", "Jugo"], "price": 11.49},
        ]
    } 