from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Enum as SQLEnum
from .enums import TipoItemPresupuestoEnum

if TYPE_CHECKING:
    from .concepto import Concepto
    from .gasto_comunidad import GastoComunidad

class PresupuestoAnual(SQLModel, table=True):
    __tablename__ = "presupuesto_anual"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    año: int = Field(unique=True)
    descripcion: Optional[str] = None
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    items_presupuesto: List["ItemPresupuesto"] = Relationship(back_populates="presupuesto_anual")
    gastos_comunidad: List["GastoComunidad"] = Relationship(back_populates="presupuesto_anual")

class ItemPresupuesto(SQLModel, table=True):
    __tablename__ = "item_presupuesto"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    presupuesto_anual_id: int = Field(foreign_key="presupuesto_anual.id")
    concepto_id: int = Field(foreign_key="concepto.id")
    mes: int = Field(ge=1, le=12)
    monto_presupuestado: Decimal = Field(decimal_places=2, max_digits=12)
    tipo_item: TipoItemPresupuestoEnum = Field(
        sa_column=SQLEnum(TipoItemPresupuestoEnum, name="tipo_item_presupuesto_enum")
    )
    #descripcion: Optional[str] = None
    #fecha_creacion: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    presupuesto_anual: "PresupuestoAnual" = Relationship(back_populates="items_presupuesto")
    concepto: "Concepto" = Relationship(back_populates="items_presupuesto")
