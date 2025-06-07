#!/usr/bin/env python3
"""
Script para limpiar registros del apartamento 9901 y regenerarlos con lógica corregida
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

def limpiar_y_regenerar():
    """Limpia todos los registros del apartamento 9901 y los regenera con lógica corregida"""
    
    with Session(engine) as session:
        print("🔍 Obteniendo referencias...")
        
        # Obtener apartamento 9901
        apartamento = session.exec(
            select(Apartamento).where(Apartamento.identificador == "9901")
        ).first()
        
        if not apartamento:
            print("❌ Apartamento 9901 no encontrado")
            return
        
        print(f"✅ Apartamento 9901 encontrado (ID: {apartamento.id})")
        
        # 1. LIMPIAR registros existentes
        print("\n🧹 LIMPIANDO registros existentes del apartamento 9901...")
        
        registros_existentes = session.exec(
            select(RegistroFinancieroApartamento).where(
                RegistroFinancieroApartamento.apartamento_id == apartamento.id
            )
        ).all()
        
        print(f"   📊 Registros encontrados: {len(registros_existentes)}")
        
        for registro in registros_existentes:
            session.delete(registro)
        
        session.commit()
        print("   ✅ Registros eliminados exitosamente")
        
        # 2. REGENERAR con lógica corregida
        print("\n🔄 REGENERANDO registros con lógica corregida...")
        
        # Obtener conceptos
        concepto_cuota = session.exec(
            select(Concepto).where(Concepto.nombre == "Cuota Ordinaria Administración")
        ).first()
        
        concepto_interes = session.exec(
            select(Concepto).where(Concepto.nombre == "Intereses por Mora")
        ).first()
        
        print(f"✅ Concepto Cuota ID: {concepto_cuota.id}")
        print(f"✅ Concepto Interés ID: {concepto_interes.id}")
        print()
        
        # Contadores
        cargos_cuota_creados = 0
        cargos_interes_creados = 0
        
        # Iterar desde julio 2022 hasta mayo 2025
        current_anio = 2022
        current_mes = 7
        
        while (current_anio < 2025) or (current_anio == 2025 and current_mes <= 5):
            
            print(f"📅 Procesando {current_mes:02d}/{current_anio}")
            
            # --- CARGO DE CUOTA ORDINARIA ---
            fecha_cargo_cuota = date(current_anio, current_mes, 1)
            
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
            
            # --- CARGO DE INTERÉS MORATORIO ---
            if not (current_anio == 2022 and current_mes == 7):  # No calcular intereses el primer mes
                fecha_cargo_interes = date(current_anio, current_mes, 15)
                
                # Obtener tasa de interés
                tasa_interes = session.exec(
                    select(TasaInteresMora).where(
                        TasaInteresMora.año == current_anio,
                        TasaInteresMora.mes == current_mes
                    )
                ).first()
                
                if tasa_interes:
                    # *** LÓGICA CORREGIDA: Calcular saldo acumulado total ***
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
            
            # Avanzar al siguiente mes
            current_mes += 1
            if current_mes > 12:
                current_mes = 1
                current_anio += 1
        
        # Confirmar cambios
        session.commit()
        
        # Mostrar resumen
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE REGENERACIÓN CON LÓGICA CORREGIDA")
        print("=" * 70)
        print(f"💰 Cargos de cuota creados: {cargos_cuota_creados}")
        print(f"💸 Cargos de interés creados: {cargos_interes_creados}")
        print(f"📋 Total registros generados: {cargos_cuota_creados + cargos_interes_creados}")
        print("=" * 70)
        
        # Verificación final - mostrar algunos ejemplos de los nuevos cálculos
        print("\n🔍 VERIFICACIÓN DE EJEMPLOS:")
        
        ejemplos = [
            (2022, 8),  # Primer interés
            (2022, 9),  # Segundo interés 
            (2022, 10), # Tercer interés
        ]
        
        for anio, mes in ejemplos:
            registros_mes = session.exec(
                select(RegistroFinancieroApartamento).where(
                    RegistroFinancieroApartamento.apartamento_id == apartamento.id,
                    RegistroFinancieroApartamento.año_aplicable == anio,
                    RegistroFinancieroApartamento.mes_aplicable == mes
                ).order_by(RegistroFinancieroApartamento.fecha_efectiva)
            ).all()
            
            print(f"\n📅 {mes:02d}/{anio}:")
            for registro in registros_mes:
                tipo = "CUOTA" if registro.concepto_id == concepto_cuota.id else "INTERÉS"
                print(f"   {registro.fecha_efectiva} | {tipo:8} | ${registro.monto:>12,.2f}")
                if tipo == "INTERÉS":
                    print(f"      Descripción: {registro.descripcion_adicional}")

if __name__ == "__main__":
    print("🧹 LIMPIEZA Y REGENERACIÓN CON LÓGICA CORREGIDA")
    print("🏢 Apartamento: 9901")
    print("📅 Período: 07/2022 - 05/2025")
    print("🔧 Cambio: Interés sobre saldo total acumulado (no solo vencidos)")
    print()
    
    try:
        limpiar_y_regenerar()
        print("\n🎉 ¡Regeneración completada exitosamente!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
