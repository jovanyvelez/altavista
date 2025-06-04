from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .presupuesto_anual import ItemPresupuesto
    from .registro_financiero_apartamento import RegistroFinancieroApartamento
    from .gasto_comunidad import GastoComunidad

class Concepto(SQLModel, table=True):
    __tablename__ = "concepto"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150, unique=True)
    es_ingreso_tipico: bool = Field(default=False)
    es_recurrente_presupuesto: bool = Field(default=True)
    descripcion: Optional[str] = None

    # Relaciones
    items_presupuesto: List["ItemPresupuesto"] = Relationship(back_populates="concepto")
    registros_financieros: List["RegistroFinancieroApartamento"] = Relationship(back_populates="concepto")
    gastos_comunidad: List["GastoComunidad"] = Relationship(back_populates="concepto")
