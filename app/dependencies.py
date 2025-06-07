from fastapi import HTTPException, status, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from typing import Optional
from app.models import db_manager, Usuario, Propietario, RolUsuarioEnum
from app.config import settings

# Configurar plantillas
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

def get_db_session() -> Session:
    """Obtener sesión de base de datos"""
    return db_manager.get_session()

def get_current_user(request: Request) -> Usuario:
    """Obtener el usuario actual desde la sesión"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )
    
    with get_db_session() as session:
        user = session.get(Usuario, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        return user

def require_admin(request: Request) -> Usuario:
    """Verificar que el usuario actual sea administrador"""
    user = get_current_user(request)
    if user.rol != RolUsuarioEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere permisos de administrador"
        )
    return user

def require_propietario(request: Request) -> tuple[Usuario, Propietario]:
    """Verificar que el usuario actual sea propietario"""
    user = get_current_user(request)
    if user.rol != RolUsuarioEnum.PROPIETARIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere permisos de propietario"
        )
    
    # Verificar que el usuario tenga propietario_id
    if not user.propietario_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no está asociado a ningún propietario"
        )
    
    with get_db_session() as session:
        propietario = session.get(Propietario, user.propietario_id)
        
        if not propietario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Propietario no encontrado"
            )
        
        return user, propietario
