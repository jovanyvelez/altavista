from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager


# Importar configuración y servicios
from src.config import settings
from src.models import db_manager
from src.services.initial_data import crear_datos_iniciales

# Importar rutas
from src.routes import auth_router, admin_router, admin_pagos_router, propietario_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializar base de datos y datos de prueba"""
    db_manager.create_tables()
    await crear_datos_iniciales()
    yield
    """Limpieza al cerrar la aplicación"""
    pass

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Agregar middleware de sesiones
app.add_middleware(SessionMiddleware, secret_key="building-management-secret-key-2024")

# Configurar archivos estáticos
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Incluir rutas
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_pagos_router)
app.include_router(propietario_router)

# Eventos de inicio y cierre