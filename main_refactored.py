from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

# Importar configuración y servicios
from app.config import settings
from app.models import db_manager
from app.services.initial_data import crear_datos_iniciales

# Importar rutas
from app.routes import auth_router, admin_router, admin_pagos_router, propietario_router

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION
)

# Agregar middleware de sesiones
app.add_middleware(SessionMiddleware, secret_key="tu_clave_secreta_aqui")

# Configurar archivos estáticos
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Incluir rutas
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_pagos_router)
app.include_router(propietario_router)

# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_event():
    """Inicializar base de datos y datos de prueba"""
    db_manager.create_tables()
    await crear_datos_iniciales()

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar la aplicación"""
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
