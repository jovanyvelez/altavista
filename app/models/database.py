from sqlalchemy import create_engine, UniqueConstraint, Index
from sqlmodel import SQLModel, Session, create_engine as sqlmodel_create_engine
from typing import Optional

# Cambia aquí la cadena de conexión para usar PostgreSQL en vez de SQLite


# NqYMCFXBEQYYJ60u

engine = create_engine(DATABASE_URL, echo=False)

class DatabaseManager:
    def __init__(self, engine):
        self.engine = engine

    def create_tables(self):
        """Crear todas las tablas con constraints y índices"""
        # Importar todos los modelos para asegurar que estén registrados
        from .propietario import Propietario
        from .apartamento import Apartamento
        from .concepto import Concepto
        from .presupuesto_anual import PresupuestoAnual, ItemPresupuesto
        from .cuota_configuracion import CuotaConfiguracion
        from .tasa_interes_mora import TasaInteresMora
        from .registro_financiero_apartamento import RegistroFinancieroApartamento
        from .gasto_comunidad import GastoComunidad
        from .usuario import Usuario
        
        # Crear todas las tablas
        SQLModel.metadata.create_all(self.engine)
        
        # Agregar constraints únicos después de crear las tablas base
        with self.engine.connect() as conn:
            # Para ItemPresupuesto: UNIQUE (presupuesto_anual_id, concepto_id, mes, tipo_item)
            try:
                conn.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_item_presupuesto_unique 
                    ON item_presupuesto(presupuesto_anual_id, concepto_id, mes, tipo_item)
                """)
            except Exception:
                pass  # Índice ya existe
            
            # Para CuotaConfiguracion: UNIQUE (apartamento_id, año, mes)
            try:
                conn.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_cuota_config_apartamento_año_mes 
                    ON cuota_configuracion(apartamento_id, año, mes)
                """)
            except Exception:
                pass
            
            # Para TasaInteresMora: UNIQUE (año, mes)
            try:
                conn.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_tasa_interes_año_mes 
                    ON tasa_interes_mora(año, mes)
                """)
            except Exception:
                pass
            
            # Crear índices adicionales para mejor rendimiento
            indices_adicionales = [
                "CREATE INDEX IF NOT EXISTS idx_apartamento_propietario_id ON apartamento(propietario_id)",
                "CREATE INDEX IF NOT EXISTS idx_item_presupuesto_anual_id ON item_presupuesto(presupuesto_anual_id)",
                "CREATE INDEX IF NOT EXISTS idx_item_presupuesto_concepto_id ON item_presupuesto(concepto_id)",
                "CREATE INDEX IF NOT EXISTS idx_cuota_configuracion_apartamento_id ON cuota_configuracion(apartamento_id)",
                "CREATE INDEX IF NOT EXISTS idx_cuota_configuracion_año_mes ON cuota_configuracion(año, mes)",
                "CREATE INDEX IF NOT EXISTS idx_rfa_apartamento_id ON registro_financiero_apartamento(apartamento_id)",
                "CREATE INDEX IF NOT EXISTS idx_rfa_fecha_efectiva ON registro_financiero_apartamento(fecha_efectiva)",
                "CREATE INDEX IF NOT EXISTS idx_rfa_concepto_id ON registro_financiero_apartamento(concepto_id)",
                "CREATE INDEX IF NOT EXISTS idx_rfa_mes_año_aplicable ON registro_financiero_apartamento(año_aplicable, mes_aplicable)",
                "CREATE INDEX IF NOT EXISTS idx_gasto_comunidad_fecha ON gasto_comunidad(fecha_gasto)",
                "CREATE INDEX IF NOT EXISTS idx_gasto_comunidad_concepto_id ON gasto_comunidad(concepto_id)",
                "CREATE INDEX IF NOT EXISTS idx_gasto_comunidad_presupuesto_id ON gasto_comunidad(presupuesto_anual_id)",
                "CREATE INDEX IF NOT EXISTS idx_usuario_propietario_id ON usuario(propietario_id)"
            ]
            
            for indice in indices_adicionales:
                try:
                    conn.execute(indice)
                except Exception:
                    pass  # Índice ya existe
            
            conn.commit()
    
    def get_session(self) -> Session:
        return Session(self.engine)
    
    def get_engine(self):
        return self.engine

# Instancia global del manager de base de datos
db_manager = DatabaseManager(engine)
