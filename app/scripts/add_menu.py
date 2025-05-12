from sqlmodel import SQLModel, create_engine, Session, select
from models.product import Product
from core.config import settings

def add_products_to_db():
    """
    Agrega los productos definidos a la tabla 'product' en la base de datos.
    """
    productos = [

        # Menú a la carta
        {
            "name": "Churrasco + chorizo",
            "description": "300 grs + chorizo, sopa o crema del día, arroz blanco, jugo, ensalada natural",
            "price": 42000,
            "category": "a la carta"
        },
        {
            "name": "Salmón chileno",
            "description": "200 grs, ensalada natural, jugo, arroz blanco, sopa o crema del día, tostón",
            "price": 42000,
            "category": "a la carta"
        },
        {
            "name": "Punta de anca de cerdo",
            "description": "300 grs, arroz, ensalada natural, jugo, tostón, sopa o crema",
            "price": 30000,
            "category": "a la carta"
        },
        {
            "name": "Mojarra frita",
            "description": "300 grs, arroz blanco, sopa o crema del día, jugo, arroz, ensalada del día",
            "price": 32000,
            "category": "a la carta"
        },
        {
            "name": "Filete de trucha",
            "description": "Ensalada natural, arroz, sopa o crema del día, jugo, acompañante",
            "price": 20000,
            "category": "a la carta"
        },
        
        # Menú de bebidas
        {
            "name": "Soda en botella",
            "description": "Soda en botella",
            "price": 5000,
            "category": "bebida"
        },
        {
            "name": "Hatsu Green Tea & Kiwi",
            "description": "Té verde con kiwi",
            "price": 7000,
            "category": "bebida"
        },
        {
            "name": "Hatsu Roses Tea & Lychee",
            "description": "Té de rosas con lichi",
            "price": 7000,
            "category": "bebida"
        },
        {
            "name": "Hatsu White Tea & Mangosteen",
            "description": "Té blanco con mangostán",
            "price": 7000,
            "category": "bebida"
        },
        {
            "name": "Hatsu Blue Pomegranate Tea & Açai",
            "description": "Té de granada azul con açai",
            "price": 7000,
            "category": "bebida"
        },
        {
            "name": "Hatsu Pu-Erh Red Tea",
            "description": "Mezcla de tés rojos con frutos rojos",
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