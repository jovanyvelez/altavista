from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from app.models import db_manager, Usuario, RolUsuarioEnum
from app.dependencies import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Página de login"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Procesar login de usuario"""
    with db_manager.get_session() as session:
        user = session.exec(
            select(Usuario).where(Usuario.username == username)
        ).first()
        
        if not user or user.password != password:
            return templates.TemplateResponse(
                "login.html", 
                {
                    "request": request, 
                    "error": "Usuario o contraseña incorrectos"
                }
            )
        
        # Guardar usuario en sesión
        request.session["user_id"] = user.id
        request.session["user_role"] = user.rol.value
        
        # Redirigir según el rol
        if user.rol == RolUsuarioEnum.ADMIN:
            return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)
        else:
            return RedirectResponse(url="/propietario/dashboard", status_code=status.HTTP_302_FOUND)

@router.get("/logout")
async def logout(request: Request):
    """Cerrar sesión"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
