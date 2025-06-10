#!/usr/bin/env python3
"""
Prueba real del sistema de pago automático con un pago pequeño
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

def prueba_pago_real_pequeño():
    """Prueba real con un pago muy pequeño para no afectar mucho los datos"""
    print("🧪 PRUEBA REAL DEL SISTEMA DE PAGO AUTOMÁTICO")
    print("=" * 60)
    
    servicio = PagoAutomaticoService()
    
    # Usar apartamento con deuda conocida
    apartamento_id = 11  # Apartamento 203
    
    print(f"\n📋 Estado ANTES del pago:")
    print("-" * 40)
    resumen_antes = servicio.obtener_resumen_deuda(apartamento_id)
    print(f"Total deuda: ${resumen_antes['total_deuda']:,.2f}")
    print(f"Primer período: {resumen_antes['detalle'][0] if resumen_antes['detalle'] else 'N/A'}")
    
    # Hacer un pago muy pequeño para prueba
    monto_prueba = 0.01  # Solo 1 centavo para no afectar los datos
    print(f"\n💰 Procesando pago de prueba: ${monto_prueba}")
    print("-" * 40)
    
    try:
        resultado = servicio.procesar_pago_automatico(
            apartamento_id=apartamento_id,
            monto_pago=monto_prueba,
            referencia="PRUEBA-AUTOMATICA"
        )
        
        if resultado.get("success"):
            print("✅ Pago procesado exitosamente!")
            print(f"   Monto procesado: ${resultado['monto_procesado']:,.2f}")
            print(f"   Pagos realizados: {len(resultado['pagos_realizados'])}")
            print(f"   Mensaje: {resultado['mensaje']}")
            
            # Mostrar detalles de los pagos
            for pago in resultado['pagos_realizados']:
                print(f"   - {pago['tipo']} {pago['periodo']}: ${pago['monto']:,.2f}")
        else:
            print(f"❌ Error en el pago: {resultado.get('error', 'Error desconocido')}")
            
    except Exception as e:
        print(f"❌ Excepción durante el pago: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n📋 Estado DESPUÉS del pago:")
    print("-" * 40)
    resumen_despues = servicio.obtener_resumen_deuda(apartamento_id)
    print(f"Total deuda: ${resumen_despues['total_deuda']:,.2f}")
    
    # Verificar la diferencia
    diferencia = resumen_antes['total_deuda'] - resumen_despues['total_deuda']
    print(f"Diferencia: ${diferencia:,.2f}")
    
    if abs(diferencia - monto_prueba) < 0.001:  # Permitir pequeñas diferencias de redondeo
        print("✅ La diferencia coincide con el monto pagado!")
    else:
        print(f"⚠️  La diferencia no coincide exactamente (esperado: ${monto_prueba})")
    
    print(f"\n🎉 Prueba completada")
    print("=" * 60)

if __name__ == "__main__":
    prueba_pago_real_pequeño()
