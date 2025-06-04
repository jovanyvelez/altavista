from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from .enums import TipoMovimientoEnum

if TYPE_CHECKING:
    from .apartamento import Apartamento
    from .concepto import Concepto

class RegistroFinancieroApartamento(SQLModel, table=True):
    __tablename__ = "registro_financiero_apartamento"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    apartamento_id: int = Field(foreign_key="apartamento.id")
    fecha_registro: datetime = Field(default_factory=datetime.utcnow)
    fecha_efectiva: date
    concepto_id: int = Field(foreign_key="concepto.id")
    descripcion_adicional: Optional[str] = None
    tipo_movimiento: TipoMovimientoEnum
    monto: Decimal = Field(decimal_places=2, max_digits=12)
    mes_aplicable: Optional[int] = Field(default=None, ge=1, le=12)
    año_aplicable: Optional[int] = None
    documento_soporte_path: Optional[str] = Field(default=None, max_length=512)
    referencia_pago: Optional[str] = Field(default=None, max_length=100)

    # Relaciones
    apartamento: "Apartamento" = Relationship(back_populates="registros_financieros")
    concepto: "Concepto" = Relationship(back_populates="registros_financieros")
