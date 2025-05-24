import os
import sys
from dotenv import load_dotenv

# Agregar el directorio raíz de la aplicación al PYTHONPATH
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(app_dir)

# Cargar variables de entorno manualmente
# Subir un nivel desde scripts para encontrar .env.development en la carpeta app
dotenv_path = os.path.join(app_dir, ".env.development")
load_dotenv(dotenv_path=dotenv_path)

from sqlmodel import SQLModel, create_engine
from core.config import settings

# Importa todos los modelos para que SQLModel los registre
from models import database  # noqa: F401

def create_all_tables():
    """
    Crea todas las tablas definidas en los modelos de la base de datos.
    """
    print("POSTGRES_URL:", settings.POSTGRES_URL)
    engine = create_engine(settings.POSTGRES_URL)
    SQLModel.metadata.create_all(engine)
    print("Todas las tablas han sido creadas correctamente.")

if __name__ == "__main__":
    create_all_tables() 