from fastapi import UploadFile
from pathlib import Path
from uuid import uuid4
import shutil
from app.config import settings

def guardar_documento(archivo: UploadFile, carpeta: str = "") -> str:
    """
    Guarda un documento subido por el usuario y retorna la ruta relativa al archivo
    
    Args:
        archivo: Archivo subido por el usuario
        carpeta: Subcarpeta opcional donde guardar el archivo
    
    Returns:
        str: Ruta relativa al archivo guardado
    """
    # Crear directorio si no existe
    dir_path = settings.UPLOADS_DIR / carpeta
    dir_path.mkdir(exist_ok=True)
    
    # Generar nombre único para el archivo
    filename = f"{uuid4()}_{archivo.filename}"
    file_path = dir_path / filename
    
    # Guardar el archivo
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
    
    # Retornar ruta relativa para guardar en la base de datos
    return str(Path(carpeta) / filename)

def obtener_ruta_documento(ruta_relativa: str) -> Path:
    """
    Convierte una ruta relativa almacenada en la base de datos a una ruta absoluta
    
    Args:
        ruta_relativa: Ruta relativa del archivo
    
    Returns:
        Path: Ruta absoluta al archivo
    """
    return settings.UPLOADS_DIR / ruta_relativa
