from pathlib import Path

class Settings:
    """Configuración de la aplicación"""
    
    # Información de la aplicación
    APP_TITLE: str = "Sistema de Gestión Edificio Residencial"
    APP_DESCRIPTION: str = "Sistema para la administración de zonas comunes de edificios residenciales"
    APP_VERSION: str = "0.1.0"
    
    # Directorios
    STATIC_DIR: str = "static"
    TEMPLATES_DIR: str = "templates"
    UPLOADS_DIR: Path = Path("static/uploads")
    
    def __init__(self):
        # Crear directorios necesarios
        self.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
