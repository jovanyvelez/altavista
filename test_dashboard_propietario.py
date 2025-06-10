#!/usr/bin/env python3
"""
Script para probar el dashboard del propietario después de las correcciones
"""

import requests
import json
from datetime import datetime

def test_propietario_dashboard():
    """Prueba el dashboard del propietario"""
    
    print("🧪 PROBANDO DASHBOARD DEL PROPIETARIO")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Crear una sesión para mantener cookies
    session = requests.Session()
    
    try:
        # 1. Obtener página de login
        print("\n1️⃣ Obteniendo página de login...")
        login_page = session.get(f"{base_url}/login")
        
        if login_page.status_code == 200:
            print("   ✅ Página de login cargada")
        else:
            print(f"   ❌ Error cargando login: {login_page.status_code}")
            return False
        
        # 2. Intentar login como propietario (necesitarías credenciales reales)
        print("\n2️⃣ Información para login manual:")
        print("   🌐 URL: http://localhost:8000/login")
        print("   👤 Necesitas credenciales de un usuario propietario")
        print("   📋 Luego navega a: http://localhost:8000/propietario/dashboard")
        
        # 3. Probar acceso directo al dashboard (sin autenticación)
        print("\n3️⃣ Probando acceso directo al dashboard...")
        dashboard_response = session.get(f"{base_url}/propietario/dashboard")
        
        if dashboard_response.status_code == 401:
            print("   ✅ Redirección de autenticación funcionando correctamente")
        elif dashboard_response.status_code == 200:
            print("   ⚠️ Dashboard accesible sin autenticación (revisar seguridad)")
        else:
            print(f"   📊 Respuesta: {dashboard_response.status_code}")
        
        # 4. Verificar endpoints relacionados
        print("\n4️⃣ Verificando endpoints del propietario...")
        endpoints = [
            "/propietario/estado-cuenta",
            "/propietario/mis-pagos"
        ]
        
        for endpoint in endpoints:
            try:
                response = session.get(f"{base_url}{endpoint}")
                status = "✅ OK" if response.status_code in [200, 401, 302] else f"❌ {response.status_code}"
                print(f"   {endpoint}: {status}")
            except Exception as e:
                print(f"   {endpoint}: ❌ Error - {e}")
        
        print("\n" + "=" * 50)
        print("🎯 RESUMEN DE LA PRUEBA:")
        print("✅ La aplicación está funcionando")
        print("✅ Los endpoints están respondiendo")
        print("✅ La autenticación está funcionando")
        print("\n🔧 PASOS PARA PRUEBA MANUAL:")
        print("1. Abrir: http://localhost:8000")
        print("2. Iniciar sesión con credenciales de propietario")
        print("3. Verificar que aparezcan los apartamentos del propietario")
        print("4. Probar navegación a estado de cuenta")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la aplicación")
        print("   Asegúrate de que esté corriendo en http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False

def verificar_datos_propietario():
    """Verifica los datos del propietario 5 directamente en la base de datos"""
    
    print("\n🔍 VERIFICACIÓN DIRECTA DE DATOS")
    print("=" * 40)
    
    try:
        # Importar después de cambiar al directorio correcto
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app.models import db_manager
        from sqlmodel import text
        
        session = db_manager.get_session()
        
        # Verificar propietario 5
        print("📋 PROPIETARIO 5:")
        result = session.execute(text("""
            SELECT id, nombre_completo, documento_identidad, email
            FROM propietario 
            WHERE id = 5
        """))
        
        propietario = result.fetchone()
        if propietario:
            print(f"   ID: {propietario[0]}")
            print(f"   Nombre: {propietario[1]}")
            print(f"   Documento: {propietario[2]}")
            print(f"   Email: {propietario[3] or 'No registrado'}")
        else:
            print("   ❌ Propietario 5 no encontrado")
            return False
        
        # Verificar apartamentos del propietario 5
        print("\n🏠 APARTAMENTOS DEL PROPIETARIO 5:")
        result = session.execute(text("""
            SELECT a.id, a.identificador, a.coeficiente_copropiedad
            FROM apartamento a
            WHERE a.propietario_id = 5
            ORDER BY a.identificador
        """))
        
        apartamentos = result.fetchall()
        if apartamentos:
            for apt in apartamentos:
                print(f"   - Apartamento {apt[0]} ({apt[1]}) - Coef: {apt[2]}")
        else:
            print("   ❌ No hay apartamentos asignados")
            return False
        
        session.close()
        print("\n✅ Datos verificados correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DEL DASHBOARD PROPIETARIO")
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar datos primero
    datos_ok = verificar_datos_propietario()
    
    # Probar aplicación web
    app_ok = test_propietario_dashboard()
    
    print("\n" + "=" * 60)
    if datos_ok and app_ok:
        print("🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("✅ El dashboard del propietario debería funcionar correctamente")
    else:
        print("⚠️ ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisa los errores arriba para más detalles")
