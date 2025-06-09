#!/usr/bin/env python3
"""
Comparación entre la lógica anterior y la nueva lógica de intereses
"""

def comparar_logicas():
    """Comparar comportamiento de ambas lógicas"""
    
    print("="*80)
    print("COMPARACIÓN: LÓGICA ANTERIOR VS NUEVA LÓGICA")
    print("="*80)
    
    print("\n📊 ESCENARIO DE PRUEBA:")
    print("   - Apartamento 20")
    print("   - DÉBITO de $72,000 el 29/01/2025")
    print("   - Evaluación para generar intereses en 02/2025")
    
    print("\n🔴 LÓGICA ANTERIOR (30+ días):")
    print("   ❌ NO genera interés")
    print("   ❌ Razón: Deuda de solo 2-3 días (no > 30 días)")
    print("   ❌ Resultado: Apartamento no paga interés pese a no pagar a tiempo")
    
    print("\n🟢 NUEVA LÓGICA (fin de mes):")
    print("   ✅ SÍ genera interés")
    print("   ✅ Razón: Saldo pendiente al 31/01/2025")
    print("   ✅ Resultado: Interés de $929.28 (72,000 * 1.29%)")
    print("   ✅ Beneficio: Propietario tuvo todo enero para pagar sin interés")
    
    print("\n📋 OTROS EJEMPLOS:")
    
    ejemplos = [
        {
            'fecha_debito': '05/01/2025',
            'monto': 50000,
            'pago': None,
            'descripcion': 'Cuota ordinaria enero no pagada'
        },
        {
            'fecha_debito': '15/01/2025', 
            'monto': 25000,
            'pago': '30/01/2025',
            'descripcion': 'Cuota extraordinaria pagada a tiempo'
        },
        {
            'fecha_debito': '20/01/2025',
            'monto': 15000,
            'pago': None,
            'descripcion': 'Multa por daños no pagada'
        }
    ]
    
    for i, ejemplo in enumerate(ejemplos, 1):
        interes_anterior = "NO" if ejemplo['pago'] else "NO (< 30 días)"
        interes_nuevo = "NO" if ejemplo['pago'] else "SÍ"
        monto_interes = ejemplo['monto'] * 0.0129 if not ejemplo['pago'] else 0
        
        print(f"\n   Ejemplo {i}: {ejemplo['descripcion']}")
        print(f"   - Débito: ${ejemplo['monto']:,} el {ejemplo['fecha_debito']}")
        if ejemplo['pago']:
            print(f"   - Pago: {ejemplo['pago']}")
        print(f"   - Lógica anterior: {interes_anterior}")
        print(f"   - Nueva lógica: {interes_nuevo}")
        if monto_interes > 0:
            print(f"   - Interés generado: ${monto_interes:,.2f}")
    
    print("\n🎯 VENTAJAS DE LA NUEVA LÓGICA:")
    print("   ✅ Simplicidad: Solo verifica saldo al fin de mes")
    print("   ✅ Equidad: Todos tienen el mes completo para pagar")
    print("   ✅ Consistencia: Clara regla de cuándo se genera interés")
    print("   ✅ Incentivo: Motiva pago dentro del mes")
    
    print("\n⚙️  IMPLEMENTACIÓN TÉCNICA:")
    print("   - Eliminado: CTEs complejos de saldos_morosos")
    print("   - Simplificado: Solo CTE saldos_apartamento")
    print("   - Criterio: saldo_pendiente > 0.01 (cualquier deuda)")
    print("   - Base cálculo: Saldo total al final del mes anterior")
    
    print("="*80)

if __name__ == "__main__":
    comparar_logicas()
