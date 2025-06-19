from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .apartamento import Apartamento
    from .usuario import Usuario

class Propietario(SQLModel, table=True):
    __tablename__ = "propietario"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_completo: str = Field(max_length=255)
    documento_identidad: str = Field(max_length=50, unique=True)
    email: Optional[str] = Field(default=None, max_length=255, unique=True)
    telefono: Optional[str] = Field(default=None, max_length=50)
    datos_adicionales: Optional[str] = None
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    apartamentos: List["Apartamento"] = Relationship(back_populates="propietario")
    usuarios: List["Usuario"] = Relationship(back_populates="propietario")
