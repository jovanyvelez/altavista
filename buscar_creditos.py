#!/usr/bin/env python3
"""Script temporal para buscar apartamentos con créditos"""

import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models.database import DATABASE_URL
from sqlmodel import create_engine, Session, text

def buscar_apartamentos_con_creditos():
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        # Buscar apartamentos con créditos para hacer una prueba más completa
        sql = '''
            SELECT 
                apartamento_id,
                COUNT(CASE WHEN tipo_movimiento = 'DEBITO' THEN 1 END) as debitos,
                COUNT(CASE WHEN tipo_movimiento = 'CREDITO' THEN 1 END) as creditos,
                SUM(CASE WHEN tipo_movimiento = 'DEBITO' THEN monto ELSE -monto END) as saldo_neto
            FROM registro_financiero_apartamento
            WHERE concepto_id != 3  -- Excluir intereses
            GROUP BY apartamento_id
            HAVING COUNT(CASE WHEN tipo_movimiento = 'CREDITO' THEN 1 END) > 0
            ORDER BY saldo_neto DESC
            LIMIT 5
        '''
        
        resultados = session.exec(text(sql)).all()
        
        print('🔍 APARTAMENTOS CON DÉBITOS Y CRÉDITOS:')
        print('Apt | Débitos | Créditos | Saldo Neto')
        print('-' * 40)
        for r in resultados:
            print(f'{r.apartamento_id:3d} | {r.debitos:7d} | {r.creditos:8d} | ${r.saldo_neto:>10,.2f}')

if __name__ == "__main__":
    buscar_apartamentos_con_creditos()
