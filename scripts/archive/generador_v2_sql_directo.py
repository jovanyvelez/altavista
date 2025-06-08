#!/usr/bin/env python3
"""
Generador Automático de Cargos Financieros Mensual - Versión SQL Directo
=========================================================================

Este script resuelve los problemas de compatibilidad con enums de SQLModel
usando SQL directo para las inserciones, mientras mantiene SQLModel para las consultas.

✅ Generación automática de cuotas ordinarias  
✅ Cálculo automático de intereses moratorios usando tabla tasa_interes_mora
✅ Control de duplicados y reprocesamiento
✅ Procesamiento en lotes optimizado
✅ Registro completo de auditoría
✅ Manejo robusto de errores

Ejecutar: 
  python scripts/generador_v2_sql_directo.py [año] [mes]
  python scripts/generador_v2_sql_directo.py          # Mes actual
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
        sql = text("""
            SELECT COUNT(*) as total FROM control_procesamiento_mensual 
            WHERE año = :año AND mes = :mes 
            AND tipo_procesamiento IN ('CUOTAS', 'INTERESES') 
            AND estado = 'COMPLETADO'
        """).bindparams(año=año, mes=mes)
        
        result = session.exec(sql).first()
        
        return result.total >= 2 if result else False
    
    def _procesar_cuotas_ordinarias_sql(self, session: Session, año: int, mes: int, forzar: bool) -> Dict:
        """Procesa las cuotas ordinarias del mes usando SQL directo"""
        resultado = {
            'cuotas_generadas': 0,
            'monto_cuotas': Decimal('0.00'),
            'apartamentos_procesados': 0
        }
        
        # Obtener concepto de cuota ordinaria
        concepto_cuota = session.exec(
            select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%administr%"))
        ).first()
        
        if not concepto_cuota:
            raise Exception("No se encontró concepto de cuota ordinaria")
        
        fecha_efectiva = date(año, mes, 1)
        
        # SQL para insertar cuotas - evita duplicados y usa bulk insert
        sql_insert_cuotas = text("""
            INSERT INTO registro_financiero_apartamento (
                apartamento_id, fecha_registro, fecha_efectiva, concepto_id, 
                descripcion_adicional, tipo_movimiento, monto, mes_aplicable, 
                año_aplicable, referencia_pago
            )
            SELECT 
                cc.apartamento_id,
                CURRENT_TIMESTAMP,
                :fecha_efectiva,
                :concepto_id,
                :descripcion_adicional,
                'DEBITO'::tipo_movimiento_enum,
                cc.monto_cuota_ordinaria_mensual,
                :mes,
                :año,
                :referencia_pago
            FROM cuota_configuracion cc
            WHERE cc.año = :año AND cc.mes = :mes
            AND NOT EXISTS (
                SELECT 1 FROM registro_financiero_apartamento rfa
                WHERE rfa.apartamento_id = cc.apartamento_id
                AND rfa.concepto_id = :concepto_id
                AND rfa.tipo_movimiento = 'DEBITO'
                AND rfa.mes_aplicable = :mes
                AND rfa.año_aplicable = :año
                AND NOT :forzar
            )
            RETURNING apartamento_id, monto
        """)
        
        params = {
            'fecha_efectiva': fecha_efectiva,
            'concepto_id': concepto_cuota.id,
            'descripcion_adicional': f'Cuota ordinaria administración {mes:02d}/{año}',
            'mes': mes,
            'año': año,
            'referencia_pago': f'CUOTA-AUTO-{mes:02d}/{año}',
            'forzar': forzar
        }
        
        # Ejecutar inserción
        result = session.exec(sql_insert_cuotas, params)
        registros_insertados = result.fetchall()
        
        if registros_insertados:
            resultado['cuotas_generadas'] = len(registros_insertados)
            resultado['monto_cuotas'] = sum(Decimal(str(r.monto)) for r in registros_insertados)
            resultado['apartamentos_procesados'] = len(registros_insertados)
            
            self.logger.info(f"Cuotas generadas: {resultado['cuotas_generadas']} por ${resultado['monto_cuotas']:,.2f}")
        
        return resultado
    
    def _procesar_intereses_moratorios_sql(self, session: Session, año: int, mes: int, forzar: bool) -> Dict:
        """Procesa intereses moratorios usando SQL directo"""
        resultado = {
            'intereses_generados': 0,
            'monto_total': Decimal('0.00')
        }
        
        # Obtener concepto de interés moratorio
        concepto_interes = session.exec(
            select(Concepto).where(Concepto.nombre.ilike("%interes%mora%"))
        ).first()
        
        if not concepto_interes:
            self.logger.warning("No se encontró concepto de interés moratorio")
            return resultado
        
        # Obtener tasa de interés para el período
        tasa_interes = session.exec(
            select(TasaInteresMora).where(
                TasaInteresMora.año == año,
                TasaInteresMora.mes == mes
            )
        ).first()
        
        if not tasa_interes:
            self.logger.warning(f"No hay tasa de interés configurada para {mes:02d}/{año}")
            return resultado
        
        fecha_efectiva = date(año, mes, 15)  # Día 15 para intereses
        fecha_limite = date(año, mes, 1) - timedelta(days=1)
        fecha_corte_mora = fecha_limite - timedelta(days=30)  # 30 días para considerar mora
        tasa_mensual = tasa_interes.tasa_interes_mensual / 100
        
        # SQL complejo para calcular saldos morosos e insertar intereses
        sql_insert_intereses = text("""
            WITH saldos_apartamentos AS (
                SELECT 
                    a.id as apartamento_id,
                    COALESCE(SUM(
                        CASE 
                            WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto
                            ELSE -rfa.monto
                        END
                    ), 0) as saldo_total
                FROM apartamento a
                LEFT JOIN registro_financiero_apartamento rfa ON a.id = rfa.apartamento_id
                    AND rfa.fecha_efectiva <= :fecha_limite
                GROUP BY a.id
            ),
            apartamentos_con_mora AS (
                SELECT 
                    sa.apartamento_id,
                    sa.saldo_total,
                    (sa.saldo_total * :tasa_mensual)::DECIMAL(12,2) as interes_calculado
                FROM saldos_apartamentos sa
                WHERE sa.saldo_total > 0.01
                AND EXISTS (
                    SELECT 1 FROM registro_financiero_apartamento rfa_mora
                    WHERE rfa_mora.apartamento_id = sa.apartamento_id
                    AND rfa_mora.tipo_movimiento = 'DEBITO'
                    AND rfa_mora.fecha_efectiva <= :fecha_corte_mora
                )
                AND NOT EXISTS (
                    SELECT 1 FROM registro_financiero_apartamento rfa_dup
                    WHERE rfa_dup.apartamento_id = sa.apartamento_id
                    AND rfa_dup.concepto_id = :concepto_id
                    AND rfa_dup.tipo_movimiento = 'DEBITO'
                    AND rfa_dup.mes_aplicable = :mes
                    AND rfa_dup.año_aplicable = :año
                    AND NOT :forzar
                )
                AND (sa.saldo_total * :tasa_mensual) > 0.01
            )
            INSERT INTO registro_financiero_apartamento (
                apartamento_id, fecha_registro, fecha_efectiva, concepto_id,
                descripcion_adicional, tipo_movimiento, monto, mes_aplicable,
                año_aplicable, referencia_pago
            )
            SELECT 
                acm.apartamento_id,
                CURRENT_TIMESTAMP,
                :fecha_efectiva,
                :concepto_id,
                'Interés mora ' || :tasa_porcentual || '% sobre saldo $' || 
                TO_CHAR(acm.saldo_total, 'FM999,999,999.00') || ' - ' || :mes_año,
                'DEBITO'::tipo_movimiento_enum,
                acm.interes_calculado,
                :mes,
                :año,
                :referencia_pago
            FROM apartamentos_con_mora acm
            RETURNING apartamento_id, monto
        """)
        
        params = {
            'fecha_limite': fecha_limite,
            'fecha_corte_mora': fecha_corte_mora,
            'tasa_mensual': float(tasa_mensual),
            'concepto_id': concepto_interes.id,
            'mes': mes,
            'año': año,
            'forzar': forzar,
            'fecha_efectiva': fecha_efectiva,
            'tasa_porcentual': f"{tasa_mensual*100:.2f}",
            'mes_año': f"{mes:02d}/{año}",
            'referencia_pago': f'INTERES-AUTO-{mes:02d}/{año}'
        }
        
        # Ejecutar inserción
        result = session.exec(sql_insert_intereses, params)
        registros_insertados = result.fetchall()
        
        if registros_insertados:
            resultado['intereses_generados'] = len(registros_insertados)
            resultado['monto_total'] = sum(Decimal(str(r.monto)) for r in registros_insertados)
            
            self.logger.info(f"Intereses generados: {resultado['intereses_generados']} por ${resultado['monto_total']:,.2f}")
        
        return resultado
    
    def _marcar_procesamiento_iniciado(self, session: Session, año: int, mes: int):
        """Marca el inicio del procesamiento"""
        sql = text("""
            INSERT INTO control_procesamiento_mensual 
            (año, mes, tipo_procesamiento, estado, observaciones)
            VALUES (:año, :mes, 'PROCESAMIENTO_COMPLETO', 'PROCESANDO', 'Procesamiento iniciado')
            ON CONFLICT (año, mes, tipo_procesamiento) 
            DO UPDATE SET estado = 'PROCESANDO', fecha_procesamiento = CURRENT_TIMESTAMP
        """)
        session.exec(sql, {"año": año, "mes": mes})
        session.commit()
    
    def _marcar_procesamiento_completado(self, session: Session, año: int, mes: int, 
                                       registros: int, monto: Decimal):
        """Marca el procesamiento como completado"""
        # Actualizar registro principal
        sql_principal = text("""
            UPDATE control_procesamiento_mensual 
            SET estado = 'COMPLETADO', 
                registros_procesados = :registros, 
                monto_total_generado = :monto,
                observaciones = 'Procesamiento completado exitosamente'
            WHERE año = :año AND mes = :mes AND tipo_procesamiento = 'PROCESAMIENTO_COMPLETO'
        """)
        session.exec(sql_principal, {"año": año, "mes": mes, "registros": registros, "monto": float(monto)})
        
        # Crear registros específicos
        sql_especificos = text("""
            INSERT INTO control_procesamiento_mensual 
            (año, mes, tipo_procesamiento, estado, observaciones)
            VALUES 
                (:año, :mes, 'CUOTAS', 'COMPLETADO', 'Incluido en procesamiento completo'),
                (:año, :mes, 'INTERESES', 'COMPLETADO', 'Incluido en procesamiento completo')
            ON CONFLICT (año, mes, tipo_procesamiento) DO NOTHING
        """)
        session.exec(sql_especificos, {"año": año, "mes": mes})
        session.commit()
    
    def _marcar_procesamiento_error(self, session: Session, año: int, mes: int, error: str):
        """Marca error en procesamiento"""
        sql = text("""
            UPDATE control_procesamiento_mensual 
            SET estado = 'ERROR', 
                observaciones = :observaciones
            WHERE año = :año AND mes = :mes AND tipo_procesamiento = 'PROCESAMIENTO_COMPLETO'
        """)
        session.exec(sql, {
            "año": año, 
            "mes": mes, 
            "observaciones": f"Error: {error[:200]}"
        })
        session.commit()


def main():
    """Función principal para ejecutar desde línea de comandos"""
    generador = GeneradorAutomaticoV2()
    
    if len(sys.argv) >= 3:
        try:
            año = int(sys.argv[1])
            mes = int(sys.argv[2])
            forzar = len(sys.argv) > 3 and sys.argv[3].lower() in ['true', '1', 'forzar']
            
            print(f"🚀 Iniciando procesamiento V2 para {mes:02d}/{año}...")
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
            sys.exit(1)
    else:
        # Usar mes actual
        hoy = date.today()
        print(f"🚀 Procesando mes actual V2: {hoy.month:02d}/{hoy.year}")
        
        resultado = generador.generar_procesamiento_completo(hoy.year, hoy.month)
        
        print(f"\n✅ Resultado para {hoy.month:02d}/{hoy.year}:")
        print(f"📊 Cuotas: {resultado['cuotas_generadas']} (${resultado['monto_cuotas']:,.2f})")
        print(f"💰 Intereses: {resultado['intereses_generados']} (${resultado['monto_intereses']:,.2f})")
        
        if resultado['ya_procesado']:
            print("ℹ️  El mes ya había sido procesado previamente")


if __name__ == "__main__":
    main()
