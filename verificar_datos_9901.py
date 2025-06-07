#!/usr/bin/env python3
"""
Script de prueba para verificar la generación de cargos
sin confirmación interactiva del usuario
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

engine = create_engine(DATABASE_URL)

def verificar_datos_disponibles():
    """
    Verifica qué datos están disponibles en la base de datos
    """
    with Session(engine) as session:
        print("🔍 VERIFICANDO DATOS DISPONIBLES EN LA BASE DE DATOS")
        print("=" * 60)
        
        # 1. Verificar apartamento 9901
        apartamento = session.exec(
            select(Apartamento).where(Apartamento.identificador == "9901")
        ).first()
        
        if apartamento:
            print(f"✅ Apartamento 9901 encontrado (ID: {apartamento.id})")
        else:
            print("❌ Apartamento 9901 NO encontrado")
            return
        
        # 2. Verificar conceptos necesarios
        conceptos_necesarios = ["Cuota Ordinaria Administración", "Interés Moratorio"]
        conceptos_encontrados = {}
        
        for concepto_nombre in conceptos_necesarios:
            concepto = session.exec(
                select(Concepto).where(Concepto.nombre == concepto_nombre)
            ).first()
            
            if concepto:
                print(f"✅ Concepto '{concepto_nombre}' encontrado (ID: {concepto.id})")
                conceptos_encontrados[concepto_nombre] = concepto
            else:
                print(f"❌ Concepto '{concepto_nombre}' NO encontrado")
        
        # 3. Verificar configuraciones de cuota para apartamento 9901
        cuotas_config = session.exec(
            select(CuotaConfiguracion).where(
                CuotaConfiguracion.apartamento_id == apartamento.id
            ).order_by(CuotaConfiguracion.año, CuotaConfiguracion.mes)
        ).all()
        
        print(f"\n📊 CONFIGURACIONES DE CUOTA ENCONTRADAS: {len(cuotas_config)}")
        if cuotas_config:
            print("   Año | Mes | Monto")
            print("   " + "-" * 20)
            for cuota in cuotas_config[:10]:  # Mostrar solo las primeras 10
                print(f"   {cuota.año} | {cuota.mes:2d}  | ${cuota.monto_cuota_ordinaria_mensual}")
            if len(cuotas_config) > 10:
                print(f"   ... y {len(cuotas_config) - 10} más")
        
        # 4. Verificar tasas de interés moratorio
        tasas_interes = session.exec(
            select(TasaInteresMora).order_by(TasaInteresMora.año, TasaInteresMora.mes)
        ).all()
        
        print(f"\n💰 TASAS DE INTERÉS MORATORIO ENCONTRADAS: {len(tasas_interes)}")
        if tasas_interes:
            print("   Año | Mes | Tasa")
            print("   " + "-" * 25)
            for tasa in tasas_interes[:10]:  # Mostrar solo las primeras 10
                print(f"   {tasa.año} | {tasa.mes:2d}  | {tasa.tasa_interes_mensual*100:.2f}%")
            if len(tasas_interes) > 10:
                print(f"   ... y {len(tasas_interes) - 10} más")
        
        # 5. Verificar registros financieros existentes para apartamento 9901
        from app.models.registro_financiero_apartamento import RegistroFinancieroApartamento
        
        registros_existentes = session.exec(
            select(RegistroFinancieroApartamento).where(
                RegistroFinancieroApartamento.apartamento_id == apartamento.id
            ).order_by(RegistroFinancieroApartamento.fecha_efectiva)
        ).all()
        
        print(f"\n📋 REGISTROS FINANCIEROS EXISTENTES: {len(registros_existentes)}")
        if registros_existentes:
            print("   Primeros 5 registros:")
            for registro in registros_existentes[:5]:
                tipo = "CARGO" if registro.tipo_movimiento.value == "DEBITO" else "PAGO"
                print(f"   {registro.fecha_efectiva} | {tipo} | ${registro.monto} | {registro.descripcion_adicional}")
        
        print("\n" + "=" * 60)
        
        # Verificar si tenemos datos suficientes para el período requerido
        periodo_inicio = date(2022, 7, 1)
        periodo_fin = date(2025, 5, 31)
        
        cuotas_en_periodo = [c for c in cuotas_config if 
                           date(c.año, c.mes, 1) >= periodo_inicio and 
                           date(c.año, c.mes, 1) <= periodo_fin]
        
        tasas_en_periodo = [t for t in tasas_interes if 
                          date(t.año, t.mes, 1) >= periodo_inicio and 
                          date(t.año, t.mes, 1) <= periodo_fin]
        
        meses_total_periodo = ((2025 - 2022) * 12) + (5 - 7 + 1) + 12  # Cálculo aproximado
        
        print(f"📅 ANÁLISIS DEL PERÍODO (07/2022 - 05/2025):")
        print(f"   Configuraciones de cuota en período: {len(cuotas_en_periodo)}")
        print(f"   Tasas de interés en período: {len(tasas_en_periodo)}")
        print(f"   Meses aproximados en período: ~{meses_total_periodo}")
        
        if len(cuotas_en_periodo) > 0:
            print("   ✅ HAY configuraciones de cuota para generar cargos")
        else:
            print("   ❌ NO hay configuraciones de cuota para el período")
            
        if len(tasas_en_periodo) > 0:
            print("   ✅ HAY tasas de interés para generar intereses moratorios")
        else:
            print("   ❌ NO hay tasas de interés para el período")

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO DE DATOS PARA GENERACIÓN DE CARGOS")
    print("=" * 60)
    print(f"🗃️  Conectando a: {DATABASE_URL[:50]}...")
    print()
    
    try:
        verificar_datos_disponibles()
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()
