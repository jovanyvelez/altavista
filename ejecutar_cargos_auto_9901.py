#!/usr/bin/env python3
"""
Script automático para generar cargos del apartamento 9901
(versión sin confirmación para testing)
"""

from sqlmodel import create_engine, Session, select
from datetime import date, datetime
from decimal import Decimal
import os
import sys
from dateutil.relativedelta import relativedelta

# Añadir el directorio raíz del proyecto al sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.models.database import DATABASE_URL
from app.models.apartamento import Apartamento
from app.models.concepto import Concepto
from app.models.cuota_configuracion import CuotaConfiguracion
from app.models.tasa_interes_mora import TasaInteresMora
from app.models.registro_financiero_apartamento import RegistroFinancieroApartamento
from app.models.enums import TipoMovimientoEnum

engine = create_engine(DATABASE_URL)

def obtener_saldo_acumulado(session: Session, apartamento_id: int, fecha_calculo: date) -> Decimal:
    """
    Calcula el saldo total acumulado hasta la fecha (todos los débitos menos créditos).
    El interés moratorio se calcula sobre TODO el saldo pendiente, no solo sobre cargos vencidos.
    """
    # Obtener todos los DEBITOS hasta el día anterior a la fecha de cálculo
    fecha_limite = fecha_calculo - relativedelta(days=1)
    
    statement_debitos = select(RegistroFinancieroApartamento).where(
        RegistroFinancieroApartamento.apartamento_id == apartamento_id,
        RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.DEBITO,
        RegistroFinancieroApartamento.fecha_efectiva <= fecha_limite
    )
    
    debitos = session.exec(statement_debitos).all()
    total_debitos = sum(registro.monto for registro in debitos)
    
    # Obtener todos los CREDITOS hasta el día anterior a la fecha de cálculo
    statement_creditos = select(RegistroFinancieroApartamento).where(
        RegistroFinancieroApartamento.apartamento_id == apartamento_id,
        RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.CREDITO,
        RegistroFinancieroApartamento.fecha_efectiva <= fecha_limite
    )
    
    creditos = session.exec(statement_creditos).all()
    total_creditos = sum(registro.monto for registro in creditos)
    
    saldo_total = total_debitos - total_creditos
    return max(saldo_total, Decimal("0.00"))

def generar_cargos():
    """Genera los cargos automáticamente"""
    
    with Session(engine) as session:
        print("🔍 Obteniendo referencias...")
        
        # Obtener apartamento 9901
        apartamento = session.exec(
            select(Apartamento).where(Apartamento.identificador == "9901")
        ).first()
        
        # Obtener conceptos
        concepto_cuota = session.exec(
            select(Concepto).where(Concepto.nombre == "Cuota Ordinaria Administración")
        ).first()
        
        concepto_interes = session.exec(
            select(Concepto).where(Concepto.nombre == "Intereses por Mora")
        ).first()
        
        print(f"✅ Apartamento ID: {apartamento.id}")
        print(f"✅ Concepto Cuota ID: {concepto_cuota.id}")
        print(f"✅ Concepto Interés ID: {concepto_interes.id}")
        print()
        
        # Contadores
        cargos_cuota_creados = 0
        cargos_interes_creados = 0
        cargos_cuota_omitidos = 0
        cargos_interes_omitidos = 0
        
        # Iterar desde julio 2022 hasta mayo 2025
        current_anio = 2022
        current_mes = 7
        
        while (current_anio < 2025) or (current_anio == 2025 and current_mes <= 5):
            
            print(f"📅 Procesando {current_mes:02d}/{current_anio}")
            
            # --- CARGO DE CUOTA ORDINARIA ---
            fecha_cargo_cuota = date(current_anio, current_mes, 1)
            
            # Verificar si ya existe
            cargo_cuota_existente = session.exec(
                select(RegistroFinancieroApartamento).where(
                    RegistroFinancieroApartamento.apartamento_id == apartamento.id,
                    RegistroFinancieroApartamento.concepto_id == concepto_cuota.id,
                    RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.DEBITO,
                    RegistroFinancieroApartamento.año_aplicable == current_anio,
                    RegistroFinancieroApartamento.mes_aplicable == current_mes
                )
            ).first()
            
            if not cargo_cuota_existente:
                # Buscar configuración de cuota
                cuota_config = session.exec(
                    select(CuotaConfiguracion).where(
                        CuotaConfiguracion.apartamento_id == apartamento.id,
                        CuotaConfiguracion.año == current_anio,
                        CuotaConfiguracion.mes == current_mes
                    )
                ).first()
                
                if cuota_config:
                    nuevo_cargo_cuota = RegistroFinancieroApartamento(
                        apartamento_id=apartamento.id,
                        fecha_registro=datetime.now(),
                        fecha_efectiva=fecha_cargo_cuota,
                        concepto_id=concepto_cuota.id,
                        descripcion_adicional=f"Cuota ordinaria administración {current_mes:02d}/{current_anio}",
                        tipo_movimiento=TipoMovimientoEnum.DEBITO,
                        monto=cuota_config.monto_cuota_ordinaria_mensual,
                        mes_aplicable=current_mes,
                        año_aplicable=current_anio
                    )
                    
                    session.add(nuevo_cargo_cuota)
                    session.flush()  # Para que esté disponible en siguientes consultas
                    cargos_cuota_creados += 1
                    print(f"   ✅ Cargo cuota: ${cuota_config.monto_cuota_ordinaria_mensual}")
                else:
                    print(f"   ⚠️  No hay configuración de cuota para {current_mes:02d}/{current_anio}")
            else:
                cargos_cuota_omitidos += 1
                print(f"   ⏭️  Cargo cuota ya existe")
            
            # --- CARGO DE INTERÉS MORATORIO ---
            if not (current_anio == 2022 and current_mes == 7):  # No calcular intereses el primer mes
                fecha_cargo_interes = date(current_anio, current_mes, 15)
                
                # Verificar si ya existe
                cargo_interes_existente = session.exec(
                    select(RegistroFinancieroApartamento).where(
                        RegistroFinancieroApartamento.apartamento_id == apartamento.id,
                        RegistroFinancieroApartamento.concepto_id == concepto_interes.id,
                        RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.DEBITO,
                        RegistroFinancieroApartamento.año_aplicable == current_anio,
                        RegistroFinancieroApartamento.mes_aplicable == current_mes
                    )
                ).first()
                
                if not cargo_interes_existente:
                    # Obtener tasa de interés
                    tasa_interes = session.exec(
                        select(TasaInteresMora).where(
                            TasaInteresMora.año == current_anio,
                            TasaInteresMora.mes == current_mes
                        )
                    ).first()
                    
                    if tasa_interes:
                        # Calcular saldo acumulado total al inicio del mes
                        fecha_calculo_saldo = date(current_anio, current_mes, 1)
                        saldo_acumulado = obtener_saldo_acumulado(session, apartamento.id, fecha_calculo_saldo)
                        
                        if saldo_acumulado > Decimal("0.00"):
                            interes_calculado = saldo_acumulado * tasa_interes.tasa_interes_mensual
                            interes_calculado = interes_calculado.quantize(Decimal("0.01"))
                            
                            if interes_calculado > Decimal("0.00"):
                                nuevo_cargo_interes = RegistroFinancieroApartamento(
                                    apartamento_id=apartamento.id,
                                    fecha_registro=datetime.now(),
                                    fecha_efectiva=fecha_cargo_interes,
                                    concepto_id=concepto_interes.id,
                                    descripcion_adicional=f"Interés moratorio {current_mes:02d}/{current_anio} - Tasa: {tasa_interes.tasa_interes_mensual*100:.2f}% sobre ${saldo_acumulado}",
                                    tipo_movimiento=TipoMovimientoEnum.DEBITO,
                                    monto=interes_calculado,
                                    mes_aplicable=current_mes,
                                    año_aplicable=current_anio
                                )
                                
                                session.add(nuevo_cargo_interes)
                                session.flush()
                                cargos_interes_creados += 1
                                print(f"   💰 Interés: ${interes_calculado} ({tasa_interes.tasa_interes_mensual*100:.2f}% sobre ${saldo_acumulado})")
                            else:
                                print(f"   💸 Interés calculado: $0.00")
                        else:
                            print(f"   📊 Sin saldo pendiente")
                    else:
                        print(f"   ⚠️  No hay tasa de interés para {current_mes:02d}/{current_anio}")
                else:
                    cargos_interes_omitidos += 1
                    print(f"   ⏭️  Cargo interés ya existe")
            
            # Avanzar al siguiente mes
            current_mes += 1
            if current_mes > 12:
                current_mes = 1
                current_anio += 1
        
        # Confirmar cambios
        session.commit()
        
        # Mostrar resumen
        print("\n" + "=" * 60)
        print("📊 RESUMEN FINAL")
        print("=" * 60)
        print(f"💰 Cargos de cuota creados: {cargos_cuota_creados}")
        print(f"💰 Cargos de cuota omitidos: {cargos_cuota_omitidos}")
        print(f"💸 Cargos de interés creados: {cargos_interes_creados}")
        print(f"💸 Cargos de interés omitidos: {cargos_interes_omitidos}")
        print("=" * 60)

if __name__ == "__main__":
    print("🚀 GENERADOR AUTOMÁTICO DE CARGOS - APARTAMENTO 9901")
    print("📅 Período: 07/2022 - 05/2025")
    print()
    
    try:
        generar_cargos()
        print("🎉 ¡Proceso completado exitosamente!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
