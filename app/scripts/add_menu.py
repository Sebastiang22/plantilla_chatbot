from sqlmodel import SQLModel, create_engine, Session, select

def add_products_to_db():
    """
    Agrega los productos definidos a la tabla 'product' en la base de datos.
    """
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