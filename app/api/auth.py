"""Endpoints para la autenticación de administradores."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from schemas.admin import AdminCreate, AdminResponse, LoginRequest
from schemas.auth import TokenResponse
from models.admin import Admin
from services.auth_service import AuthService
from services.database import database_service

# Crear instancia del servicio de autenticación
auth_service = AuthService(database_service)

router = APIRouter(tags=["Autenticación"])

@router.post("/admin/register", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def register_admin(admin_data: AdminCreate):
    """Registra un nuevo administrador.
    
    Args:
        admin_data: Datos del nuevo administrador
        
    Returns:
        AdminResponse: Datos del administrador creado
    """
    admin = await auth_service.create_admin(admin_data)
    return AdminResponse(
        id=admin.id,
        username=admin.username,
        is_active=admin.is_active
    )

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint para iniciar sesión.
    
    Args:
        form_data: Formulario de inicio de sesión (username, password)
        
    Returns:
        TokenResponse: Token de acceso
        
    Raises:
        HTTPException: Si las credenciales son inválidas
    """
    login_request = LoginRequest(
        username=form_data.username,
        password=form_data.password
    )
    
    admin = await auth_service.authenticate_admin(login_request)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(admin["id"], admin["username"])
    expiration = datetime.utcnow() + timedelta(minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=expiration
    )

@router.get("/me", response_model=AdminResponse)
async def get_current_admin(admin: Admin = Depends(auth_service.get_current_admin)):
    """Obtiene la información del administrador autenticado.
    
    Args:
        admin: Administrador autenticado (inyectado por dependencia)
        
    Returns:
        AdminResponse: Datos del administrador autenticado
    """
    return AdminResponse(
        id=admin.id,
        username=admin.username,
        is_active=admin.is_active
    ) 