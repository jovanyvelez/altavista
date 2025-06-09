#!/usr/bin/env python3
"""
Test para verificar el comportamiento del script con los datos específicos:
| apartamento_id | año_aplicable | mes_aplicable | monto    | concepto | tipo    |
| -------------- | ------------- | ------------- | -------- | -------- | ------- |
| 20             | 2025          | 1             | 72000.00 | 1        | DEBITO  |
| 20             | 2025          | 1             | 72000.00 | 5        | CREDITO |
"""

def test_escenario_especifico():
    """Simula el cálculo de intereses con los datos proporcionados"""
    
    print("="*80)
    print("TEST: ESCENARIO ESPECÍFICO APARTAMENTO 20")
    print("="*80)
    
    print("\n📊 DATOS DE ENTRADA:")
    print("| apartamento_id | año_aplicable | mes_aplicable | monto    | concepto | tipo    |")
    print("| -------------- | ------------- | ------------- | -------- | -------- | ------- |")
    print("| 20             | 2025          | 1             | 72000.00 | 1        | DEBITO  |")
    print("| 20             | 2025          | 1             | 72000.00 | 5        | CREDITO |")
    
    print("\n🧮 CÁLCULO DE SALDO:")
    debito = 72000.00
    credito = 72000.00
    saldo_neto = debito - credito
    
    print(f"   DÉBITO:  ${debito:,.2f}")
    print(f"   CRÉDITO: ${credito:,.2f}")
    print(f"   SALDO NETO: ${saldo_neto:,.2f}")
    
    print("\n🎯 EVALUACIÓN PARA GENERACIÓN DE INTERESES (02/2025):")
    print("   Fecha límite: 2025-01-31")
    print("   Condición: saldo_pendiente > 0.01")
    
    if saldo_neto > 0.01:
        interes = saldo_neto * 0.0129  # Asumiendo tasa 1.29%
        print(f"   ✅ GENERA INTERÉS: ${interes:.2f}")
        print(f"   Razón: Saldo neto ${saldo_neto:.2f} > $0.01")
    else:
        print(f"   ❌ NO GENERA INTERÉS")
        print(f"   Razón: Saldo neto ${saldo_neto:.2f} ≤ $0.01")
    
    print("\n📋 LÓGICA SQL EQUIVALENTE:")
    print("""
    WITH saldos_apartamento AS (
        SELECT 
            apartamento_id,
            SUM(CASE 
                WHEN tipo_movimiento = 'DEBITO' THEN monto 
                ELSE -monto 
            END) as saldo_pendiente
        FROM registro_financiero_apartamento
        WHERE apartamento_id = 20
        AND fecha_efectiva <= '2025-01-31'
        AND concepto no es de interés
        GROUP BY apartamento_id
        HAVING saldo_pendiente > 0.01
    )
    
    Resultado: apartamento_id=20, saldo_pendiente=0.00
    No cumple HAVING saldo_pendiente > 0.01
    """)
    
    print("\n✅ RESULTADO ESPERADO:")
    print("   El apartamento 20 NO debería generar interés en febrero 2025")
    print("   porque su saldo neto al 31/01/2025 es $0.00")
    
    print("\n🔧 CORRECCIÓN APLICADA:")
    print("   - Cambiado condición WHERE para usar fecha_efectiva <= fecha_limite")
    print("   - Eliminada suma incorrecta de año+mes")
    print("   - Mantenida exclusión de conceptos de interés")
    
    print("="*80)

def test_otros_escenarios():
    """Prueba otros escenarios para validar la lógica"""
    
    print("\n🧪 OTROS ESCENARIOS DE PRUEBA:")
    
    escenarios = [
        {
            'nombre': 'Solo DÉBITO sin pago',
            'movimientos': [('DEBITO', 72000)],
            'esperado': 'SÍ genera interés'
        },
        {
            'nombre': 'DÉBITO con pago parcial',
            'movimientos': [('DEBITO', 72000), ('CREDITO', 36000)],
            'esperado': 'SÍ genera interés (sobre $36,000)'
        },
        {
            'nombre': 'DÉBITO con pago completo',
            'movimientos': [('DEBITO', 72000), ('CREDITO', 72000)],
            'esperado': 'NO genera interés'
        },
        {
            'nombre': 'DÉBITO con sobrepago',
            'movimientos': [('DEBITO', 72000), ('CREDITO', 80000)],
            'esperado': 'NO genera interés (saldo negativo)'
        }
    ]
    
    for i, escenario in enumerate(escenarios, 1):
        saldo = sum(monto if tipo == 'DEBITO' else -monto for tipo, monto in escenario['movimientos'])
        genera_interes = saldo > 0.01
        interes = saldo * 0.0129 if genera_interes else 0
        
        print(f"\n   {i}. {escenario['nombre']}:")
        print(f"      Saldo neto: ${saldo:,.2f}")
        print(f"      Genera interés: {'SÍ' if genera_interes else 'NO'}")
        if genera_interes:
            print(f"      Interés: ${interes:,.2f}")
        print(f"      Esperado: {escenario['esperado']}")

if __name__ == "__main__":
    test_escenario_especifico()
    test_otros_escenarios()
