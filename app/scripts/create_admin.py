"""Script para crear un administrador inicial en la base de datos."""

import argparse
import sys
import os
from sqlmodel import Session, create_engine
from passlib.hash import bcrypt
from dotenv import load_dotenv

# Subir un nivel desde scripts para encontrar .env.development en la carpeta app
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env.development")
load_dotenv(dotenv_path=dotenv_path)

from models.admin import Admin
from core.config import settings

def create_admin(username: str, password: str):
    """Crea un nuevo administrador en la base de datos.
    
    Args:
        username: Nombre de usuario del administrador
        password: Contraseña del administrador
    """
    # Crear conexión a la base de datos
    engine = create_engine(settings.POSTGRES_URL)
    
    # Verificar si ya existe un administrador con ese username
    with Session(engine) as session:
        admin_by_username = session.query(Admin).filter(Admin.username == username).first()
        if admin_by_username:
            print(f"Ya existe un administrador con el nombre de usuario '{username}'")
            return
        
        # Crear el administrador
        new_admin = Admin(
            username=username,
            password_hash=bcrypt.hash(password),
            is_active=True
        )
        
        # Guardar en la base de datos
        session.add(new_admin)
        session.commit()
        print(f"Administrador '{username}' creado exitosamente")

def main():
    """Punto de entrada principal del script."""
    parser = argparse.ArgumentParser(description="Crear un administrador inicial")
    parser.add_argument("--username", required=True, help="Nombre de usuario del administrador")
    parser.add_argument("--password", required=True, help="Contraseña del administrador")
    
    args = parser.parse_args()
    
    create_admin(args.username, args.password)

if __name__ == "__main__":
    main() 