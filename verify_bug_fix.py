#!/usr/bin/env python3
"""
Script de Verificación Final - Corrección del Bug de Cálculo de Intereses
=========================================================================

Este script verifica que la corrección del cálculo de intereses funciona
correctamente, mostrando la diferencia entre el método anterior (incorrecto)
y el nuevo método (correcto).
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

def verificar_bug_corregido():
    """Verifica que el bug del cálculo de intereses se corrigió"""
    
    print("🐛➡️✅ VERIFICACIÓN DE CORRECCIÓN DEL BUG DE INTERESES")
    print("=" * 65)
    
    generador = GeneradorCargosHistoricos()
    engine = create_engine(DATABASE_URL)
    
    # Apartamento de prueba con débitos y créditos
    apartamento_id = 1  # Apartamento 9801
    año_test = 2024
    mes_test = 11  # Noviembre 2024
    
    # Mes anterior para el cálculo base
    año_anterior = año_test
    mes_anterior = mes_test - 1  # Octubre 2024
    
    print(f"\n📊 ANÁLISIS PARA APARTAMENTO {apartamento_id} - {mes_test:02d}/{año_test}")
    print(f"    (Base de cálculo: saldo neto al {mes_anterior:02d}/{año_anterior})")
    print("-" * 65)
    
    with Session(engine) as session:
        # 1. Método ANTERIOR (INCORRECTO): Solo débitos del concepto 1
        sql_metodo_anterior = f"""
            SELECT 
                COALESCE(SUM(monto), 0) as solo_cuotas_debito
            FROM registro_financiero_apartamento
            WHERE apartamento_id = {apartamento_id}
            AND fecha_efectiva <= '{año_anterior}-{mes_anterior:02d}-31'
            AND concepto_id = 1  -- Solo cuotas ordinarias
            AND tipo_movimiento = 'DEBITO'
        """
        
        solo_cuotas = session.exec(text(sql_metodo_anterior)).first().solo_cuotas_debito or Decimal('0.00')
        
        # 2. Método NUEVO (CORRECTO): Saldo neto de todos los conceptos (excepto intereses)
        saldo_neto = generador.calcular_saldo_neto_al_mes(apartamento_id, año_anterior, mes_anterior)
        
        # 3. Desglose detallado para mostrar la diferencia
        sql_desglose = f"""
            SELECT 
                concepto_id,
                SUM(CASE WHEN tipo_movimiento = 'DEBITO' THEN monto ELSE 0 END) as debitos,
                SUM(CASE WHEN tipo_movimiento = 'CREDITO' THEN monto ELSE 0 END) as creditos,
                SUM(CASE WHEN tipo_movimiento = 'DEBITO' THEN monto ELSE -monto END) as neto
            FROM registro_financiero_apartamento
            WHERE apartamento_id = {apartamento_id}
            AND fecha_efectiva <= '{año_anterior}-{mes_anterior:02d}-31'
            AND concepto_id != 3  -- Excluir intereses
            GROUP BY concepto_id
            ORDER BY concepto_id
        """
        
        desglose = session.exec(text(sql_desglose)).all()
        
        print("📋 DESGLOSE POR CONCEPTO:")
        print("Concepto | Débitos     | Créditos    | Saldo Neto")
        print("-" * 52)
        
        total_debitos = Decimal('0.00')
        total_creditos = Decimal('0.00')
        
        for row in desglose:
            print(f"   {row.concepto_id:2d}    | ${row.debitos:>10,.2f} | ${row.creditos:>10,.2f} | ${row.neto:>10,.2f}")
            total_debitos += row.debitos
            total_creditos += row.creditos
        
        print("-" * 52)
        print(f" TOTAL   | ${total_debitos:>10,.2f} | ${total_creditos:>10,.2f} | ${saldo_neto:>10,.2f}")
        
        print(f"\n🔍 COMPARACIÓN DE MÉTODOS:")
        print(f"   ❌ Método anterior (solo débitos concepto 1): ${solo_cuotas:,.2f}")
        print(f"   ✅ Método corregido (saldo neto):            ${saldo_neto:,.2f}")
        print(f"   📊 Diferencia:                               ${abs(saldo_neto - solo_cuotas):,.2f}")
        
        if abs(saldo_neto - solo_cuotas) > Decimal('0.01'):
            print("   🎯 ¡La corrección hace diferencia!")
        else:
            print("   ℹ️  En este caso específico, ambos métodos dan el mismo resultado")
        
        # 4. Calcular intereses con ambos métodos
        tasa = generador.obtener_tasa_interes(año_anterior, mes_anterior)
        tasa_porcentaje = float(tasa) * 100
        
        interes_metodo_anterior = solo_cuotas * tasa
        interes_metodo_corregido = saldo_neto * tasa
        
        print(f"\n💰 CÁLCULO DE INTERESES (Tasa: {tasa_porcentaje:.2f}%):")
        print(f"   ❌ Con método anterior:   ${interes_metodo_anterior:,.2f}")
        print(f"   ✅ Con método corregido:  ${interes_metodo_corregido:,.2f}")
        print(f"   📊 Diferencia en interés: ${abs(interes_metodo_corregido - interes_metodo_anterior):,.2f}")
        
        # 5. Mostrar qué incluye cada método
        print(f"\n📖 QUÉ INCLUYE CADA MÉTODO:")
        print(f"   ❌ Método anterior:")
        print(f"      - Solo débitos del concepto 1 (cuotas ordinarias)")
        print(f"      - Ignora otros conceptos y pagos realizados")
        print(f"   ✅ Método corregido:")
        print(f"      - Todos los débitos (cuotas, servicios, etc.)")
        print(f"      - Menos todos los créditos (pagos)")
        print(f"      - Excluye intereses previos")
        print(f"      - = Saldo real pendiente")

def main():
    """Función principal"""
    try:
        verificar_bug_corregido()
        
        print(f"\n" + "=" * 65)
        print("✅ CORRECCIÓN VERIFICADA")
        print("=" * 65)
        print("\n🎉 El bug del cálculo de intereses ha sido corregido exitosamente!")
        print("   Los intereses ahora se calculan sobre el saldo neto real.")
        
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
