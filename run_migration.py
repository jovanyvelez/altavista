#!/usr/bin/env python3
"""
Script simple para ejecutar la migración de enums usando psql directamente
"""

import subprocess
import os
import sys

def run_migration():
    """Ejecutar la migración usando psql"""
    print("🚀 MIGRACIÓN DE ENUMS A VARCHAR")
    print("=" * 50)
    
    # Información de conexión
    db_config = {
        'host': 'db.xnmealeoourdfcgsyfqv.supabase.co',
        'port': '5432', 
        'database': 'postgres',
        'user': 'postgres',
        'password': 'NqYMCFXBEQYYJ60u'
    }
    
    # Construir URL de conexión
    connection_url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    sql_file = "migrate_enums_direct.sql"
    
    if not os.path.exists(sql_file):
        print(f"❌ Archivo {sql_file} no encontrado")
        return False
    
    print(f"📄 Ejecutando script SQL: {sql_file}")
    print("🔗 Conectando a la base de datos...")
    
    try:
        # Ejecutar con psql
        result = subprocess.run([
            'psql', 
            connection_url,
            '-f', sql_file,
            '-v', 'ON_ERROR_STOP=1'
        ], 
        capture_output=True, 
        text=True, 
        timeout=60
        )
        
        if result.returncode == 0:
            print("✅ ¡Migración ejecutada exitosamente!")
            print("\n📋 Salida del script:")
            print(result.stdout)
            return True
        else:
            print("❌ Error ejecutando la migración")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout ejecutando la migración")
        return False
    except FileNotFoundError:
        print("❌ psql no encontrado. Instalarlo con: sudo apt-get install postgresql-client")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_migration():
    """Probar que la migración funcionó"""
    print("\n🧪 Probando el sistema después de la migración...")
    
    try:
        import sys
        sys.path.append('.')
        
        from app.services.pago_automatico import PagoAutomaticoService
        
        # Crear servicio
        servicio = PagoAutomaticoService()
        print("✅ PagoAutomaticoService creado correctamente")
        
        # Probar obtener resumen (esto usa la base de datos)
        resumen = servicio.obtener_resumen_deuda(11)
        print(f"✅ Consulta a BD exitosa - Deuda: ${resumen['total_deuda']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando el sistema: {e}")
        return False

def provide_alternatives():
    """Proporcionar alternativas si psql no funciona"""
    print("\n🔧 ALTERNATIVAS SI PSQL NO FUNCIONA:")
    print("=" * 50)
    print("""
1. 📋 EJECUTAR MANUALMENTE EN PGADMIN/CONSOLA:
   - Abrir pgAdmin o la consola de Supabase
   - Copiar y pegar el contenido de migrate_enums_direct.sql
   - Ejecutar el script completo

2. 🔗 USAR SUPABASE SQL EDITOR:
   - Ir a https://supabase.com/dashboard
   - Abrir el proyecto
   - Ir a SQL Editor
   - Pegar el script migrate_enums_direct.sql
   - Ejecutar

3. 🐍 EJECUTAR CON PYTHON (si hay problemas de conexión):
   - Instalar psycopg2: pip install psycopg2-binary
   - Ejecutar el script fix_enum_database.py

4. 🛠️ COMANDOS MANUALES BÁSICOS:
   Conectar a la BD y ejecutar:
   
   ALTER TABLE registro_financiero_apartamento ADD COLUMN tipo_movimiento_new VARCHAR(10);
   UPDATE registro_financiero_apartamento SET tipo_movimiento_new = tipo_movimiento::text;
   ALTER TABLE registro_financiero_apartamento DROP COLUMN tipo_movimiento;
   ALTER TABLE registro_financiero_apartamento RENAME COLUMN tipo_movimiento_new TO tipo_movimiento;
   ALTER TABLE registro_financiero_apartamento ADD CONSTRAINT check_tipo_movimiento CHECK (tipo_movimiento IN ('DEBITO', 'CREDITO'));
   ALTER TABLE registro_financiero_apartamento ALTER COLUMN tipo_movimiento SET NOT NULL;
    """)

if __name__ == "__main__":
    success = run_migration()
    
    if success:
        # Probar el sistema
        if test_migration():
            print("\n🎉 ¡MIGRACIÓN Y PRUEBAS COMPLETADAS!")
            print("✨ El sistema de pago automático debería funcionar ahora")
            print("🚀 Puedes probar el botón '🪄 Pagar' en la interfaz web")
        else:
            print("\n⚠️ Migración completada pero hay problemas en el sistema")
    else:
        provide_alternatives()
        print("\n📝 PASOS RECOMENDADOS:")
        print("1. Ejecutar la migración manualmente usando una de las alternativas")
        print("2. Probar el sistema de pago automático")
        print("3. Verificar que no hay más errores de enum")
