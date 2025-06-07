#!/usr/bin/env python3
"""
Verificación final de la lógica corregida de intereses moratorios
"""

from sqlmodel import create_engine, Session, select
from datetime import date
from decimal import Decimal
import os
import sys

# Añadir el directorio raíz del proyecto al sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.models.database import DATABASE_URL
from app.models.apartamento import Apartamento
from app.models.registro_financiero_apartamento import RegistroFinancieroApartamento
from app.models.enums import TipoMovimientoEnum

engine = create_engine(DATABASE_URL)

def verificar_logica_intereses():
    """Verifica que la lógica de intereses esté correcta"""
    
    with Session(engine) as session:
        print("🔍 VERIFICACIÓN FINAL DE LÓGICA DE INTERESES")
        print("=" * 60)
        
        # Obtener apartamento 9901
        apartamento = session.exec(
            select(Apartamento).where(Apartamento.identificador == "9901")
        ).first()
        
        # Obtener todos los registros ordenados por fecha
        registros = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
            .order_by(RegistroFinancieroApartamento.fecha_efectiva)
        ).all()
        
        print(f"📋 Total de registros: {len(registros)}")
        print()
        
        # Análisis detallado de los primeros meses
        print("📊 ANÁLISIS DETALLADO DE LOS PRIMEROS MESES:")
        print("-" * 60)
        
        saldo_acumulado = Decimal("0.00")
        
        # Julio 2022
        print("📅 JULIO 2022:")
        julio_registros = [r for r in registros if r.fecha_efectiva.year == 2022 and r.fecha_efectiva.month == 7]
        for registro in julio_registros:
            if registro.tipo_movimiento == TipoMovimientoEnum.DEBITO:
                saldo_acumulado += registro.monto
            else:
                saldo_acumulado -= registro.monto
            print(f"   {registro.fecha_efectiva} | {registro.monto:>12,.2f} | {registro.descripcion}")
        print(f"   💰 Saldo al final de julio: ${saldo_acumulado:,.2f}")
        print()
        
        # Agosto 2022
        print("📅 AGOSTO 2022:")
        agosto_registros = [r for r in registros if r.fecha_efectiva.year == 2022 and r.fecha_efectiva.month == 8]
        for registro in agosto_registros:
            if registro.tipo_movimiento == TipoMovimientoEnum.DEBITO:
                saldo_acumulado += registro.monto
            else:
                saldo_acumulado -= registro.monto
            print(f"   {registro.fecha_efectiva} | {registro.monto:>12,.2f} | {registro.descripcion}")
        print(f"   💰 Saldo al final de agosto: ${saldo_acumulado:,.2f}")
        print()
        
        # Septiembre 2022
        print("📅 SEPTIEMBRE 2022:")
        septiembre_registros = [r for r in registros if r.fecha_efectiva.year == 2022 and r.fecha_efectiva.month == 9]
        for registro in septiembre_registros:
            if registro.tipo_movimiento == TipoMovimientoEnum.DEBITO:
                saldo_acumulado += registro.monto
            else:
                saldo_acumulado -= registro.monto
            print(f"   {registro.fecha_efectiva} | {registro.monto:>12,.2f} | {registro.descripcion}")
        print(f"   💰 Saldo al final de septiembre: ${saldo_acumulado:,.2f}")
        print()
        
        # Resumen final
        print("=" * 60)
        print("📊 RESUMEN DE VERIFICACIÓN:")
        print("=" * 60)
        
        # Contar tipos de registros
        cuotas = [r for r in registros if "Cuota ordinaria" in r.descripcion]
        intereses = [r for r in registros if "Interés moratorio" in r.descripcion]
        
        total_cuotas = sum(r.monto for r in cuotas)
        total_intereses = sum(r.monto for r in intereses)
        
        print(f"📋 Registros de cuotas: {len(cuotas)}")
        print(f"💰 Total cuotas: ${total_cuotas:,.2f}")
        print(f"📋 Registros de intereses: {len(intereses)}")
        print(f"💸 Total intereses: ${total_intereses:,.2f}")
        print(f"💳 Deuda total: ${total_cuotas + total_intereses:,.2f}")
        print()
        
        # Verificar cálculo específico de septiembre
        print("🔍 VERIFICACIÓN ESPECÍFICA - INTERÉS SEPTIEMBRE 2022:")
        print("-" * 60)
        interes_sept = next((r for r in intereses if "09/2022" in r.descripcion), None)
        if interes_sept:
            print(f"📅 Fecha: {interes_sept.fecha_efectiva}")
            print(f"💸 Monto: ${interes_sept.monto:,.2f}")
            print(f"📝 Descripción: {interes_sept.descripcion}")
            
            # El saldo base debería ser $40,000 (julio) + $40,000 (agosto) + $676 (interés agosto) = $80,676
            saldo_esperado_base = Decimal("80676.00")
            tasa_septiembre = Decimal("1.77") / 100  # 1.77%
            interes_esperado = saldo_esperado_base * tasa_septiembre
            
            print(f"🧮 Cálculo esperado: ${saldo_esperado_base:,.2f} × 1.77% = ${interes_esperado:,.2f}")
            
            if abs(interes_sept.monto - interes_esperado) < Decimal("0.01"):
                print("✅ ¡Cálculo CORRECTO!")
            else:
                print("❌ Error en el cálculo")
        
        print("\n🎉 Verificación completada!")

if __name__ == "__main__":
    verificar_logica_intereses()
