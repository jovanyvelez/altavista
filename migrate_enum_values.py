#!/usr/bin/env python3
"""
Migration script to update enum values in the database.
This script updates old enum values to new ones:
- administrador -> ADMIN
- propietario_consulta -> PROPIETARIO
- CARGO -> DEBITO
- ABONO -> CREDITO
"""

import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
DATABASE_URL = "postgresql://postgres:NqYMCFXBEQYYJ60u@db.xnmealeoourdfcgsyfqv.supabase.co:5432/postgres"

def migrate_enum_values():
    """Update enum values in the database"""
    print("Starting enum values migration...")
    
    engine = create_engine(DATABASE_URL)
    
    # First, add new enum values (requires separate transaction)
    with engine.connect() as conn:
        print("Checking current database values...")
        
        # Check what enum values exist
        result = conn.execute(text("SELECT DISTINCT rol FROM usuario"))
        existing_roles = [row[0] for row in result]
        print(f"Existing roles: {existing_roles}")
        
        # Add new enum values if needed
        if 'ADMIN' not in existing_roles or 'PROPIETARIO' not in existing_roles:
            print("Adding new enum values to PostgreSQL enum type...")
            
            # Add ADMIN if it doesn't exist
            try:
                conn.execute(text("ALTER TYPE rol_usuario_enum ADD VALUE 'ADMIN'"))
                conn.commit()
                print("Added ADMIN enum value")
            except Exception as e:
                print(f"ADMIN enum value might already exist: {e}")
            
            # Add PROPIETARIO if it doesn't exist
            try:
                conn.execute(text("ALTER TYPE rol_usuario_enum ADD VALUE 'PROPIETARIO'"))
                conn.commit()
                print("Added PROPIETARIO enum value")
            except Exception as e:
                print(f"PROPIETARIO enum value might already exist: {e}")
        
        # Add movement type enum values if needed
        try:
            result = conn.execute(text("SELECT DISTINCT tipo_movimiento FROM registro_financiero_apartamento LIMIT 1"))
            # Table exists, check for enum values
            for new_value in ['DEBITO', 'CREDITO']:
                try:
                    conn.execute(text(f"ALTER TYPE tipo_movimiento_enum ADD VALUE '{new_value}'"))
                    conn.commit()
                    print(f"Added {new_value} enum value")
                except Exception as e:
                    print(f"{new_value} enum value might already exist: {e}")
        except Exception as e:
            print(f"Movement types table might be empty or not exist: {e}")
    
    # Now update the data (new transaction)
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            print("Updating user roles...")
            
            # Update old values to new ones
            for old_value, new_value in [('administrador', 'ADMIN'), ('propietario_consulta', 'PROPIETARIO')]:
                result1 = conn.execute(
                    text(f"UPDATE usuario SET rol = :new_value WHERE rol = :old_value"),
                    {"new_value": new_value, "old_value": old_value}
                )
                print(f"Updated {result1.rowcount} {old_value} roles to {new_value}")
            
            # Update movement types if they exist
            try:
                result = conn.execute(text("SELECT DISTINCT tipo_movimiento FROM registro_financiero_apartamento"))
                existing_movements = [row[0] for row in result]
                print(f"Existing movement types: {existing_movements}")
                
                # Update old values to new ones
                for old_value, new_value in [('CARGO', 'DEBITO'), ('ABONO', 'CREDITO')]:
                    if old_value in existing_movements:
                        result3 = conn.execute(
                            text(f"UPDATE registro_financiero_apartamento SET tipo_movimiento = :new_value WHERE tipo_movimiento = :old_value"),
                            {"new_value": new_value, "old_value": old_value}
                        )
                        print(f"Updated {result3.rowcount} {old_value} movement types to {new_value}")
                        
            except Exception as e:
                print(f"Movement types table might be empty or not exist: {e}")
            
            # Commit transaction
            trans.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"Migration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    migrate_enum_values()
