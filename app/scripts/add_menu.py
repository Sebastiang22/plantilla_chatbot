import os
from dotenv import load_dotenv

# Cargar variables de entorno antes de cualquier otro import
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env.development")
load_dotenv(dotenv_path=dotenv_path)

from sqlmodel import SQLModel, create_engine, Session, select
from models.product import Product
from core.config import settings

def add_products_to_db():
    """
    Agrega los productos definidos a la tabla 'product' en la base de datos.
    """
    productos = [
        
        # Menú de bebidas
        {
            "name": "Soda en botella",
            "description": "Soda en botella",
            "price": 5000,
            "category": "bebida"
        },
        {
            "name": "Hatsu",
            "description": "Té hatsu",
            "price": 7000,
            "category": "bebida"
        },

        {
            "name": "Red Bull lata",
            "description": "Energizante Red Bull en lata",
            "price": 8000,
            "category": "bebida"
        },
        {
            "name": "Andina cerveza botella",
            "description": "Cerveza Andina en botella",
            "price": 5000,
            "category": "bebida"
        },
        {
            "name": "Agua con gas cristal",
            "description": "Agua con gas cristal",
            "price": 4000,
            "category": "bebida"
        },
        {
            "name": "Agua sin gas",
            "description": "Agua sin gas",
            "price": 3000,
            "category": "bebida"
        },
        {
            "name": "Jugo Hit Mango 500 ml",
            "description": "Jugo Hit sabor mango",
            "price": 4000,
            "category": "bebida"
        },
        {
            "name": "Jugo Hit Lulo 500 ml",
            "description": "Jugo Hit sabor lulo",
            "price": 4000,
            "category": "bebida"
        },
        {
            "name": "Jugo Hit Frutas tropicales 500 ml",
            "description": "Jugo Hit sabor fruta tropical",
            "price": 4000,
            "category": "bebida"
        },
        {
            "name": "Jugo Hit Naranja Piña 500 ml",
            "description": "Jugo Hit sabor naranja piña",
            "price": 4000,
            "category": "bebida"
        },
        {
            "name": "Mister Té lima limón",
            "description": "Mister Té sabor lima limón",
            "price": 5000,
            "category": "bebida"
        },
        {
            "name": "Mister Té durazno",
            "description": "Mister Té sabor durazno",
            "price": 5000,
            "category": "bebida"
        },
        {
            "name": "Gatorade",
            "description": "Bebida Gatorade",
            "price": 5000,
            "category": "bebida"
        },
        {
            "name": "Postobon Uva 400ml",
            "description": "Gaseosa Postobon sabor Uva en botella PET 400ml",
            "price": 3000,
            "category": "bebida"
        },
        {
            "name": "Postobon Naranja 400ml",
            "description": "Gaseosa Postobon sabor Naranja en botella PET 400ml",
            "price": 3000,
            "category": "bebida"
        },
        {
            "name": "Postobon Colombiana 400ml",
            "description": "Gaseosa Postobon sabor Colombiana en botella PET 400ml",
            "price": 3000,
            "category": "bebida"
        }
    ]

    engine = create_engine(settings.POSTGRES_URL)
    with Session(engine) as session:
        for prod in productos:
            exists = session.exec(
                select(Product).where(Product.name == prod["name"])
            ).first()
            if not exists:
                product = Product(
                    name=prod["name"],
                    description=prod["description"],
                    price=prod["price"],
                    category=prod["category"],
                )
                session.add(product)
                print(f"Producto agregado: {prod['name']} ({prod['category']})")
            else:
                print(f"Producto ya existe: {prod['name']} ({prod['category']})")
        session.commit()
        print("Todos los productos han sido procesados.")

if __name__ == "__main__":
    add_products_to_db()

