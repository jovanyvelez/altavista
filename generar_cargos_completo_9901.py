#!/usr/bin/env python3
"""
Script para generar cargos de cuota ordinaria e intereses moratorios
para el apartamento 9901 desde julio 2022 hasta mayo 2025.

Este script:
1. Conecta a la base de datos de Supabase
2. Genera cargos de cuota ordinaria basados en cuota_configuracion
3. Calcula y genera intereses moratorios basados en saldos en mora
4. Usa los conceptos apropiados de la tabla concepto
"""

from sqlmodel import create_engine, Session, select
from datetime import date, datetime
from decimal import Decimal
import os
import sys

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

# --- CONFIGURACIÓN ---
APARTAMENTO_IDENTIFICADOR = "9901"
CONCEPTO_CUOTA_ORDINARIA = "Cuota Ordinaria Administración"
CONCEPTO_INTERES_MORATORIO = "Intereses por Mora"

FECHA_INICIO_ANIO = 2022
FECHA_INICIO_MES = 7
FECHA_FIN_ANIO = 2025
FECHA_FIN_MES = 5

# Día del mes para aplicar cargos (1 = primer día del mes)
DIA_CARGO_CUOTA = 1
DIA_CARGO_INTERES = 15  # Calcular intereses a mitad de mes
# ---------------------

engine = create_engine(DATABASE_URL)

def obtener_saldo_apartamento(session: Session, apartamento_id: int, hasta_fecha: date) -> Decimal:
    """
    Calcula el saldo acumulado del apartamento hasta una fecha específica.
    Saldo = DEBITOS - CREDITOS
    """
    # Obtener todos los registros hasta la fecha
    statement = select(RegistroFinancieroApartamento).where(
        RegistroFinancieroApartamento.apartamento_id == apartamento_id,
        RegistroFinancieroApartamento.fecha_efectiva <= hasta_fecha
    )
    
    registros = session.exec(statement).all()
    
    saldo = Decimal("0.00")
    for registro in registros:
        if registro.tipo_movimiento == TipoMovimientoEnum.DEBITO:
            saldo += registro.monto
        else:  # CREDITO
            saldo -= registro.monto
    
    return saldo

def obtener_saldo_en_mora(session: Session, apartamento_id: int, fecha_calculo: date) -> Decimal:
    """
    Calcula el saldo en mora (solo los cargos vencidos sin pagar).
    Se considera en mora los cargos con más de 30 días de vencimiento.
    """
    from dateutil.relativedelta import relativedelta
    
    fecha_limite_mora = fecha_calculo - relativedelta(days=30)
    
    # Obtener todos los DEBITOS hasta la fecha límite de mora
    statement_debitos = select(RegistroFinancieroApartamento).where(
        RegistroFinancieroApartamento.apartamento_id == apartamento_id,
        RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.DEBITO,
        RegistroFinancieroApartamento.fecha_efectiva <= fecha_limite_mora
    )
    
    debitos = session.exec(statement_debitos).all()
    total_debitos = sum(registro.monto for registro in debitos)
    
    # Obtener todos los CREDITOS hasta la fecha de cálculo
    statement_creditos = select(RegistroFinancieroApartamento).where(
        RegistroFinancieroApartamento.apartamento_id == apartamento_id,
        RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.CREDITO,
        RegistroFinancieroApartamento.fecha_efectiva <= fecha_calculo
    )
    
    creditos = session.exec(statement_creditos).all()
    total_creditos = sum(registro.monto for registro in creditos)
    
    saldo_mora = total_debitos - total_creditos
    return max(saldo_mora, Decimal("0.00"))  # No puede ser negativo

def generar_cargos_apartamento():
    """
    Función principal que genera los cargos para el apartamento 9901
    """
    
    with Session(engine) as session:
        # 1. Obtener referencias de base de datos
        print("🔍 Obteniendo referencias de base de datos...")
        
        # Obtener apartamento
        apartamento = session.exec(
            select(Apartamento).where(Apartamento.identificador == APARTAMENTO_IDENTIFICADOR)
        ).first()
        
        if not apartamento:
            print(f"❌ Error: No se encontró el apartamento '{APARTAMENTO_IDENTIFICADOR}'")
            return
        
        # Obtener conceptos
        concepto_cuota = session.exec(
            select(Concepto).where(Concepto.nombre == CONCEPTO_CUOTA_ORDINARIA)
        ).first()
        
        concepto_interes = session.exec(
            select(Concepto).where(Concepto.nombre == CONCEPTO_INTERES_MORATORIO)
        ).first()
        
        if not concepto_cuota:
            print(f"❌ Error: No se encontró el concepto '{CONCEPTO_CUOTA_ORDINARIA}'")
            return
            
        if not concepto_interes:
            print(f"❌ Error: No se encontró el concepto '{CONCEPTO_INTERES_MORATORIO}'")
            return
        
        print(f"✅ Apartamento ID: {apartamento.id}")
        print(f"✅ Concepto Cuota ID: {concepto_cuota.id}")
        print(f"✅ Concepto Interés ID: {concepto_interes.id}")
        print()
        
        # 2. Iterar por cada mes en el rango
        cargos_cuota_creados = 0
        cargos_interes_creados = 0
        cargos_cuota_omitidos = 0
        cargos_interes_omitidos = 0
        
        current_anio = FECHA_INICIO_ANIO
        current_mes = FECHA_INICIO_MES
        
        print("🔄 Iniciando generación de cargos...")
        print()
        
        while (current_anio < FECHA_FIN_ANIO) or (current_anio == FECHA_FIN_ANIO and current_mes <= FECHA_FIN_MES):
            
            print(f"📅 Procesando {current_mes:02d}/{current_anio}")
            
            # --- GENERAR CARGO DE CUOTA ORDINARIA ---
            fecha_cargo_cuota = date(current_anio, current_mes, DIA_CARGO_CUOTA)
            
            # Verificar si ya existe el cargo de cuota
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
                # Buscar configuración de cuota para este apartamento, año y mes
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
                    cargos_cuota_creados += 1
                    print(f"   ✅ Cargo cuota: ${cuota_config.monto_cuota_ordinaria_mensual}")
                else:
                    print(f"   ⚠️  No hay configuración de cuota para {current_mes:02d}/{current_anio}")
            else:
                cargos_cuota_omitidos += 1
                print(f"   ⏭️  Cargo cuota ya existe")
            
            # --- GENERAR CARGO DE INTERÉS MORATORIO ---
            if current_mes >= 2 or current_anio > FECHA_INICIO_ANIO:  # No calcular intereses el primer mes
                fecha_cargo_interes = date(current_anio, current_mes, DIA_CARGO_INTERES)
                
                # Verificar si ya existe el cargo de interés
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
                    # Obtener tasa de interés para este mes/año
                    tasa_interes = session.exec(
                        select(TasaInteresMora).where(
                            TasaInteresMora.año == current_anio,
                            TasaInteresMora.mes == current_mes
                        )
                    ).first()
                    
                    if tasa_interes:
                        # Calcular saldo en mora al inicio del mes
                        fecha_calculo_mora = date(current_anio, current_mes, 1)
                        saldo_mora = obtener_saldo_en_mora(session, apartamento.id, fecha_calculo_mora)
                        
                        if saldo_mora > Decimal("0.00"):
                            interes_calculado = saldo_mora * tasa_interes.tasa_interes_mensual
                            interes_calculado = interes_calculado.quantize(Decimal("0.01"))  # Redondear a 2 decimales
                            
                            if interes_calculado > Decimal("0.00"):
                                nuevo_cargo_interes = RegistroFinancieroApartamento(
                                    apartamento_id=apartamento.id,
                                    fecha_registro=datetime.now(),
                                    fecha_efectiva=fecha_cargo_interes,
                                    concepto_id=concepto_interes.id,
                                    descripcion_adicional=f"Interés moratorio {current_mes:02d}/{current_anio} - Tasa: {tasa_interes.tasa_interes_mensual*100:.2f}% sobre ${saldo_mora}",
                                    tipo_movimiento=TipoMovimientoEnum.DEBITO,
                                    monto=interes_calculado,
                                    mes_aplicable=current_mes,
                                    año_aplicable=current_anio
                                )
                                
                                session.add(nuevo_cargo_interes)
                                cargos_interes_creados += 1
                                print(f"   💰 Interés moratorio: ${interes_calculado} (tasa: {tasa_interes.tasa_interes_mensual*100:.2f}% sobre ${saldo_mora})")
                            else:
                                print(f"   💸 Interés calculado: $0.00 (no se genera cargo)")
                        else:
                            print(f"   📊 Sin saldo en mora para intereses")
                    else:
                        print(f"   ⚠️  No hay tasa de interés configurada para {current_mes:02d}/{current_anio}")
                else:
                    cargos_interes_omitidos += 1
                    print(f"   ⏭️  Cargo interés ya existe")
            
            print()
            
            # Avanzar al siguiente mes
            current_mes += 1
            if current_mes > 12:
                current_mes = 1
                current_anio += 1
        
        # 3. Confirmar cambios en la base de datos
        session.commit()
        
        # 4. Mostrar resumen
        print("=" * 80)
        print("📊 RESUMEN DE GENERACIÓN DE CARGOS")
        print("=" * 80)
        print(f"🏢 Apartamento: {APARTAMENTO_IDENTIFICADOR}")
        print(f"📅 Período: {FECHA_INICIO_MES:02d}/{FECHA_INICIO_ANIO} - {FECHA_FIN_MES:02d}/{FECHA_FIN_ANIO}")
        print()
        print("💰 CARGOS DE CUOTA ORDINARIA:")
        print(f"   ✅ Creados: {cargos_cuota_creados}")
        print(f"   ⏭️  Omitidos (ya existían): {cargos_cuota_omitidos}")
        print()
        print("💸 CARGOS DE INTERÉS MORATORIO:")
        print(f"   ✅ Creados: {cargos_interes_creados}")
        print(f"   ⏭️  Omitidos (ya existían): {cargos_interes_omitidos}")
        print()
        
        if cargos_cuota_creados > 0 or cargos_interes_creados > 0:
            print("🎉 ¡Cargos generados exitosamente!")
        else:
            print("ℹ️  No se generaron nuevos cargos (posiblemente ya existían todos)")
        
        print("=" * 80)

def verificar_datos_requeridos():
    """
    Verifica que existan los datos necesarios en la base de datos
    """
    with Session(engine) as session:
        print("🔍 Verificando datos requeridos...")
        
        # Verificar apartamento
        apartamento = session.exec(
            select(Apartamento).where(Apartamento.identificador == APARTAMENTO_IDENTIFICADOR)
        ).first()
        
        if not apartamento:
            print(f"❌ Apartamento '{APARTAMENTO_IDENTIFICADOR}' no encontrado")
            return False
        
        # Verificar conceptos
        conceptos_requeridos = [CONCEPTO_CUOTA_ORDINARIA, CONCEPTO_INTERES_MORATORIO]
        for concepto_nombre in conceptos_requeridos:
            concepto = session.exec(
                select(Concepto).where(Concepto.nombre == concepto_nombre)
            ).first()
            
            if not concepto:
                print(f"❌ Concepto '{concepto_nombre}' no encontrado")
                return False
        
        # Verificar configuraciones de cuota (al menos algunas)
        count_cuotas = session.exec(
            select(CuotaConfiguracion).where(
                CuotaConfiguracion.apartamento_id == apartamento.id
            )
        ).all()
        
        if not count_cuotas:
            print(f"⚠️  No hay configuraciones de cuota para el apartamento {APARTAMENTO_IDENTIFICADOR}")
            print("   El script solo generará intereses moratorios")
        
        # Verificar tasas de interés (al menos algunas)
        tasas = session.exec(select(TasaInteresMora)).all()
        
        if not tasas:
            print(f"⚠️  No hay tasas de interés moratorio configuradas")
            print("   El script solo generará cargos de cuota ordinaria")
        
        print("✅ Verificación completada")
        return True

if __name__ == "__main__":
    print("=" * 80)
    print("🏢 GENERADOR DE CARGOS APARTAMENTO 9901")
    print("=" * 80)
    print(f"📅 Período: {FECHA_INICIO_MES:02d}/{FECHA_INICIO_ANIO} - {FECHA_FIN_MES:02d}/{FECHA_FIN_ANIO}")
    print(f"🗃️  Base de datos: {DATABASE_URL[:50]}...")
    print()
    
    if not verificar_datos_requeridos():
        print("❌ Faltan datos requeridos. Verifique la configuración de la base de datos.")
        sys.exit(1)
    
    print()
    confirmacion = input("¿Está seguro de que desea continuar con la generación de cargos? (s/N): ")
    
    if confirmacion.lower() == 's':
        print("\n🚀 Iniciando generación de cargos...")
        print()
        try:
            generar_cargos_apartamento()
        except Exception as e:
            print(f"❌ Error durante la generación: {e}")
            sys.exit(1)
    else:
        print("❌ Operación cancelada por el usuario.")
