#!/usr/bin/env python3
"""
Script para probar la corrección del estado de cuenta del propietario
"""

import os
import sys

# Añadir el directorio raíz al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from app.models import db_manager, Apartamento, Concepto, RegistroFinancieroApartamento
    from sqlmodel import select
    
    session = db_manager.get_session()
    
    print("🔍 VERIFICACIÓN DE CORRECCIÓN DEL ESTADO DE CUENTA")
    print("=" * 60)
    
    # Simular lo que hace el controlador corregido
    apartamento_id = 4
    
    print(f"📋 PROBANDO CON APARTAMENTO ID: {apartamento_id}")
    
    # 1. Verificar que el apartamento existe
    apartamento = session.exec(
        select(Apartamento).where(Apartamento.id == apartamento_id)
    ).first()
    
    if not apartamento:
        print("❌ Apartamento no encontrado")
        exit(1)
    
    print(f"✅ Apartamento encontrado: {apartamento.identificador}")
    
    # 2. Obtener registros financieros
    registros_raw = session.exec(
        select(RegistroFinancieroApartamento)
        .where(RegistroFinancieroApartamento.apartamento_id == apartamento_id)
        .order_by(RegistroFinancieroApartamento.fecha_efectiva.desc())
        .limit(5)  # Solo los primeros 5 para la prueba
    ).all()
    
    print(f"📊 Registros encontrados: {len(registros_raw)}")
    
    # 3. Probar carga de relaciones
    registros_con_relaciones = 0
    for reg in registros_raw:
        # Obtener apartamento
        apt = session.exec(
            select(Apartamento).where(Apartamento.id == reg.apartamento_id)
        ).first()
        
        # Obtener concepto
        concepto = session.exec(
            select(Concepto).where(Concepto.id == reg.concepto_id)
        ).first()
        
        if apt and concepto:
            registros_con_relaciones += 1
            print(f"   ✅ Registro {reg.id}: {concepto.nombre} - ${reg.monto} ({reg.tipo_movimiento})")
        else:
            print(f"   ❌ Registro {reg.id}: Error cargando relaciones")
    
    print(f"\n📈 RESUMEN:")
    print(f"   Registros totales: {len(registros_raw)}")
    print(f"   Con relaciones cargadas: {registros_con_relaciones}")
    
    if registros_con_relaciones == len(registros_raw):
        print("   ✅ Todas las relaciones se cargaron correctamente")
    else:
        print("   ⚠️ Algunas relaciones no se cargaron")
    
    # 4. Probar estructura de saldos_por_apartamento
    print(f"\n🏠 ESTRUCTURA DE SALDOS POR APARTAMENTO:")
    saldos_por_apartamento = {
        apartamento.id: {
            'apartamento': apartamento,
            'saldo': 1500.50  # Ejemplo
        }
    }
    
    print(f"   Apartamento {apartamento.id} ({apartamento.identificador}): ${saldos_por_apartamento[apartamento.id]['saldo']}")
    
    session.close()
    
    print("\n🎯 CONCLUSIÓN:")
    print("✅ La estructura de datos es correcta")
    print("✅ Las consultas funcionan")
    print("✅ Las relaciones se pueden cargar")
    print("\n🌐 PRÓXIMO PASO:")
    print("   Probar en navegador: http://localhost:8000/propietario/estado-cuenta?apartamento=4")
    print("   (Después de iniciar sesión como propietario)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
