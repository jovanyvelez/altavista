from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from .enums import RolUsuarioEnum

if TYPE_CHECKING:
    from .propietario import Propietario

class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=100, unique=True)
    email: str = Field(max_length=255, unique=True)
    hashed_password: str = Field(max_length=255)
    nombre_completo: Optional[str] = Field(default=None, max_length=255)
    rol: RolUsuarioEnum
    is_active: bool = Field(default=True)
    propietario_id: Optional[int] = Field(default=None, foreign_key="propietario.id")
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    propietario: Optional["Propietario"] = Relationship(back_populates="usuarios")

    def validate_propietario_constraint(self):
        """Valida que usuarios con rol propietario_consulta tengan propietario_id"""
        if self.rol == RolUsuarioEnum.PROPIETARIO_CONSULTA and not self.propietario_id:
            raise ValueError("Usuario con rol 'propietario_consulta' debe tener propietario_id")
        return self
