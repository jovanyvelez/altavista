#!/usr/bin/env python3
"""Script temporal para verificar los intereses creados"""

import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models.database import DATABASE_URL
from sqlmodel import create_engine, Session, select, text
from app.models import RegistroFinancieroApartamento

def verificar_intereses():
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        sql = '''
            SELECT 
                mes_aplicable, año_aplicable, monto, descripcion_adicional, fecha_efectiva
            FROM registro_financiero_apartamento 
            WHERE apartamento_id = 3 AND concepto_id = 3
            AND año_aplicable = 2024 AND mes_aplicable IN (6, 7, 8)
            ORDER BY año_aplicable, mes_aplicable
        '''
        resultados = session.exec(text(sql)).all()
        
        print('📊 INTERESES GENERADOS PARA APARTAMENTO 3 (9901):')
        print('=' * 70)
        for r in resultados:
            print(f'{r.mes_aplicable:02d}/{r.año_aplicable}: ${r.monto:,.2f}')
            print(f'   Descripción: {r.descripcion_adicional}')
            print(f'   Fecha efectiva: {r.fecha_efectiva}')
            print()

if __name__ == "__main__":
    verificar_intereses()
