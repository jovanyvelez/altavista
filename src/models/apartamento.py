from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .propietario import Propietario
    from .cuota_configuracion import CuotaConfiguracion
    from .registro_financiero_apartamento import RegistroFinancieroApartamento

class Apartamento(SQLModel, table=True):
    __tablename__ = "apartamento"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    identificador: str = Field(max_length=50, unique=True)
    coeficiente_copropiedad: Decimal = Field(decimal_places=6, max_digits=8)
    propietario_id: Optional[int] = Field(default=None, foreign_key="propietario.id")
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    propietario: Optional["Propietario"] = Relationship(back_populates="apartamentos")
    cuotas_configuracion: List["CuotaConfiguracion"] = Relationship(back_populates="apartamento")
    registros_financieros: List["RegistroFinancieroApartamento"] = Relationship(back_populates="apartamento")
