#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import create_engine, Session, select
from app.models.database import DATABASE_URL
from app.models.apartamento import Apartamento
from app.models.registro_financiero_apartamento import RegistroFinancieroApartamento

engine = create_engine(DATABASE_URL)
with Session(engine) as session:
    apartamento = session.exec(select(Apartamento).where(Apartamento.identificador == '9901')).first()
    registros = session.exec(select(RegistroFinancieroApartamento).where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)).all()
    print(f'Total registros: {len(registros)}')
    
    cuotas = [r for r in registros if 'Cuota ordinaria' in r.descripcion]
    intereses = [r for r in registros if 'Interés moratorio' in r.descripcion]
    
    total_cuotas = sum(r.monto for r in cuotas)
    total_intereses = sum(r.monto for r in intereses)
    
    print(f'Cuotas: {len(cuotas)} = ${total_cuotas:,.2f}')
    print(f'Intereses: {len(intereses)} = ${total_intereses:,.2f}')
    print(f'Total deuda: ${total_cuotas + total_intereses:,.2f}')
