#!/usr/bin/env python3
"""
Script para migrar de ENUMs de PostgreSQL a VARCHAR con CHECK constraints
Esto simplifica el manejo de enums y evita problemas de compatibilidad
"""

import sys
import os
sys.path.append('.')

from sqlalchemy import create_engine, text
from app.config import get_database_url

def migrate_enums_to_varchar():
    """Migra enums de PostgreSQL a VARCHAR con constraints"""
    
    print("🔄 Iniciando migración de ENUMs a VARCHAR...")
    
    # Crear conexión a la base de datos
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    # Leer el script SQL
    script_path = "/home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio/migrate_enums_to_varchar.sql"
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("📄 Script SQL cargado correctamente")
        
        # Ejecutar el script
        with engine.connect() as conn:
            print("🔗 Conectado a la base de datos")
            
            # Ejecutar en una transacción
            trans = conn.begin()
            try:
                # Dividir el script en comandos individuales
                commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
                
                for i, command in enumerate(commands):
                    if command.upper().startswith(('BEGIN', 'COMMIT')):
                        continue  # Saltamos BEGIN/COMMIT ya que manejamos transacciones manualmente
                    
                    print(f"⚡ Ejecutando comando {i+1}/{len(commands)}...")
                    conn.execute(text(command))
                
                trans.commit()
                print("✅ Migración completada exitosamente")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error durante la migración: {e}")
                raise
                
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo SQL: {script_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def verify_migration():
    """Verifica que la migración fue exitosa"""
    print("\\n🔍 Verificando migración...")
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Verificar que las columnas son ahora VARCHAR
        tables_to_check = [
            ('registro_financiero_apartamento', 'tipo_movimiento'),
            ('usuario', 'rol'),
        ]
        
        for table_name, column_name in tables_to_check:
            result = conn.execute(text(f"""
                SELECT data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND column_name = '{column_name}'
            """))
            
            row = result.fetchone()
            if row:
                data_type, max_length = row
                print(f"✅ {table_name}.{column_name}: {data_type}({max_length})")
            else:
                print(f"❌ No se encontró {table_name}.{column_name}")
        
        # Verificar constraints CHECK
        result = conn.execute(text("""
            SELECT conname, conrelid::regclass 
            FROM pg_constraint 
            WHERE contype = 'c' 
            AND conname LIKE 'check_%tipo_%'
        """))
        
        constraints = result.fetchall()
        if constraints:
            print("\\n✅ Constraints CHECK creados:")
            for constraint_name, table_name in constraints:
                print(f"  - {constraint_name} on {table_name}")
        else:
            print("⚠️  No se encontraron constraints CHECK")

def test_enum_usage():
    """Prueba que los enums de Python siguen funcionando"""
    print("\\n🧪 Probando uso de enums en Python...")
    
    try:
        from app.models.enums import TipoMovimientoEnum, RolUsuarioEnum
        from app.services.pago_automatico import PagoAutomaticoService
        
        # Probar que los enums funcionan
        movimiento = TipoMovimientoEnum.CREDITO
        rol = RolUsuarioEnum.ADMIN
        
        print(f"✅ TipoMovimientoEnum.CREDITO = '{movimiento}'")
        print(f"✅ RolUsuarioEnum.ADMIN = '{rol}'")
        
        # Probar el servicio de pago automático
        servicio = PagoAutomaticoService()
        print("✅ PagoAutomaticoService creado correctamente")
        
        print("🎉 Los enums de Python funcionan correctamente")
        
    except Exception as e:
        print(f"❌ Error probando enums: {e}")
        raise

if __name__ == "__main__":
    print("🚀 MIGRACIÓN DE ENUMS A VARCHAR")
    print("=" * 50)
    
    try:
        migrate_enums_to_varchar()
        verify_migration()
        test_enum_usage()
        
        print("\\n" + "=" * 50)
        print("🎉 ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
        print("✨ Los enums ahora usan VARCHAR con CHECK constraints")
        print("🔧 Esto debería resolver los problemas de compatibilidad")
        
    except Exception as e:
        print(f"\\n❌ La migración falló: {e}")
        sys.exit(1)
