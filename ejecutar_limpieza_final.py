#!/usr/bin/env python3
"""
Script para ejecutar la limpieza final de enums directamente desde Python
"""

from app.models import db_manager
from sqlmodel import text

def ejecutar_limpieza_final():
    """Ejecuta la limpieza final de enums"""
    session = db_manager.get_session()
    
    try:
        print("🧹 INICIANDO LIMPIEZA FINAL DE ENUMS...")
        
        # 1. Verificar restricciones que usen enums viejos
        print("\n🔍 Verificando restricciones...")
        result = session.execute(text("""
            SELECT 
                conname as constraint_name,
                conrelid::regclass as table_name,
                pg_get_constraintdef(oid) as constraint_definition
            FROM pg_constraint 
            WHERE pg_get_constraintdef(oid) LIKE '%tipomovimientoenum%'
               OR pg_get_constraintdef(oid) LIKE '%CARGO%'
               OR pg_get_constraintdef(oid) LIKE '%ABONO%';
        """))
        
        constraints = result.fetchall()
        for constraint_name, table_name, definition in constraints:
            print(f"   ❌ Restricción problemática: {table_name}.{constraint_name}")
            print(f"      Definición: {definition}")
            
            # Eliminar la restricción
            session.execute(text(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}"))
            print(f"   ✅ Eliminada restricción {constraint_name}")
        
        # 2. Asegurar que tipo_movimiento tenga restricción correcta
        print("\n🔧 Configurando restricciones correctas...")
        session.execute(text("""
            ALTER TABLE registro_financiero_apartamento 
                DROP CONSTRAINT IF EXISTS registro_financiero_apartamento_tipo_movimiento_check
        """))
        
        session.execute(text("""
            ALTER TABLE registro_financiero_apartamento 
                ADD CONSTRAINT registro_financiero_apartamento_tipo_movimiento_check 
                CHECK (tipo_movimiento IN ('DEBITO', 'CREDITO'))
        """))
        print("   ✅ Restricción de tipo_movimiento configurada")
        
        # 3. Actualizar datos existentes si es necesario
        print("\n📝 Actualizando datos existentes...")
        result = session.execute(text("""
            UPDATE registro_financiero_apartamento 
            SET tipo_movimiento = 'DEBITO' 
            WHERE tipo_movimiento IN ('CARGO', 'DEBIT')
        """))
        print(f"   📊 Actualizados {result.rowcount} registros a DEBITO")
        
        result = session.execute(text("""
            UPDATE registro_financiero_apartamento 
            SET tipo_movimiento = 'CREDITO' 
            WHERE tipo_movimiento IN ('ABONO', 'CREDIT')
        """))
        print(f"   📊 Actualizados {result.rowcount} registros a CREDITO")
        
        # 4. Eliminar enums no utilizados
        print("\n🗑️ Eliminando enums obsoletos...")
        try:
            session.execute(text("DROP TYPE IF EXISTS tipomovimientoenum CASCADE"))
            print("   ✅ Eliminado tipomovimientoenum")
        except Exception as e:
            print(f"   ⚠️ No se pudo eliminar tipomovimientoenum: {e}")
        
        try:
            session.execute(text("DROP TYPE IF EXISTS rolusuarioenum CASCADE"))
            print("   ✅ Eliminado rolusuarioenum")
        except Exception as e:
            print(f"   ⚠️ No se pudo eliminar rolusuarioenum: {e}")
            
        try:
            session.execute(text("DROP TYPE IF EXISTS tipoitempresupuestoenum CASCADE"))
            print("   ✅ Eliminado tipoitempresupuestoenum")
        except Exception as e:
            print(f"   ⚠️ No se pudo eliminar tipoitempresupuestoenum: {e}")
        
        # 5. Commit de todos los cambios
        session.commit()
        print("\n✅ LIMPIEZA COMPLETADA EXITOSAMENTE")
        
        # 6. Verificar resultado final
        print("\n🔍 VERIFICACIÓN FINAL:")
        result = session.execute(text("""
            SELECT 
                table_name,
                column_name,
                data_type,
                udt_name
            FROM information_schema.columns 
            WHERE table_name IN ('registro_financiero_apartamento', 'usuario', 'item_presupuesto')
              AND column_name IN ('tipo_movimiento', 'rol', 'tipo_item')
            ORDER BY table_name, column_name;
        """))
        
        columns = result.fetchall()
        for table, column, data_type, udt_name in columns:
            print(f"   📋 {table}.{column} -> {data_type} ({udt_name})")
        
        # Verificar enums restantes
        result = session.execute(text("""
            SELECT 
                t.typname as enum_name,
                array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid 
            WHERE t.typtype = 'e' 
              AND t.typname LIKE '%movimiento%'
            GROUP BY t.typname
            ORDER BY t.typname;
        """))
        
        remaining_enums = result.fetchall()
        if remaining_enums:
            print("\n📋 ENUMS DE MOVIMIENTO RESTANTES:")
            for enum_name, enum_values in remaining_enums:
                print(f"   - {enum_name}: {enum_values}")
        else:
            print("\n✅ No quedan enums de movimiento problemáticos")
            
    except Exception as e:
        print(f"\n❌ ERROR DURANTE LA LIMPIEZA: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    ejecutar_limpieza_final()
