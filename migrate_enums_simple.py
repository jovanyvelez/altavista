#!/usr/bin/env python3
"""
Script simplificado para migrar enums de PostgreSQL a VARCHAR
"""

import sys
sys.path.append('.')

from sqlalchemy import create_engine, text

# URL de la base de datos (copiada del archivo database.py)
DATABASE_URL = "postgresql://postgres:NqYMCFXBEQYYJ60u@db.xnmealeoourdfcgsyfqv.supabase.co:5432/postgres"

def check_current_state():
    """Verificar el estado actual de las columnas"""
    print("🔍 Verificando estado actual de la base de datos...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Verificar tipos de columnas actuales
        result = conn.execute(text("""
            SELECT table_name, column_name, data_type, udt_name
            FROM information_schema.columns 
            WHERE table_name IN ('registro_financiero_apartamento', 'usuario')
            AND column_name IN ('tipo_movimiento', 'rol')
            ORDER BY table_name, column_name
        """))
        
        print("📊 Estado actual de las columnas:")
        current_state = {}
        for row in result:
            table, column, data_type, udt_name = row
            print(f"  {table}.{column}: {data_type} ({udt_name})")
            current_state[f"{table}.{column}"] = udt_name
            
        return current_state

def migrate_if_needed():
    """Migrar solo si es necesario"""
    current_state = check_current_state()
    
    # Verificar si necesita migración
    needs_migration = any('enum' in state.lower() for state in current_state.values())
    
    if not needs_migration:
        print("✅ Las columnas ya son VARCHAR, no se necesita migración")
        return True
    
    print("🔄 Iniciando migración de ENUMs a VARCHAR...")
    
    engine = create_engine(DATABASE_URL)
    
    migration_commands = [
        # Migrar tipo_movimiento
        "ALTER TABLE registro_financiero_apartamento ADD COLUMN tipo_movimiento_new VARCHAR(10)",
        "UPDATE registro_financiero_apartamento SET tipo_movimiento_new = tipo_movimiento::text",
        "ALTER TABLE registro_financiero_apartamento DROP COLUMN tipo_movimiento",
        "ALTER TABLE registro_financiero_apartamento RENAME COLUMN tipo_movimiento_new TO tipo_movimiento",
        "ALTER TABLE registro_financiero_apartamento ADD CONSTRAINT check_tipo_movimiento CHECK (tipo_movimiento IN ('DEBITO', 'CREDITO'))",
        "ALTER TABLE registro_financiero_apartamento ALTER COLUMN tipo_movimiento SET NOT NULL",
        
        # Migrar rol de usuario
        "ALTER TABLE usuario ADD COLUMN rol_new VARCHAR(20)",
        "UPDATE usuario SET rol_new = rol::text",
        "ALTER TABLE usuario DROP COLUMN rol",
        "ALTER TABLE usuario RENAME COLUMN rol_new TO rol",
        "ALTER TABLE usuario ADD CONSTRAINT check_rol_usuario CHECK (rol IN ('ADMIN', 'PROPIETARIO'))",
        "ALTER TABLE usuario ALTER COLUMN rol SET NOT NULL"
    ]
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for i, command in enumerate(migration_commands):
                print(f"⚡ Ejecutando comando {i+1}/{len(migration_commands)}: {command[:50]}...")
                conn.execute(text(command))
            
            trans.commit()
            print("✅ Migración completada exitosamente")
            return True
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error durante la migración: {e}")
            return False

def verify_migration():
    """Verificar que la migración fue exitosa"""
    print("\n🔍 Verificando migración...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Verificar que las columnas son ahora VARCHAR
        result = conn.execute(text("""
            SELECT table_name, column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name IN ('registro_financiero_apartamento', 'usuario')
            AND column_name IN ('tipo_movimiento', 'rol')
            ORDER BY table_name, column_name
        """))
        
        print("✅ Estado después de la migración:")
        for row in result:
            table, column, data_type, max_length = row
            print(f"  {table}.{column}: {data_type}({max_length})")
        
        # Verificar constraints CHECK
        result = conn.execute(text("""
            SELECT conname, conrelid::regclass 
            FROM pg_constraint 
            WHERE contype = 'c' 
            AND conname LIKE 'check_%'
            AND conrelid::regclass::text IN ('registro_financiero_apartamento', 'usuario')
        """))
        
        constraints = result.fetchall()
        if constraints:
            print("\n✅ Constraints CHECK creados:")
            for constraint_name, table_name in constraints:
                print(f"  - {constraint_name} on {table_name}")
        
        return True

def test_models():
    """Probar que los modelos siguen funcionando"""
    print("\n🧪 Probando modelos actualizados...")
    
    try:
        from app.models.enums import TipoMovimientoEnum, RolUsuarioEnum
        from app.services.pago_automatico import PagoAutomaticoService
        
        # Probar que los enums funcionan
        movimiento = TipoMovimientoEnum.CREDITO
        rol = RolUsuarioEnum.ADMIN
        
        print(f"✅ TipoMovimientoEnum.CREDITO = '{movimiento.value}'")
        print(f"✅ RolUsuarioEnum.ADMIN = '{rol.value}'")
        
        # Probar el servicio de pago automático
        servicio = PagoAutomaticoService()
        print("✅ PagoAutomaticoService creado correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando modelos: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MIGRACIÓN DE ENUMS A VARCHAR")
    print("=" * 50)
    
    try:
        # Verificar estado actual
        current_state = check_current_state()
        
        # Migrar si es necesario
        success = migrate_if_needed()
        if not success:
            sys.exit(1)
        
        # Verificar migración
        verify_migration()
        
        # Probar modelos
        if test_models():
            print("\n" + "=" * 50)
            print("🎉 ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
            print("✨ Los enums ahora usan VARCHAR con CHECK constraints")
            print("🔧 Esto debería resolver los problemas de compatibilidad")
        else:
            print("\n❌ Los modelos no funcionan correctamente después de la migración")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
