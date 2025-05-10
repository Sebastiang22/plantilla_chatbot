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