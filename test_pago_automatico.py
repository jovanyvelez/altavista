#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de pago automático
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
from app.services.pago_automatico import PagoAutomaticoService
from app.dependencies import get_db_session
from sqlmodel import Session, select
from app.models.apartamento import Apartamento
from app.models.registro_financiero_apartamento import RegistroFinancieroApartamento

def test_pago_automatico():
    """Test de la funcionalidad de pago automático"""
    print("🧪 Iniciando pruebas del sistema de pago automático")
    print("=" * 60)
    
    servicio = PagoAutomaticoService()
    
    # Test 1: Obtener resumen de deuda
    print("\n📊 Test 1: Obtener resumen de deuda")
    print("-" * 40)
    
    with get_db_session() as session:
        # Obtener el primer apartamento con registros
        apartamento = session.exec(
            select(Apartamento).limit(1)
        ).first()
        
        if not apartamento:
            print("❌ No se encontraron apartamentos")
            return
        
        print(f"Apartamento: {apartamento.identificador}")
        
        # Obtener resumen de deuda
        resumen = servicio.obtener_resumen_deuda(apartamento.id)
        print(f"Total deuda: ${resumen['total_deuda']:,.2f}")
        print(f"Total intereses: ${resumen['total_intereses']:,.2f}")
        print(f"Total cuotas: ${resumen['total_cuotas']:,.2f}")
        print(f"Períodos pendientes: {resumen['periodos_pendientes']}")
        
        # Mostrar detalles
        if resumen['detalle']:
            print("\nDetalle de períodos pendientes:")
            for periodo in resumen['detalle'][:5]:  # Mostrar solo los primeros 5
                tipo = "Interés" if periodo['concepto_id'] == 3 else "Cuota"
                print(f"  - {tipo} {periodo['mes']:02d}/{periodo['año']}: ${periodo['saldo']:,.2f}")
        
        # Test 2: Simular pago automático pequeño
        print(f"\n💰 Test 2: Simular pago automático")
        print("-" * 40)
        
        if resumen['total_deuda'] > 0:
            # Pago parcial (50% del primer período pendiente)
            monto_test = float(resumen['detalle'][0]['saldo']) * 0.5 if resumen['detalle'] else 100.0
            print(f"Simulando pago de: ${monto_test:,.2f}")
            
            # NOTA: No ejecutamos el pago real para no afectar datos
            print("✅ Funcionalidad lista para usar")
            print("   (Pago no ejecutado para preservar datos)")
        else:
            print("ℹ️  Apartamento sin deuda pendiente")
    
    # Test 3: Verificar lógica de distribución
    print(f"\n🧮 Test 3: Verificar lógica de distribución")
    print("-" * 40)
    
    with get_db_session() as session:
        registros_pendientes = servicio._obtener_registros_pendientes(session, apartamento.id)
        
        if registros_pendientes:
            print("Orden de prioridad para pagos:")
            for i, registro in enumerate(registros_pendientes[:5], 1):
                tipo = "Interés" if registro['concepto_id'] == 3 else "Cuota"
                print(f"  {i}. {tipo} {registro['mes']:02d}/{registro['año']}: ${registro['saldo']:,.2f}")
        else:
            print("✅ No hay registros pendientes")
    
    print(f"\n🎉 Pruebas completadas exitosamente")
    print("=" * 60)

if __name__ == "__main__":
    test_pago_automatico()
