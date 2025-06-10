#!/usr/bin/env python3
"""
Script para migrar enums de PostgreSQL a VARCHAR
Resuelve el error: column "tipo_movimiento" is of type tipo_movimiento_enum but expression is of type character varying
"""

import sys
import os
sys.path.append('.')

from sqlalchemy import create_engine, text

# URL de la base de datos (desde database.py)
DATABASE_URL = "postgresql://postgres:NqYMCFXBEQYYJ60u@db.xnmealeoourdfcgsyfqv.supabase.co:5432/postgres"

def backup_data():
    """Hacer backup de los datos críticos antes de la migración"""
    print("📦 Creando backup de datos críticos...")
    
    engine = create_engine(DATABASE_URL)
    
    backup_data = {}
    
    with engine.connect() as conn:
        # Backup registro_financiero_apartamento
        result = conn.execute(text("""
            SELECT id, apartamento_id, tipo_movimiento, monto, fecha_efectiva, concepto_id
            FROM registro_financiero_apartamento 
            ORDER BY id
        """))
        
        backup_data['registros'] = []
        for row in result:
            backup_data['registros'].append({
                'id': row[0],
                'apartamento_id': row[1], 
                'tipo_movimiento': row[2],
                'monto': row[3],
                'fecha_efectiva': row[4],
                'concepto_id': row[5]
            })
        
        print(f"✅ Backup: {len(backup_data['registros'])} registros financieros")
        
        # Backup usuarios
        result = conn.execute(text("""
            SELECT id, username, rol, is_active
            FROM usuario
            ORDER BY id
        """))
        
        backup_data['usuarios'] = []
        for row in result:
            backup_data['usuarios'].append({
                'id': row[0],
                'username': row[1],
                'rol': row[2], 
                'is_active': row[3]
            })
            
        print(f"✅ Backup: {len(backup_data['usuarios'])} usuarios")
    
    return backup_data

def migrate_registro_financiero():
    """Migrar la tabla registro_financiero_apartamento"""
    print("\n🔄 Migrando registro_financiero_apartamento...")
    
    engine = create_engine(DATABASE_URL)
    
    migration_steps = [
        # Paso 1: Agregar nueva columna VARCHAR
        "ALTER TABLE registro_financiero_apartamento ADD COLUMN tipo_movimiento_new VARCHAR(10)",
        
        # Paso 2: Copiar datos convertidos
        "UPDATE registro_financiero_apartamento SET tipo_movimiento_new = tipo_movimiento::text",
        
        # Paso 3: Eliminar columna original  
        "ALTER TABLE registro_financiero_apartamento DROP COLUMN tipo_movimiento",
        
        # Paso 4: Renombrar nueva columna
        "ALTER TABLE registro_financiero_apartamento RENAME COLUMN tipo_movimiento_new TO tipo_movimiento",
        
        # Paso 5: Agregar constraint de validación
        "ALTER TABLE registro_financiero_apartamento ADD CONSTRAINT check_tipo_movimiento CHECK (tipo_movimiento IN ('DEBITO', 'CREDITO'))",
        
        # Paso 6: Hacer NOT NULL
        "ALTER TABLE registro_financiero_apartamento ALTER COLUMN tipo_movimiento SET NOT NULL"
    ]
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for i, step in enumerate(migration_steps):
                print(f"  ⚡ Paso {i+1}/6: {step[:60]}...")
                conn.execute(text(step))
            
            trans.commit()
            print("✅ Migración de registro_financiero_apartamento completada")
            return True
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error en migración: {e}")
            return False

def migrate_usuario():
    """Migrar la tabla usuario"""
    print("\n🔄 Migrando usuario...")
    
    engine = create_engine(DATABASE_URL)
    
    migration_steps = [
        # Paso 1: Agregar nueva columna VARCHAR
        "ALTER TABLE usuario ADD COLUMN rol_new VARCHAR(20)",
        
        # Paso 2: Copiar datos convertidos
        "UPDATE usuario SET rol_new = rol::text",
        
        # Paso 3: Eliminar columna original
        "ALTER TABLE usuario DROP COLUMN rol",
        
        # Paso 4: Renombrar nueva columna
        "ALTER TABLE usuario RENAME COLUMN rol_new TO rol", 
        
        # Paso 5: Agregar constraint de validación
        "ALTER TABLE usuario ADD CONSTRAINT check_rol_usuario CHECK (rol IN ('ADMIN', 'PROPIETARIO', 'administrador', 'propietario_consulta'))",
        
        # Paso 6: Hacer NOT NULL
        "ALTER TABLE usuario ALTER COLUMN rol SET NOT NULL"
    ]
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for i, step in enumerate(migration_steps):
                print(f"  ⚡ Paso {i+1}/6: {step[:60]}...")
                conn.execute(text(step))
            
            trans.commit()
            print("✅ Migración de usuario completada")
            return True
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error en migración usuario: {e}")
            return False

def migrate_item_presupuesto():
    """Migrar la tabla item_presupuesto si existe"""
    print("\n🔄 Verificando item_presupuesto...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Verificar si la tabla existe y tiene la columna
        result = conn.execute(text("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'item_presupuesto' 
            AND column_name = 'tipo_item'
        """))
        
        row = result.fetchone()
        if not row:
            print("  ⏭️ Tabla item_presupuesto no tiene columna tipo_item, saltando...")
            return True
            
        data_type, udt_name = row[1], row[2]
        if 'enum' not in udt_name.lower():
            print(f"  ✅ item_presupuesto.tipo_item ya es {data_type}, no necesita migración")
            return True
        
        print(f"  🔄 Migrando item_presupuesto.tipo_item de {udt_name} a VARCHAR...")
        
        migration_steps = [
            "ALTER TABLE item_presupuesto ADD COLUMN tipo_item_new VARCHAR(10)",
            "UPDATE item_presupuesto SET tipo_item_new = tipo_item::text",
            "ALTER TABLE item_presupuesto DROP COLUMN tipo_item",
            "ALTER TABLE item_presupuesto RENAME COLUMN tipo_item_new TO tipo_item",
            "ALTER TABLE item_presupuesto ADD CONSTRAINT check_tipo_item_presupuesto CHECK (tipo_item IN ('INGRESO', 'GASTO'))",
            "ALTER TABLE item_presupuesto ALTER COLUMN tipo_item SET NOT NULL"
        ]
        
        trans = conn.begin()
        try:
            for i, step in enumerate(migration_steps):
                print(f"    ⚡ Paso {i+1}/6: {step[:50]}...")
                conn.execute(text(step))
            
            trans.commit()
            print("  ✅ Migración de item_presupuesto completada")
            return True
            
        except Exception as e:
            trans.rollback()
            print(f"  ❌ Error en migración item_presupuesto: {e}")
            return False

def verify_migration():
    """Verificar que la migración fue exitosa"""
    print("\n🔍 Verificando migración...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Verificar tipos de columnas
        result = conn.execute(text("""
            SELECT table_name, column_name, data_type, character_maximum_length, udt_name
            FROM information_schema.columns 
            WHERE (table_name = 'registro_financiero_apartamento' AND column_name = 'tipo_movimiento')
            OR (table_name = 'usuario' AND column_name = 'rol')
            OR (table_name = 'item_presupuesto' AND column_name = 'tipo_item')
            ORDER BY table_name, column_name
        """))
        
        print("📊 Estado después de la migración:")
        success = True
        for row in result:
            table, column, data_type, max_length, udt_name = row
            if 'enum' in udt_name.lower():
                print(f"  ❌ {table}.{column}: {data_type} ({udt_name}) - ¡Sigue siendo enum!")
                success = False
            else:
                print(f"  ✅ {table}.{column}: {data_type}({max_length})")
        
        # Verificar constraints CHECK
        result = conn.execute(text("""
            SELECT conname, conrelid::regclass, consrc
            FROM pg_constraint 
            WHERE contype = 'c' 
            AND conname LIKE 'check_%'
            AND conrelid::regclass::text IN ('registro_financiero_apartamento', 'usuario', 'item_presupuesto')
        """))
        
        constraints = result.fetchall()
        if constraints:
            print("\n✅ Constraints CHECK creados:")
            for constraint_name, table_name, constraint_def in constraints:
                print(f"  - {constraint_name} on {table_name}")
        
        return success

def test_insertion():
    """Probar que podemos insertar datos con los nuevos tipos"""
    print("\n🧪 Probando inserción de datos...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Probar inserción en registro_financiero_apartamento
            test_query = """
                INSERT INTO registro_financiero_apartamento 
                (apartamento_id, tipo_movimiento, monto, fecha_efectiva, concepto_id, fecha_registro)
                VALUES (1, 'CREDITO', 1000.00, '2025-06-09', 1, NOW())
                RETURNING id
            """
            
            result = conn.execute(text(test_query))
            test_id = result.scalar()
            
            # Limpiar el registro de prueba
            conn.execute(text(f"DELETE FROM registro_financiero_apartamento WHERE id = {test_id}"))
            conn.commit()
            
            print("✅ Test de inserción exitoso")
            return True
            
        except Exception as e:
            print(f"❌ Error en test de inserción: {e}")
            return False

def main():
    print("🚀 MIGRACIÓN DE ENUMS A VARCHAR")
    print("=" * 60)
    print("⚠️  IMPORTANTE: Esta migración modificará la estructura de la base de datos")
    print("💾 Se recomienda hacer backup antes de continuar")
    print("=" * 60)
    
    try:
        # Paso 1: Backup
        backup_data = backup_data()
        
        # Paso 2: Migrar registro_financiero_apartamento
        if not migrate_registro_financiero():
            print("❌ Falló migración de registro_financiero_apartamento")
            sys.exit(1)
        
        # Paso 3: Migrar usuario
        if not migrate_usuario():
            print("❌ Falló migración de usuario")
            sys.exit(1)
        
        # Paso 4: Migrar item_presupuesto si existe
        if not migrate_item_presupuesto():
            print("❌ Falló migración de item_presupuesto")
            sys.exit(1)
        
        # Paso 5: Verificar migración
        if not verify_migration():
            print("❌ Verificación de migración falló")
            sys.exit(1)
        
        # Paso 6: Test de inserción
        if not test_insertion():
            print("❌ Test de inserción falló")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("🎉 ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
        print("✨ Los enums han sido convertidos a VARCHAR con CHECK constraints")
        print("🔧 El error de tipo de datos debería estar resuelto")
        print("🚀 El sistema de pago automático debería funcionar ahora")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
