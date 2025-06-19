from sqlmodel import SQLModel, Field, Relationship
from datetime import date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .concepto import Concepto
    from .presupuesto_anual import PresupuestoAnual

class GastoComunidad(SQLModel, table=True):
    __tablename__ = "gasto_comunidad"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_gasto: date
    concepto_id: int = Field(foreign_key="concepto.id")
    descripcion_adicional: Optional[str] = None
    monto: Decimal = Field(decimal_places=2, max_digits=12)
    documento_soporte_path: Optional[str] = Field(default=None, max_length=512)
    presupuesto_anual_id: Optional[int] = Field(default=None, foreign_key="presupuesto_anual.id")
    mes_gasto: Optional[int] = Field(default=None, ge=1, le=12)
    año_gasto: int

    # Relaciones
    concepto: "Concepto" = Relationship(back_populates="gastos_comunidad")
    presupuesto_anual: Optional["PresupuestoAnual"] = Relationship(back_populates="gastos_comunidad")
