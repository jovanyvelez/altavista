#!/usr/bin/env python3
"""
Test específico de la lógica de pago automático con un caso controlado
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
from app.services.pago_automatico import PagoAutomaticoService

def demo_pago_automatico():
    """Demostración de la funcionalidad de pago automático"""
    print("🚀 DEMOSTRACIÓN DEL SISTEMA DE PAGO AUTOMÁTICO")
    print("=" * 60)
    
    servicio = PagoAutomaticoService()
    
    # Test con un apartamento específico
    apartamento_id = 11  # Usar apartamento 203 que sabemos tiene datos
    
    print(f"\n📋 Resumen de Deuda - Apartamento ID: {apartamento_id}")
    print("-" * 50)
    
    resumen = servicio.obtener_resumen_deuda(apartamento_id)
    
    print(f"💰 Total deuda: ${resumen['total_deuda']:,.2f}")
    print(f"📈 Total intereses: ${resumen['total_intereses']:,.2f}")
    print(f"🏠 Total cuotas: ${resumen['total_cuotas']:,.2f}")
    print(f"📅 Períodos pendientes: {resumen['periodos_pendientes']}")
    
    if resumen['detalle']:
        print(f"\n📊 Detalle de Períodos Pendientes (orden de pago):")
        print("-" * 50)
        for i, periodo in enumerate(resumen['detalle'], 1):
            tipo = "💸 Interés" if periodo['concepto_id'] == 3 else "🏠 Cuota"
            print(f"{i:2d}. {tipo} {periodo['mes']:02d}/{periodo['año']} - ${periodo['saldo']:,.2f}")
    
    # Simulación de diferentes escenarios de pago
    if resumen['total_deuda'] > 0:
        escenarios = [
            ("Pago parcial pequeño", 500.0),
            ("Pago de un interés completo", 1000.0),
            ("Pago de cuota + interés", 81000.0),
            ("Pago total de la deuda", float(resumen['total_deuda']))
        ]
        
        print(f"\n🎯 SIMULACIONES DE PAGO (sin ejecutar)")
        print("=" * 60)
        
        for descripcion, monto in escenarios:
            print(f"\n📝 {descripcion}: ${monto:,.2f}")
            print("-" * 50)
            
            # Simular la distribución
            monto_restante = monto
            pagos_simulados = []
            
            for periodo in resumen['detalle']:
                if monto_restante <= 0:
                    break
                
                saldo_periodo = float(periodo['saldo'])
                monto_aplicado = min(monto_restante, saldo_periodo)
                
                tipo = "Interés" if periodo['concepto_id'] == 3 else "Cuota"
                pagos_simulados.append({
                    'tipo': tipo,
                    'periodo': f"{periodo['mes']:02d}/{periodo['año']}",
                    'monto': monto_aplicado,
                    'saldo_original': saldo_periodo
                })
                
                monto_restante -= monto_aplicado
            
            # Mostrar resultado de la simulación
            for pago in pagos_simulados:
                if pago['monto'] == pago['saldo_original']:
                    estado = "COMPLETO"
                else:
                    estado = f"PARCIAL (${pago['saldo_original'] - pago['monto']:,.2f} pendiente)"
                
                print(f"   ✅ {pago['tipo']} {pago['periodo']}: ${pago['monto']:,.2f} - {estado}")
            
            if monto_restante > 0:
                print(f"   💰 Exceso: ${monto_restante:,.2f} (se registraría como Pago en Exceso)")
            
            print(f"   💵 Total procesado: ${monto - monto_restante:,.2f}")
    
    print(f"\n🎉 Demostración completada")
    print(f"💡 Para usar: hacer clic en el botón '🪄 Pagar' en la interfaz web")
    print("=" * 60)

if __name__ == "__main__":
    demo_pago_automatico()
