#!/usr/bin/env python3
"""
Test minimal del generador V3 
"""

import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import create_engine, Session, text
from datetime import date
from app.models.database import DATABASE_URL

def test_generador():
    print("🔧 Test básico del generador")
    
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        # Test 1: Verificar conexión
        result = session.exec(text("SELECT COUNT(*) as total FROM apartamento")).first()
        total_apartamentos = result.total
        print(f"✅ Apartamentos en BD: {total_apartamentos}")
        
        # Test 2: Verificar configuraciones de cuotas
        result = session.exec(text("SELECT COUNT(*) as total FROM cuota_configuracion WHERE activo = true")).first()
        total_cuotas = result.total
        print(f"✅ Configuraciones de cuotas activas: {total_cuotas}")
        
        # Test 3: Verificar tasas de interés
        result = session.exec(text("SELECT COUNT(*) as total FROM tasa_interes_mora")).first()
        total_tasas = result.total
        print(f"✅ Tasas de interés configuradas: {total_tasas}")
        
        # Test 4: Test SQL de inserción (sin ejecutar)
        sql_test = text("""
            SELECT 
                a.id as apartamento_id,
                cc.concepto_id,
                cc.monto,
                c.nombre as concepto_nombre
            FROM apartamento a
            CROSS JOIN cuota_configuracion cc
            JOIN concepto c ON cc.concepto_id = c.id
            WHERE cc.activo = true 
            AND a.activo = true
            LIMIT 5
        """)
        
        result = session.exec(sql_test).all()
        print(f"✅ Combinaciones posibles apartamento-concepto: {len(result)}")
        for r in result:
            print(f"   - Apto {r.apartamento_id}: {r.concepto_nombre} (${r.monto})")

if __name__ == "__main__":
    test_generador()
