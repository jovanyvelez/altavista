"""
Generador Automático de Cargos Financieros Mensual
=================================================

Este script mejora el sistema actual de generación de cargos agregando:

✅ Generación automática de cuotas ordinarias  
✅ Cálculo automático de intereses moratorios usando tabla tasa_interes_mora
✅ Control de duplicados y reprocesamiento
✅ Procesamiento en lotes optimizado
✅ Registro completo de auditoría
✅ Manejo robusto de errores

Ejecutar: 
  python scripts/generador_automatico_mensual.py [año] [mes]
  python scripts/generador_automatico_mensual.py          # Mes actual

Funcionalidades principales:
- Evita reprocesamiento usando tabla control_procesamiento_mensual
- Calcula intereses solo sobre saldos morosos reales
- Genera cuotas + intereses en una sola transacción
- Optimizado para gran volumen de apartamentos
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import create_engine, Session, select, func
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
from app.models.enums import TipoMovimientoEnum

class GeneradorAutomaticoMensual:
    """
    Generador automático optimizado para cargos mensuales.
    
    Maneja tanto cuotas ordinarias como intereses moratorios
    con control de duplicados y procesamiento eficiente.
    """
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Configurar logging para auditoría"""
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
                resultado_cuotas = self._procesar_cuotas_ordinarias(session, año, mes, forzar)
                resultados.update(resultado_cuotas)
                
                # 4. Generar intereses moratorios
                resultado_intereses = self._procesar_intereses_moratorios(session, año, mes, forzar)
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
        controles_cuotas = session.exec(
            select(ControlProcesamientoMensual).where(
                ControlProcesamientoMensual.año == año,
                ControlProcesamientoMensual.mes == mes,
                ControlProcesamientoMensual.tipo_procesamiento == 'CUOTAS',
                ControlProcesamientoMensual.estado == 'COMPLETADO'
            )
        ).first()
        
        controles_intereses = session.exec(
            select(ControlProcesamientoMensual).where(
                ControlProcesamientoMensual.año == año,
                ControlProcesamientoMensual.mes == mes,
                ControlProcesamientoMensual.tipo_procesamiento == 'INTERESES',
                ControlProcesamientoMensual.estado == 'COMPLETADO'
            )
        ).first()
        
        return controles_cuotas is not None and controles_intereses is not None
    
    def _procesar_cuotas_ordinarias(self, session: Session, año: int, mes: int, forzar: bool) -> Dict:
        """Procesa las cuotas ordinarias del mes"""
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
        
        # Obtener configuraciones del mes
        configuraciones = session.exec(
            select(CuotaConfiguracion).where(
                CuotaConfiguracion.año == año,
                CuotaConfiguracion.mes == mes
            )
        ).all()
        
        if not configuraciones:
            self.logger.warning(f"No hay configuraciones para {mes:02d}/{año}")
            return resultado
        
        fecha_efectiva = date(año, mes, 1)
        cuotas_lote = []
        
        for config in configuraciones:
            # Verificar duplicado individual
            if not forzar:
                existe = session.exec(
                    select(RegistroFinancieroApartamento).where(
                        RegistroFinancieroApartamento.apartamento_id == config.apartamento_id,
                        RegistroFinancieroApartamento.concepto_id == concepto_cuota.id,
                        RegistroFinancieroApartamento.tipo_movimiento == "DEBITO",
                        RegistroFinancieroApartamento.mes_aplicable == mes,
                        RegistroFinancieroApartamento.año_aplicable == año
                    )
                ).first()
                
                if existe:
                    continue
            
            # Crear cargo de cuota
            nuevo_cargo = RegistroFinancieroApartamento(
                apartamento_id=config.apartamento_id,
                concepto_id=concepto_cuota.id,
                tipo_movimiento="DEBITO",
                monto=config.monto_cuota_ordinaria_mensual,
                fecha_efectiva=fecha_efectiva,
                mes_aplicable=mes,
                año_aplicable=año,
                referencia_pago=f"CUOTA-AUTO-{mes:02d}/{año}",
                descripcion_adicional=f"Cuota ordinaria administración {mes:02d}/{año}"
            )
            
            cuotas_lote.append(nuevo_cargo)
            resultado['monto_cuotas'] += config.monto_cuota_ordinaria_mensual
        
        # Insertar en lote para mejor performance
        if cuotas_lote:
            session.add_all(cuotas_lote)
            resultado['cuotas_generadas'] = len(cuotas_lote)
            resultado['apartamentos_procesados'] = len(cuotas_lote)
        
        return resultado
    
    def _procesar_intereses_moratorios(self, session: Session, año: int, mes: int, forzar: bool) -> Dict:
        """Procesa intereses moratorios basados en saldos morosos"""
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
        
        # Obtener todos los apartamentos
        apartamentos = session.exec(select(Apartamento)).all()
        intereses_lote = []
        fecha_efectiva = date(año, mes, 15)  # Día 15 para intereses
        
        for apartamento in apartamentos:
            # Verificar duplicado
            if not forzar:
                existe = session.exec(
                    select(RegistroFinancieroApartamento).where(
                        RegistroFinancieroApartamento.apartamento_id == apartamento.id,
                        RegistroFinancieroApartamento.concepto_id == concepto_interes.id,
                        RegistroFinancieroApartamento.tipo_movimiento == "DEBITO",
                        RegistroFinancieroApartamento.mes_aplicable == mes,
                        RegistroFinancieroApartamento.año_aplicable == año
                    )
                ).first()
                
                if existe:
                    continue
            
            # Calcular saldo moroso hasta el mes anterior
            saldo_moroso = self._calcular_saldo_moroso(session, apartamento.id, año, mes)
            
            if saldo_moroso > Decimal('0.01'):  # Solo si hay deuda significativa
                # Calcular interés
                tasa_mensual = tasa_interes.tasa_interes_mensual / 100
                monto_interes = saldo_moroso * Decimal(str(tasa_mensual))
                monto_interes = monto_interes.quantize(Decimal('0.01'))
                
                if monto_interes > Decimal('0.01'):
                    nuevo_interes = RegistroFinancieroApartamento(
                        apartamento_id=apartamento.id,
                        concepto_id=concepto_interes.id,
                        tipo_movimiento="DEBITO",
                        monto=monto_interes,
                        fecha_efectiva=fecha_efectiva,
                        mes_aplicable=mes,
                        año_aplicable=año,
                        referencia_pago=f"INTERES-AUTO-{mes:02d}/{año}",
                        descripcion_adicional=(
                            f"Interés mora {tasa_mensual*100:.2f}% sobre saldo "
                            f"${saldo_moroso:,.2f} - {mes:02d}/{año}"
                        )
                    )
                    
                    intereses_lote.append(nuevo_interes)
                    resultado['monto_total'] += monto_interes
        
        # Insertar en lote
        if intereses_lote:
            session.add_all(intereses_lote)
            resultado['intereses_generados'] = len(intereses_lote)
        
        return resultado
    
    def _calcular_saldo_moroso(self, session: Session, apartamento_id: int, año: int, mes: int) -> Decimal:
        """
        Calcula el saldo moroso de un apartamento hasta el mes anterior.
        
        Solo considera como moroso el saldo que tiene más de 30 días sin pagar.
        """
        fecha_limite = date(año, mes, 1) - timedelta(days=1)
        fecha_corte_mora = fecha_limite - timedelta(days=30)  # 30 días para considerar mora
        
        # Obtener balance hasta la fecha límite
        registros = session.exec(
            select(RegistroFinancieroApartamento).where(
                RegistroFinancieroApartamento.apartamento_id == apartamento_id,
                RegistroFinancieroApartamento.fecha_efectiva <= fecha_limite
            )
        ).all()
        
        saldo_total = Decimal('0.00')
        for registro in registros:
            if registro.tipo_movimiento == "DEBITO":
                saldo_total += registro.monto
            else:  # CREDITO
                saldo_total -= registro.monto
        
        # Solo aplicar interés si hay deuda real y antigua
        if saldo_total > Decimal('0.00'):
            # Verificar que hay cargos anteriores a la fecha de corte de mora
            cargos_morosos = session.exec(
                select(RegistroFinancieroApartamento).where(
                    RegistroFinancieroApartamento.apartamento_id == apartamento_id,
                    RegistroFinancieroApartamento.tipo_movimiento == "DEBITO",
                    RegistroFinancieroApartamento.fecha_efectiva <= fecha_corte_mora
                )
            ).first()
            
            if cargos_morosos:
                return max(saldo_total, Decimal('0.00'))
        
        return Decimal('0.00')
    
    def _marcar_procesamiento_iniciado(self, session: Session, año: int, mes: int):
        """Marca el inicio del procesamiento"""
        control = ControlProcesamientoMensual(
            año=año,
            mes=mes,
            tipo_procesamiento='PROCESAMIENTO_COMPLETO',
            estado='PROCESANDO',
            observaciones='Procesamiento iniciado'
        )
        session.add(control)
        session.commit()
    
    def _marcar_procesamiento_completado(self, session: Session, año: int, mes: int, 
                                       registros: int, monto: Decimal):
        """Marca el procesamiento como completado"""
        # Actualizar registro de procesamiento completo
        stmt = (
            select(ControlProcesamientoMensual)
            .where(
                ControlProcesamientoMensual.año == año,
                ControlProcesamientoMensual.mes == mes,
                ControlProcesamientoMensual.tipo_procesamiento == 'PROCESAMIENTO_COMPLETO'
            )
        )
        control_existente = session.exec(stmt).first()
        
        if control_existente:
            control_existente.estado = 'COMPLETADO'
            control_existente.registros_procesados = registros
            control_existente.monto_total_generado = monto
            control_existente.observaciones = 'Procesamiento completado exitosamente'
        
        # Crear registros específicos para cuotas e intereses
        control_cuotas = ControlProcesamientoMensual(
            año=año, mes=mes, tipo_procesamiento='CUOTAS',
            estado='COMPLETADO', observaciones='Incluido en procesamiento completo'
        )
        control_intereses = ControlProcesamientoMensual(
            año=año, mes=mes, tipo_procesamiento='INTERESES', 
            estado='COMPLETADO', observaciones='Incluido en procesamiento completo'
        )
        
        session.add_all([control_cuotas, control_intereses])
        session.commit()
    
    def _marcar_procesamiento_error(self, session: Session, año: int, mes: int, error: str):
        """Marca error en procesamiento"""
        from sqlmodel import text
        session.exec(
            text(f"""UPDATE control_procesamiento_mensual 
               SET estado = 'ERROR', 
                   observaciones = 'Error: {error[:200]}'
               WHERE año = {año} AND mes = {mes} AND tipo_procesamiento = 'PROCESAMIENTO_COMPLETO'""")
        )
        session.commit()
    
    def generar_rango_meses(self, año_inicio: int, mes_inicio: int, 
                           año_fin: int, mes_fin: int, forzar: bool = False) -> Dict:
        """Genera procesamiento para un rango de meses"""
        resultados_totales = {
            'meses_procesados': 0,
            'meses_saltados': 0,
            'cuotas_totales': 0,
            'intereses_totales': 0,
            'monto_total': Decimal('0.00'),
            'errores': [],
            'detalle_meses': []
        }
        
        fecha_actual = date(año_inicio, mes_inicio, 1)
        fecha_fin = date(año_fin, mes_fin, 1)
        
        while fecha_actual <= fecha_fin:
            resultado_mes = self.generar_procesamiento_completo(
                fecha_actual.year, fecha_actual.month, forzar
            )
            
            resultados_totales['detalle_meses'].append(resultado_mes)
            
            if resultado_mes['ya_procesado']:
                resultados_totales['meses_saltados'] += 1
            else:
                resultados_totales['meses_procesados'] += 1
                resultados_totales['cuotas_totales'] += resultado_mes['cuotas_generadas']
                resultados_totales['intereses_totales'] += resultado_mes['intereses_generados']
                resultados_totales['monto_total'] += (
                    resultado_mes['monto_cuotas'] + resultado_mes['monto_intereses']
                )
            
            resultados_totales['errores'].extend(resultado_mes['errores'])
            
            # Avanzar al siguiente mes
            fecha_actual += relativedelta(months=1)
        
        return resultados_totales


def main():
    """Función principal para ejecutar desde línea de comandos"""
    # Crear directorio de logs si no existe
    os.makedirs('logs', exist_ok=True)
    
    generador = GeneradorAutomaticoMensual()
    
    if len(sys.argv) >= 3:
        try:
            año = int(sys.argv[1])
            mes = int(sys.argv[2])
            forzar = len(sys.argv) > 3 and sys.argv[3].lower() in ['true', '1', 'forzar']
            
            print(f"🚀 Iniciando procesamiento para {mes:02d}/{año}...")
            if forzar:
                print("⚠️  MODO FORZADO: Ignorando verificaciones de duplicados")
            
            resultado = generador.generar_procesamiento_completo(año, mes, forzar)
            
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
        print(f"🚀 Procesando mes actual: {hoy.month:02d}/{hoy.year}")
        
        resultado = generador.generar_procesamiento_completo(hoy.year, hoy.month)
        
        print(f"\n✅ Resultado para {hoy.month:02d}/{hoy.year}:")
        print(f"📊 Cuotas: {resultado['cuotas_generadas']} (${resultado['monto_cuotas']:,.2f})")
        print(f"💰 Intereses: {resultado['intereses_generados']} (${resultado['monto_intereses']:,.2f})")
        
        if resultado['ya_procesado']:
            print("ℹ️  El mes ya había sido procesado previamente")


if __name__ == "__main__":
    main()
