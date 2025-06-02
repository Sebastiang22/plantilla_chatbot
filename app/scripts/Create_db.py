import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse
from sqlmodel import SQLModel, create_engine
from psycopg2 import extensions

# Establecer ruta base del proyecto
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(app_dir)

# Cargar variables del entorno desde .env.development
dotenv_path = os.path.join(app_dir, ".env.development")
if not os.path.exists(dotenv_path):
    print(f"❌ Archivo de entorno no encontrado en: {dotenv_path}")
    sys.exit(1)
load_dotenv(dotenv_path=dotenv_path)

from core.config import settings
from models import database  # noqa: F401 - Asegura que los modelos se registren

def create_database_if_not_exists():
    """
    Crea la base de datos si no existe.
    """
    if not settings.POSTGRES_URL:
        raise ValueError("❌ POSTGRES_URL no está configurada correctamente.")

    parsed = urlparse(settings.POSTGRES_URL)
    dbname = parsed.path.lstrip('/')

    postgres_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}/postgres"

    conn = None
    cur = None

    try:
        conn = psycopg2.connect(postgres_url)
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)  # ✅ Evita transacciones
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        exists = cur.fetchone()

        if exists:
            print(f"ℹ️ La base de datos '{dbname}' ya existe.")
        else:
            print(f"➕ Creando base de datos '{dbname}'...")
            cur.execute(f'CREATE DATABASE "{dbname}"')
            print(f"✅ Base de datos '{dbname}' creada exitosamente.")

    except psycopg2.Error as e:
        print(f"❌ Error de PostgreSQL: {e}")
        sys.exit(1)

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def create_all_tables():
    """
    Crea las tablas definidas en los modelos.
    """
    print("⚙️ Creando tablas en la base de datos...")
    try:
        engine = create_engine(settings.POSTGRES_URL)
        SQLModel.metadata.create_all(engine)
        print("✅ Todas las tablas han sido creadas correctamente.")
    except Exception as e:
        print(f"❌ Error al crear las tablas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Iniciando proceso de creación de base de datos...")
    create_database_if_not_exists()
    create_all_tables()