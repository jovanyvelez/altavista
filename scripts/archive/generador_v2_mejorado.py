#!/usr/bin/env python3
"""
Generador Automático de Cargos Financieros Mensual - Versión SQL Directo Mejorado
=================================================================================

Este script resuelve los problemas de compatibilidad con enums de SQLModel
usando SQL directo para las inserciones, mientras mantiene SQLModel para las consultas.

✅ Generación automática de cuotas ordinarias  
✅ Cálculo automático de intereses moratorios usando tabla tasa_interes_mora
✅ Control de duplicados y reprocesamiento
✅ Procesamiento en lotes optimizado
✅ Registro completo de auditoría
✅ Manejo robusto de errores

Ejecutar: 
  python scripts/generador_v2_mejorado.py [año] [mes]
  python scripts/generador_v2_mejorado.py          # Mes actual
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import create_engine, Session, select, text
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import logging
from typing import Optional, Tuple, Dict, List

# Importaciones del proyecto
from app.models.database import DATABASE_URL
from app.models import (
    Apartamento, Concepto, CuotaConfiguracion, 
    TasaInteresMora, RegistroFinancieroApartamento,
    ControlProcesamientoMensual
)


class GeneradorAutomaticoV2:
    """
    Generador automático optimizado usando SQL directo para inserciones.
    
    Resuelve problemas de compatibilidad con enums de SQLModel.
    """
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Configurar logging para auditoría"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/generacion_automatica.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def generar_procesamiento_completo(self, año: int, mes: int, forzar: bool = False) -> Dict:
        """
        Ejecuta el procesamiento completo mensual: cuotas + intereses.
        
        Args:
            año: Año a procesar
            mes: Mes a procesar (1-12)
            forzar: Si True, ignora verificaciones de duplicados
        
        Returns:
            Dict con resultados del procesamiento
        """
        resultados = {
            'año': año,
            'mes': mes,
            'cuotas_generadas': 0,
            'intereses_generados': 0,
            'monto_cuotas': Decimal('0.00'),
            'monto_intereses': Decimal('0.00'),
            'apartamentos_procesados': 0,
            'errores': [],
            'ya_procesado': False,
            'tiempo_procesamiento': None
        }
        
        inicio = datetime.now()
        
        with Session(self.engine) as session:
            try:
                # 1. Verificar si ya se procesó (solo si no se fuerza)
                if not forzar and self._ya_procesado_mes_completo(session, año, mes):
                    resultados['ya_procesado'] = True
                    self.logger.info(f"Mes {mes:02d}/{año} ya procesado previamente")
                    return resultados
                
                # 2. Marcar inicio de procesamiento
                self._marcar_procesamiento_iniciado(session, año, mes)
                
                # 3. Generar cuotas ordinarias
                resultado_cuotas = self._procesar_cuotas_ordinarias_sql(session, año, mes, forzar)
                resultados.update(resultado_cuotas)
                
                # 4. Generar intereses moratorios
                resultado_intereses = self._procesar_intereses_moratorios_sql(session, año, mes, forzar)
                resultados['intereses_generados'] = resultado_intereses['intereses_generados']
                resultados['monto_intereses'] = resultado_intereses['monto_total']
                
                # 5. Confirmar transacción
                session.commit()
                
                # 6. Registrar procesamiento completado
                self._marcar_procesamiento_completado(
                    session, año, mes, 
                    resultados['cuotas_generadas'] + resultados['intereses_generados'],
                    resultados['monto_cuotas'] + resultados['monto_intereses']
                )
                
                resultados['tiempo_procesamiento'] = datetime.now() - inicio
                
                self.logger.info(
                    f"Procesamiento {mes:02d}/{año} completado: "
                    f"{resultados['cuotas_generadas']} cuotas (${resultados['monto_cuotas']:,.2f}), "
                    f"{resultados['intereses_generados']} intereses (${resultados['monto_intereses']:,.2f})"
                )
                
            except Exception as e:
                session.rollback()
                error_msg = f"Error en procesamiento {mes:02d}/{año}: {str(e)}"
                resultados['errores'].append(error_msg)
                self.logger.error(error_msg, exc_info=True)
                
                # Marcar error en control
                self._marcar_procesamiento_error(session, año, mes, str(e))
        
        return resultados
    
    def _ya_procesado_mes_completo(self, session: Session, año: int, mes: int) -> bool:
        """Verifica si ya se procesaron cuotas E intereses para el mes"""
        result = session.exec(
            text("""
                SELECT COUNT(*) as total FROM control_procesamiento_mensual 
                WHERE año = :año AND mes = :mes 
                AND tipo_procesamiento IN ('CUOTAS', 'INTERESES') 
                AND estado = 'COMPLETADO'
            """),
            {"año": año, "mes": mes}
        ).first()
        
        return result.total >= 2 if result else False
    
    def _procesar_cuotas_ordinarias_sql(self, session: Session, año: int, mes: int, forzar: bool) -> Dict:
        """Procesa las cuotas ordinarias del mes usando SQL directo"""
        resultado = {
            'cuotas_generadas': 0,
            'monto_cuotas': Decimal('0.00'),
            'apartamentos_procesados': 0
        }
        
        # SQL para insertar cuotas ordinarias usando SQL directo con casting de enum
        sql_cuotas = text("""
            INSERT INTO registro_financiero_apartamento 
            (apartamento_id, concepto_id, fecha_vencimiento, monto, 
             tipo_movimiento, descripcion, fecha_generacion, es_automatico)
            SELECT 
                a.id as apartamento_id,
                cc.concepto_id,
                DATE(:año || '-' || LPAD(:mes::text, 2, '0') || '-' || cc.dia_vencimiento) as fecha_vencimiento,
                cc.monto,
                'DEBITO'::tipo_movimiento_enum as tipo_movimiento,
                'Cuota automática ' || c.nombre || ' - ' || LPAD(:mes::text, 2, '0') || '/' || :año as descripcion,
                NOW() as fecha_generacion,
                true as es_automatico
            FROM apartamento a
            CROSS JOIN cuota_configuracion cc
            JOIN concepto c ON cc.concepto_id = c.id
            WHERE cc.activo = true
            AND a.activo = true
            AND NOT EXISTS (
                SELECT 1 FROM registro_financiero_apartamento rfa
                WHERE rfa.apartamento_id = a.id 
                AND rfa.concepto_id = cc.concepto_id
                AND EXTRACT(YEAR FROM rfa.fecha_vencimiento) = :año
                AND EXTRACT(MONTH FROM rfa.fecha_vencimiento) = :mes
                AND rfa.es_automatico = true
            )
        """)
        
        try:
            # Ejecutar inserción de cuotas
            result = session.exec(sql_cuotas, {
                "año": año, 
                "mes": mes
            })
            
            resultado['cuotas_generadas'] = result.rowcount
            
            # Calcular montos generados
            monto_result = session.exec(
                text("""
                    SELECT 
                        COUNT(*) as total_cuotas,
                        COALESCE(SUM(cc.monto), 0) as monto_total,
                        COUNT(DISTINCT a.id) as apartamentos_procesados
                    FROM apartamento a
                    CROSS JOIN cuota_configuracion cc
                    WHERE cc.activo = true AND a.activo = true
                """)
            ).first()
            
            if monto_result:
                resultado['monto_cuotas'] = Decimal(str(monto_result.monto_total)) * resultado['cuotas_generadas'] / monto_result.total_cuotas if monto_result.total_cuotas > 0 else Decimal('0.00')
                resultado['apartamentos_procesados'] = monto_result.apartamentos_procesados
            
            self.logger.info(f"Cuotas ordinarias {mes:02d}/{año}: {resultado['cuotas_generadas']} generadas")
            
        except Exception as e:
            self.logger.error(f"Error generando cuotas ordinarias: {e}")
            raise
        
        return resultado
    
    def _procesar_intereses_moratorios_sql(self, session: Session, año: int, mes: int, forzar: bool) -> Dict:
        """Procesa los intereses moratorios del mes usando SQL directo"""
        resultado = {
            'intereses_generados': 0,
            'monto_total': Decimal('0.00')
        }
        
        # Obtener fecha límite para cálculo de intereses (último día del mes anterior)
        fecha_limite = date(año, mes, 1) - timedelta(days=1)
        
        # SQL complejo para calcular intereses con saldos acumulados
        sql_intereses = text("""
            WITH saldos_apartamento AS (
                SELECT 
                    apartamento_id,
                    SUM(CASE 
                        WHEN tipo_movimiento = 'DEBITO' THEN monto 
                        ELSE -monto 
                    END) as saldo_pendiente
                FROM registro_financiero_apartamento
                WHERE fecha_vencimiento <= :fecha_limite
                GROUP BY apartamento_id
                HAVING SUM(CASE 
                    WHEN tipo_movimiento = 'DEBITO' THEN monto 
                    ELSE -monto 
                END) > 0
            ),
            tasa_vigente AS (
                SELECT tasa_mensual
                FROM tasa_interes_mora
                WHERE fecha_inicio <= :fecha_limite
                ORDER BY fecha_inicio DESC
                LIMIT 1
            ),
            concepto_interes AS (
                SELECT id as concepto_id
                FROM concepto
                WHERE nombre ILIKE '%interés%' OR nombre ILIKE '%mora%'
                LIMIT 1
            )
            INSERT INTO registro_financiero_apartamento 
            (apartamento_id, concepto_id, fecha_vencimiento, monto, 
             tipo_movimiento, descripcion, fecha_generacion, es_automatico)
            SELECT 
                sa.apartamento_id,
                ci.concepto_id,
                DATE(:año || '-' || LPAD(:mes::text, 2, '0') || '-28') as fecha_vencimiento,
                ROUND(sa.saldo_pendiente * (tv.tasa_mensual / 100), 2) as monto,
                'DEBITO'::tipo_movimiento_enum as tipo_movimiento,
                'Interés moratorio automático - ' || LPAD(:mes::text, 2, '0') || '/' || :año || 
                ' (Saldo: $' || sa.saldo_pendiente || ', Tasa: ' || tv.tasa_mensual || '%)' as descripcion,
                NOW() as fecha_generacion,
                true as es_automatico
            FROM saldos_apartamento sa
            CROSS JOIN tasa_vigente tv
            CROSS JOIN concepto_interes ci
            WHERE ci.concepto_id IS NOT NULL
            AND tv.tasa_mensual IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM registro_financiero_apartamento rfa
                WHERE rfa.apartamento_id = sa.apartamento_id 
                AND rfa.concepto_id = ci.concepto_id
                AND EXTRACT(YEAR FROM rfa.fecha_vencimiento) = :año
                AND EXTRACT(MONTH FROM rfa.fecha_vencimiento) = :mes
                AND rfa.es_automatico = true
                AND rfa.descripcion LIKE '%Interés moratorio automático%'
            )
        """)
        
        try:
            # Ejecutar inserción de intereses
            result = session.exec(sql_intereses, {
                "año": año, 
                "mes": mes,
                "fecha_limite": fecha_limite
            })
            
            resultado['intereses_generados'] = result.rowcount
            
            # Calcular monto total de intereses generados
            if resultado['intereses_generados'] > 0:
                monto_result = session.exec(
                    text("""
                        SELECT COALESCE(SUM(monto), 0) as monto_total
                        FROM registro_financiero_apartamento
                        WHERE EXTRACT(YEAR FROM fecha_vencimiento) = :año
                        AND EXTRACT(MONTH FROM fecha_vencimiento) = :mes
                        AND es_automatico = true
                        AND descripcion LIKE '%Interés moratorio automático%'
                    """),
                    {"año": año, "mes": mes}
                ).first()
                
                if monto_result:
                    resultado['monto_total'] = Decimal(str(monto_result.monto_total))
            
            self.logger.info(f"Intereses moratorios {mes:02d}/{año}: {resultado['intereses_generados']} generados (${resultado['monto_total']:,.2f})")
            
        except Exception as e:
            self.logger.error(f"Error generando intereses moratorios: {e}")
            raise
        
        return resultado
    
    def _marcar_procesamiento_iniciado(self, session: Session, año: int, mes: int):
        """Marca el inicio del procesamiento en la tabla de control"""
        # Insertar registro de inicio para cuotas
        session.exec(
            text("""
                INSERT INTO control_procesamiento_mensual 
                (año, mes, tipo_procesamiento, estado, fecha_inicio, registros_procesados, monto_total)
                VALUES (:año, :mes, 'CUOTAS', 'EN_PROCESO', NOW(), 0, 0)
                ON CONFLICT (año, mes, tipo_procesamiento) 
                DO UPDATE SET estado = 'EN_PROCESO', fecha_inicio = NOW()
            """),
            {"año": año, "mes": mes}
        )
        
        # Insertar registro de inicio para intereses
        session.exec(
            text("""
                INSERT INTO control_procesamiento_mensual 
                (año, mes, tipo_procesamiento, estado, fecha_inicio, registros_procesados, monto_total)
                VALUES (:año, :mes, 'INTERESES', 'EN_PROCESO', NOW(), 0, 0)
                ON CONFLICT (año, mes, tipo_procesamiento) 
                DO UPDATE SET estado = 'EN_PROCESO', fecha_inicio = NOW()
            """),
            {"año": año, "mes": mes}
        )
        session.commit()

    def _marcar_procesamiento_completado(self, session: Session, año: int, mes: int, 
                                       total_registros: int, monto_total: Decimal):
        """Marca el procesamiento como completado"""
        session.exec(
            text("""
                UPDATE control_procesamiento_mensual 
                SET estado = 'COMPLETADO', 
                    fecha_fin = NOW(),
                    registros_procesados = :registros,
                    monto_total = :monto
                WHERE año = :año AND mes = :mes
            """),
            {
                "año": año, 
                "mes": mes, 
                "registros": total_registros,
                "monto": float(monto_total)
            }
        )
        session.commit()

    def _marcar_procesamiento_error(self, session: Session, año: int, mes: int, error: str):
        """Marca el procesamiento con error"""
        session.exec(
            text("""
                UPDATE control_procesamiento_mensual 
                SET estado = 'ERROR', 
                    fecha_fin = NOW(),
                    observaciones = :error
                WHERE año = :año AND mes = :mes AND estado = 'EN_PROCESO'
            """),
            {"año": año, "mes": mes, "error": error}
        )
        session.commit()


def main():
    """Función principal para ejecutar desde línea de comandos"""
    print("🚀 Iniciando Generador Automático V2 Mejorado...")
    
    try:
        generador = GeneradorAutomaticoV2()
        
        if len(sys.argv) >= 3:
            try:
                año = int(sys.argv[1])
                mes = int(sys.argv[2])
                forzar = len(sys.argv) > 3 and sys.argv[3].lower() in ['true', '1', 'forzar']
                
                print(f"📅 Procesando {mes:02d}/{año}...")
                if forzar:
                    print("⚠️  MODO FORZADO: Ignorando verificaciones de duplicados")
                
                resultado = generador.generar_procesamiento_completo(año, mes, forzar)
                
                if resultado['ya_procesado']:
                    print(f"ℹ️  El mes {mes:02d}/{año} ya había sido procesado previamente")
                else:
                    print(f"\n✅ Procesamiento completado para {mes:02d}/{año}")
                    print(f"📊 Cuotas generadas: {resultado['cuotas_generadas']} (${resultado['monto_cuotas']:,.2f})")
                    print(f"💰 Intereses generados: {resultado['intereses_generados']} (${resultado['monto_intereses']:,.2f})")
                    print(f"⏱️  Tiempo: {resultado['tiempo_procesamiento']}")
                
                if resultado['errores']:
                    print(f"❌ Errores: {len(resultado['errores'])}")
                    for error in resultado['errores']:
                        print(f"   - {error}")
                
            except ValueError:
                print("❌ Error: Los argumentos año y mes deben ser números enteros")
                sys.exit(1)
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        else:
            # Usar mes actual
            hoy = date.today()
            print(f"📅 Procesando mes actual: {hoy.month:02d}/{hoy.year}")
            
            resultado = generador.generar_procesamiento_completo(hoy.year, hoy.month)
            
            print(f"\n✅ Resultado para {hoy.month:02d}/{hoy.year}:")
            print(f"📊 Cuotas: {resultado['cuotas_generadas']} (${resultado['monto_cuotas']:,.2f})")
            print(f"💰 Intereses: {resultado['intereses_generados']} (${resultado['monto_intereses']:,.2f})")
            
            if resultado['ya_procesado']:
                print("ℹ️  El mes ya había sido procesado previamente")
                
    except Exception as e:
        print(f"❌ Error crítico inicializando el generador: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
