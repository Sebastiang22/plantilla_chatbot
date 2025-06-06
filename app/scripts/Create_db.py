import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse, urlunparse
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
from models import database  # noqa: F401

def get_db_urls():
    """
    Retorna dos URLs: una para la base con sufijo 'prod' y otra con 'dev'
    """
    base_url = settings.POSTGRES_URL
    parsed = urlparse(base_url)
    base_dbname = parsed.path.lstrip('/')

    prod_dbname = f"{base_dbname}_prod"
    dev_dbname = f"{base_dbname}_dev"

    prod_url = urlunparse(parsed._replace(path=f"/{prod_dbname}"))
    dev_url = urlunparse(parsed._replace(path=f"/{dev_dbname}"))

    return [(prod_dbname, prod_url), (dev_dbname, dev_url)]

def create_database_if_not_exists(dbname: str, postgres_url: str):
    """
    Crea una base de datos si no existe.
    """
    parsed = urlparse(postgres_url)
    # URL para conectar a la base `postgres`
    root_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}/postgres"

    try:
        conn = psycopg2.connect(root_url)
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        if cur.fetchone():
            print(f"ℹ️ La base de datos '{dbname}' ya existe.")
        else:
            print(f"➕ Creando base de datos '{dbname}'...")
            cur.execute(f'CREATE DATABASE "{dbname}"')
            print(f"✅ Base de datos '{dbname}' creada exitosamente.")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"❌ Error al crear/verificar la base de datos '{dbname}': {e}")
        sys.exit(1)

def create_all_tables(db_url: str):
    """
    Crea las tablas en la base de datos correspondiente.
    """
    print(f"⚙️ Creando tablas en: {db_url}")
    try:
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)
        engine.dispose()
        print("✅ Tablas creadas correctamente.")
    except Exception as e:
        print(f"❌ Error al crear tablas en {db_url}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Iniciando creación de bases de datos y tablas...")

    db_configs = get_db_urls()

    for dbname, db_url in db_configs:
        create_database_if_not_exists(dbname, db_url)
        create_all_tables(db_url)

    print("🎉 Proceso completado para ambas bases de datos.")