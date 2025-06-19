from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, Index
from .enums import TipoMovimientoEnum

if TYPE_CHECKING:
    from .apartamento import Apartamento
    from .concepto import Concepto

class RegistroFinancieroApartamento(SQLModel, table=True):
    """
    Modelo para la tabla registro_financiero_apartamento.
    
    Representa el estado de cuenta de cada apartamento con débitos y créditos.
    Basado en la definición SQL con todas las restricciones y índices correspondientes.
    """
    __tablename__ = "registro_financiero_apartamento"
    
    # Campos principales
    id: Optional[int] = Field(
        default=None, 
        primary_key=True,
        description="ID único del registro financiero (BIGSERIAL en PostgreSQL)"
    )
    
    apartamento_id: int = Field(
        foreign_key="apartamento.id",
        description="Referencia al apartamento (ON DELETE CASCADE)"
    )
    
    fecha_registro: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha de la transacción en el sistema (TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)"
    )
    
    fecha_efectiva: date = Field(
        description="Fecha a la que corresponde el movimiento (ej. pago cuota de enero)"
    )
    
    concepto_id: int = Field(
        foreign_key="concepto.id",
        description="Referencia al concepto (ON DELETE RESTRICT)"
    )
    
    descripcion_adicional: Optional[str] = Field(
        default=None,
        description="Descripción adicional del movimiento (TEXT en PostgreSQL)"
    )
    
    tipo_movimiento: TipoMovimientoEnum = Field(
        description="Tipo de movimiento: 'DEBITO' (aumenta deuda) o 'CREDITO' (disminuye deuda/pago)"
    )
    
    monto: Decimal = Field(
        decimal_places=2, 
        max_digits=12,
        description="Monto del movimiento (DECIMAL(12, 2))"
    )
    
    mes_aplicable: Optional[int] = Field(
        default=None, 
        ge=1, 
        le=12,
        description="Mes al que aplica el movimiento (CHECK: 1-12 o NULL)"
    )
    
    año_aplicable: Optional[int] = Field(
        default=None,
        description="Año al que aplica el movimiento"
    )
    
    documento_soporte_path: Optional[str] = Field(
        default=None, 
        max_length=512,
        description="Ruta al archivo digital de soporte (VARCHAR(512))"
    )
    
    referencia_pago: Optional[str] = Field(
        default=None, 
        max_length=100,
        description="Referencia del pago: Nro de consignación, ID de transacción, etc. (VARCHAR(100))"
    )

    # Relaciones
    apartamento: "Apartamento" = Relationship(back_populates="registros_financieros")
    concepto: "Concepto" = Relationship(back_populates="registros_financieros")
    
    class Config:
        """Configuración del modelo."""
        # Habilitar validación automática
        validate_assignment = True
        # Permitir tipos arbitrarios (para Decimal)
        arbitrary_types_allowed = True
        # Schema extra para documentación (Pydantic V2)
        json_schema_extra = {
            "example": {
                "apartamento_id": 1,
                "fecha_efectiva": "2025-01-15",
                "concepto_id": 1,
                "descripcion_adicional": "Pago cuota ordinaria enero 2025",
                "tipo_movimiento": "CREDITO",
                "monto": "150000.00",
                "mes_aplicable": 1,
                "año_aplicable": 2025,
                "referencia_pago": "TRX-2025-001"
            }
        }
    
    # Definición de índices (como están en el SQL)
    __table_args__ = (
        # Índices definidos en el SQL
        Index('idx_rfa_apartamento_id', 'apartamento_id'),
        Index('idx_rfa_fecha_efectiva', 'fecha_efectiva'),
        Index('idx_rfa_concepto_id', 'concepto_id'),
        Index('idx_rfa_mes_año_aplicable', 'año_aplicable', 'mes_aplicable'),
    )
