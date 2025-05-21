"""Servicio de autenticación para administradores del restaurante."""

from typing import Optional
from datetime import datetime, timedelta
from sqlmodel import Session, select
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from core.config import settings
from models.admin import Admin
from schemas.admin import AdminCreate, LoginRequest, TokenData
from services.database import DatabaseService

# Crear instancia de OAuth2PasswordBearer para obtener el token de los headers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

class AuthService:
    """Servicio para la gestión de autenticación de administradores."""
    
    def __init__(self, db_service: DatabaseService):
        """Inicializa el servicio de autenticación.
        
        Args:
            db_service: Servicio de base de datos
        """
        self.db = db_service
        self.SECRET_KEY = settings.JWT_SECRET_KEY
        self.ALGORITHM = settings.JWT_ALGORITHM
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS  # Días a minutos
    
    async def create_admin(self, admin_data: AdminCreate) -> Admin:
        """Crea un nuevo administrador.
        
        Args:
            admin_data: Datos del administrador a crear
            
        Returns:
            Admin: El administrador creado
            
        Raises:
            HTTPException: Si ya existe un administrador con ese username
        """
        with Session(self.db.engine) as session:
            # Verificar si ya existe el username
            username_exists = session.exec(
                select(Admin).where(Admin.username == admin_data.username)
            ).first()
            
            if username_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El nombre de usuario ya está en uso"
                )
            
            # Crear el nuevo administrador
            new_admin = Admin(
                username=admin_data.username,
                password_hash=Admin.hash_password(admin_data.password.get_secret_value()),
                is_active=True
            )
            
            session.add(new_admin)
            session.commit()
            session.refresh(new_admin)
            return new_admin
    
    async def authenticate_admin(self, login_data: LoginRequest) -> Optional[dict]:
        """Autentica a un administrador y retorna un dict plano con los datos necesarios."""
        with Session(self.db.engine) as session:
            admin = session.exec(
                select(Admin).where(Admin.username == login_data.username)
            ).first()
            
            if not admin or not admin.verify_password(login_data.password.get_secret_value()):
                return None
            
            # Actualizar última fecha de inicio de sesión
            admin.last_login = datetime.utcnow()
            session.add(admin)
            session.commit()
            
            # Retornar un dict plano con los datos necesarios
            return {
                "id": admin.id,
                "username": admin.username,
                "is_active": admin.is_active
            }
    
    def create_access_token(self, admin_id: int, username: str) -> str:
        """Crea un token JWT de acceso.
        
        Args:
            admin_id: ID del administrador
            username: Nombre de usuario del administrador
            
        Returns:
            str: Token JWT generado
        """
        expiration = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = TokenData(
            admin_id=admin_id,
            username=username,
            exp=expiration
        ).model_dump()
        
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
    
    async def get_current_admin(self, token: str = Depends(oauth2_scheme)) -> Admin:
        """Obtiene el administrador actual a partir del token JWT.
        
        Args:
            token: Token JWT de autenticación
            
        Returns:
            Admin: El administrador autenticado
            
        Raises:
            HTTPException: Si el token es inválido o el administrador no existe
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            admin_id: int = payload.get("admin_id")
            
            if admin_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        with Session(self.db.engine) as session:
            admin = session.get(Admin, admin_id)
            
            if admin is None:
                raise credentials_exception
            
            if not admin.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cuenta de administrador inactiva"
                )
                
            return admin 