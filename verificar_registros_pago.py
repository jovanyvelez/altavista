#!/usr/bin/env python3
"""
Verificar que los pagos automáticos se registren correctamente en la BD
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date, timedelta
from app.services.pago_automatico import PagoAutomaticoService
from app.dependencies import get_db_session
from sqlmodel import Session, select
from app.models.apartamento import Apartamento
from app.models.registro_financiero_apartamento import RegistroFinancieroApartamento

def verificar_registros_pago():
    """Verificar registros de pago automático en la BD"""
    print("🔍 VERIFICACIÓN DE REGISTROS DE PAGO AUTOMÁTICO")
    print("=" * 60)
    
    apartamento_id = 11  # Apartamento 203
    
    with get_db_session() as session:
        # Buscar registros de prueba recientes (últimos 5 minutos)
        hace_5_min = datetime.now() - timedelta(minutes=5)
        
        registros_recientes = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.apartamento_id == apartamento_id)
            .where(RegistroFinancieroApartamento.fecha_registro >= hace_5_min)
            .where(RegistroFinancieroApartamento.referencia_pago.like("%PRUEBA%"))
            .order_by(RegistroFinancieroApartamento.fecha_registro.desc())
        ).all()
        
        print(f"📊 Registros de prueba encontrados: {len(registros_recientes)}")
        print("-" * 50)
        
        for i, registro in enumerate(registros_recientes[:5], 1):
            print(f"{i}. ID: {registro.id}")
            print(f"   Apartamento: {registro.apartamento_id}")
            print(f"   Concepto: {registro.concepto_id}")
            print(f"   Tipo: {registro.tipo_movimiento}")
            print(f"   Monto: ${registro.monto}")
            print(f"   Fecha efectiva: {registro.fecha_efectiva}")
            print(f"   Período: {registro.mes_aplicable:02d}/{registro.año_aplicable}")
            print(f"   Referencia: {registro.referencia_pago}")
            print(f"   Descripción: {registro.descripcion_adicional}")
            print(f"   Fecha creación: {registro.fecha_registro}")
            print()
        
        # Hacer una prueba más para confirmar que todo funciona
        print("🧪 Realizando prueba adicional de pago automático...")
        print("-" * 50)
        
        servicio = PagoAutomaticoService()
        
        # Pago de $5.00 para verificar
        resultado = servicio.procesar_pago_automatico(
            apartamento_id=apartamento_id,
            monto_pago=5.00,
            referencia="VERIFICACION-DECIMAL"
        )
        
        if resultado.get("success"):
            print("✅ Pago de verificación procesado exitosamente!")
            print(f"   Monto: $5.00")
            print(f"   Monto procesado: ${resultado['monto_procesado']}")
            print(f"   Registros creados: {len(resultado['pagos_realizados'])}")
            
            # Verificar que se guardó en la BD
            registro_verificacion = session.exec(
                select(RegistroFinancieroApartamento)
                .where(RegistroFinancieroApartamento.apartamento_id == apartamento_id)
                .where(RegistroFinancieroApartamento.referencia_pago == "VERIFICACION-DECIMAL")
                .order_by(RegistroFinancieroApartamento.id.desc())
                .limit(1)
            ).first()
            
            if registro_verificacion:
                print(f"✅ Registro guardado en BD:")
                print(f"   ID: {registro_verificacion.id}")
                print(f"   Monto en BD: ${registro_verificacion.monto} (tipo: {type(registro_verificacion.monto)})")
                print(f"   Fecha: {registro_verificacion.fecha_registro}")
            else:
                print("❌ No se encontró el registro en la BD")
        else:
            print(f"❌ Error en pago de verificación: {resultado.get('error')}")
    
    print(f"\n🎉 Verificación completada")
    print("=" * 60)

if __name__ == "__main__":
    verificar_registros_pago()
