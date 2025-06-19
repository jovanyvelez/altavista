from sqlmodel import SQLModel, Field, Relationship
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .apartamento import Apartamento

class CuotaConfiguracion(SQLModel, table=True):
    __tablename__ = "cuota_configuracion"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    apartamento_id: int = Field(foreign_key="apartamento.id")
    año: int
    mes: int = Field(ge=1, le=12)
    monto_cuota_ordinaria_mensual: Decimal = Field(decimal_places=2, max_digits=12)

    # Relaciones
    apartamento: "Apartamento" = Relationship(back_populates="cuotas_configuracion")
