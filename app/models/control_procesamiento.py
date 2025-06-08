"""
Tabla de Control de Procesamiento Mensual
========================================

Esta tabla permite llevar un registro de qué procesos se han ejecutado
para evitar duplicados y reprocesamiento innecesario.
"""

from sqlmodel import SQLModel, Field, Index
from datetime import datetime
from typing import Optional
from decimal import Decimal

class ControlProcesamientoMensual(SQLModel, table=True):
    """
    Control de procesamiento mensual para evitar duplicados.
    
    Registra qué tipos de procesamiento (cuotas, intereses) se han 
    ejecutado para cada mes/año específico.
    """
    __tablename__ = "control_procesamiento_mensual"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    año: int = Field(description="Año del procesamiento")
    mes: int = Field(ge=1, le=12, description="Mes del procesamiento (1-12)")
    tipo_procesamiento: str = Field(max_length=50, description="Tipo: 'CUOTAS', 'INTERESES', 'SALDOS'")
    fecha_procesamiento: datetime = Field(default_factory=datetime.utcnow, description="Cuándo se ejecutó")
    registros_procesados: int = Field(default=0, description="Cantidad de registros generados")
    monto_total_generado: Decimal = Field(decimal_places=2, max_digits=12, default=0.00, description="Monto total generado")
    estado: str = Field(default='COMPLETADO', max_length=20, description="Estado: 'PROCESANDO', 'COMPLETADO', 'ERROR'")
    observaciones: Optional[str] = Field(default=None, description="Notas adicionales")
    
    # Índices para optimizar consultas
    __table_args__ = (
        Index('idx_control_año_mes_tipo', 'año', 'mes', 'tipo_procesamiento'),
        Index('idx_control_fecha', 'fecha_procesamiento'),
        # Constraint único para evitar duplicados
        {'extend_existing': True}
    )
    
    class Config:
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "año": 2025,
                "mes": 6,
                "tipo_procesamiento": "CUOTAS",
                "registros_procesados": 25,
                "monto_total_generado": "3750000.00",
                "estado": "COMPLETADO",
                "observaciones": "Procesamiento automático mensual"
            }
        }
