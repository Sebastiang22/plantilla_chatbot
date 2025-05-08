from sqlmodel import SQLModel, create_engine
from app.core.config import settings

# Importa todos los modelos para que SQLModel los registre
from app.models import database  # noqa: F401

def create_all_tables():
    """
    Crea todas las tablas definidas en los modelos de la base de datos.
    """
    engine = create_engine(settings.POSTGRES_URL)
    SQLModel.metadata.create_all(engine)
    print("Todas las tablas han sido creadas correctamente.")

if __name__ == "__main__":
    create_all_tables() 