#!/usr/bin/env python3
"""
Script de verificación del cálculo corregido de intereses
=========================================================

Este script verifica que los intereses se calculen correctamente sobre
el saldo neto (DEBITOS - CREDITOS) y no solo sobre débitos específicos.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from crear_cargos_historicos import GeneradorCargosHistoricos
from app.models.database import DATABASE_URL
from sqlmodel import create_engine, Session, text
from decimal import Decimal

def verificar_calculo_intereses():
    """Verifica el cálculo correcto de intereses"""
    
    print("🧮 VERIFICACIÓN DEL CÁLCULO CORREGIDO DE INTERESES")
    print("=" * 60)
    
    generador = GeneradorCargosHistoricos()
    engine = create_engine(DATABASE_URL)
    
    # Apartamento de prueba
    apartamento_id = 3  # Apartamento 9901
    año_test = 2024
    mes_test = 9  # Septiembre 2024
    
    print(f"\n📊 Analizando apartamento {apartamento_id} para {mes_test:02d}/{año_test}")
    print("-" * 50)
    
    # Mes anterior para el cálculo base
    if mes_test == 1:
        año_anterior = año_test - 1
        mes_anterior = 12
    else:
        año_anterior = año_test
        mes_anterior = mes_test - 1
    
    # 1. Mostrar el saldo neto calculado por el nuevo método
    saldo_neto = generador.calcular_saldo_neto_al_mes(apartamento_id, año_anterior, mes_anterior)
    print(f"✅ Saldo neto al {mes_anterior:02d}/{año_anterior}: ${saldo_neto:,.2f}")
    
    # 2. Desglosar el cálculo manualmente para verificación
    with Session(engine) as session:
        sql_desglose = f"""
            SELECT 
                concepto_id,
                SUM(CASE WHEN tipo_movimiento = 'DEBITO' THEN monto ELSE 0 END) as total_debitos,
                SUM(CASE WHEN tipo_movimiento = 'CREDITO' THEN monto ELSE 0 END) as total_creditos,
                SUM(CASE WHEN tipo_movimiento = 'DEBITO' THEN monto ELSE -monto END) as saldo_neto
            FROM registro_financiero_apartamento
            WHERE apartamento_id = {apartamento_id}
            AND fecha_efectiva <= '{año_anterior}-{mes_anterior:02d}-31'
            AND concepto_id != 3  -- Excluir intereses
            GROUP BY concepto_id
            ORDER BY concepto_id
        """
        
        resultados = session.exec(text(sql_desglose)).all()
        
        print(f"\n📋 Desglose por concepto hasta {mes_anterior:02d}/{año_anterior}:")
        print("Concepto | Débitos     | Créditos    | Saldo Neto")
        print("-" * 50)
        
        total_debitos = Decimal('0.00')
        total_creditos = Decimal('0.00')
        total_neto = Decimal('0.00')
        
        for r in resultados:
            print(f"   {r.concepto_id:2d}    | ${r.total_debitos:>10,.2f} | ${r.total_creditos:>10,.2f} | ${r.saldo_neto:>10,.2f}")
            total_debitos += r.total_debitos
            total_creditos += r.total_creditos
            total_neto += r.saldo_neto
        
        print("-" * 50)
        print(f" TOTAL   | ${total_debitos:>10,.2f} | ${total_creditos:>10,.2f} | ${total_neto:>10,.2f}")
        
        # 3. Verificar que coincide con nuestro método
        print(f"\n🔍 Verificación:")
        print(f"   Método calcular_saldo_neto_al_mes(): ${saldo_neto:,.2f}")
        print(f"   Cálculo manual:                      ${total_neto:,.2f}")
        
        if abs(saldo_neto - total_neto) < Decimal('0.01'):
            print("   ✅ ¡Los cálculos coinciden!")
        else:
            print("   ❌ Los cálculos NO coinciden")
    
    # 4. Mostrar la tasa de interés que se aplicaría
    tasa = generador.obtener_tasa_interes(año_anterior, mes_anterior)
    tasa_porcentaje = float(tasa) * 100
    
    print(f"\n💰 Cálculo de interés para {mes_test:02d}/{año_test}:")
    print(f"   Base de cálculo: ${saldo_neto:,.2f}")
    print(f"   Tasa aplicable:  {tasa_porcentaje:.2f}%")
    
    if saldo_neto > Decimal('0.01'):
        interes_calculado = saldo_neto * tasa
        print(f"   Interés resultante: ${interes_calculado:,.2f}")
    else:
        print("   No se genera interés (sin saldo pendiente)")
    
    # 5. Probar la generación real del interés
    print(f"\n🔧 Probando generación real del interés...")
    
    # Primero verificar si ya existe
    with Session(engine) as session:
        sql_existe = f"""
            SELECT COUNT(*) as existe
            FROM registro_financiero_apartamento
            WHERE apartamento_id = {apartamento_id}
            AND concepto_id = 3
            AND año_aplicable = {año_test}
            AND mes_aplicable = {mes_test}
        """
        
        existe = session.exec(text(sql_existe)).first().existe
        
        if existe > 0:
            print("   ⚠️  Ya existe un interés para este período, se omite la prueba")
        else:
            exito = generador.crear_cargo_interes_calculado(apartamento_id, año_test, mes_test)
            if exito:
                print("   ✅ Interés generado exitosamente")
            else:
                print("   ❌ Error generando interés")

def main():
    """Función principal"""
    try:
        verificar_calculo_intereses()
        
        print("\n" + "=" * 60)
        print("✅ VERIFICACIÓN COMPLETADA")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
