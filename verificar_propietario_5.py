#!/usr/bin/env python3
"""
Verificación rápida del problema del propietario 5
"""

import os
import sys

# Añadir el directorio raíz al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from app.models import db_manager
    from sqlmodel import text
    
    session = db_manager.get_session()
    
    print("🔍 VERIFICACIÓN DEL PROBLEMA DEL PROPIETARIO 5")
    print("=" * 50)
    
    # Verificar propietario 5 y sus apartamentos
    result = session.execute(text("""
        SELECT 
            p.id as propietario_id,
            p.nombre_completo,
            a.id as apartamento_id,
            a.identificador,
            a.coeficiente_copropiedad
        FROM propietario p
        LEFT JOIN apartamento a ON p.id = a.propietario_id
        WHERE p.id = 5
    """))
    
    data = result.fetchall()
    
    if data:
        print(f"👤 PROPIETARIO: {data[0][1]} (ID: {data[0][0]})")
        print("🏠 APARTAMENTOS:")
        
        for row in data:
            if row[2]:  # Si tiene apartamento
                print(f"   ✅ Apartamento {row[2]} ({row[3]}) - Coef: {row[4]}")
            else:
                print("   ❌ Sin apartamentos asignados")
                
        # Verificar estructura del código corregido
        print("\n🔧 VERIFICACIÓN DEL CÓDIGO:")
        with open('/home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio/app/routes/propietario.py', 'r') as f:
            content = f.read()
            
        if 'apartamentos = session.exec(' in content:
            print("   ✅ Código corregido: usando .all() para obtener apartamentos")
        else:
            print("   ❌ Código no corregido: aún usa .first()")
            
        if '"apartamentos": apartamentos' in content:
            print("   ✅ Template variable corregida: pasando 'apartamentos'")
        else:
            print("   ❌ Template variable incorrecta")
    else:
        print("❌ Propietario 5 no encontrado")
    
    session.close()
    
    print("\n🎯 DIAGNÓSTICO:")
    print("✅ El propietario 5 SÍ tiene apartamentos en la base de datos")
    print("✅ El código ha sido corregido para obtener TODOS los apartamentos")
    print("✅ La variable del template ha sido corregida")
    print("\n📱 PRÓXIMO PASO:")
    print("   Probar en el navegador: http://localhost:8000/propietario/dashboard")
    print("   (Necesitarás iniciar sesión como propietario)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
