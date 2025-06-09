#!/usr/bin/env python3
"""
Test para verificar la nueva lógica de intereses:
- Cualquier saldo pendiente al final del mes anterior genera interés
- El propietario tiene todo el mes para pagar sin generar interés
- Una vez finalizado el mes, cualquier saldo genera interés moratorio
"""

import sys
import os
from pathlib import Path
from datetime import date, datetime

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlmodel import create_engine, Session, select, text
from app.models.database import DATABASE_URL
from app.models import Concepto, TasaInteresMora

def test_nueva_logica_intereses():
    """Test de la nueva lógica de intereses"""
    
    print("="*80)
    print("PRUEBA: NUEVA LÓGICA DE INTERESES")
    print("="*80)
    
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        
        # 1. Verificar tasa de interés disponible
        stmt_tasa = select(TasaInteresMora).where(
            TasaInteresMora.año == 2025,
            TasaInteresMora.mes == 1  # Enero 2025
        ).limit(1)
        
        tasa_record = session.exec(stmt_tasa).first()
        if tasa_record:
            print(f"✅ Tasa de interés: {tasa_record.tasa_interes_mensual} para 01/2025")
        else:
            print("❌ No se encontró tasa de interés para 01/2025")
            return
        
        # 2. Verificar concepto de interés
        stmt_concepto = select(Concepto).where(
            Concepto.nombre.ilike('%interés%') | Concepto.nombre.ilike('%mora%')
        ).limit(1)
        
        concepto_interes = session.exec(stmt_concepto).first()
        if concepto_interes:
            print(f"✅ Concepto de interés: {concepto_interes.nombre} (ID: {concepto_interes.id})")
        else:
            print("❌ No se encontró concepto de interés")
            return
        
        # 3. Simular la nueva lógica para febrero 2025
        print(f"\n📅 Fecha límite: 2025-01-31")
        
        # Query para simular los apartamentos que calificarían para intereses
        sql_simulacion = """
            WITH saldos_apartamento AS (
                SELECT 
                    rfa.apartamento_id,
                    a.identificador as apartamento_nombre,
                    SUM(CASE 
                        WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                        ELSE -rfa.monto 
                    END) as saldo_pendiente
                FROM registro_financiero_apartamento rfa
                LEFT JOIN concepto c ON rfa.concepto_id = c.id
                LEFT JOIN apartamento a ON rfa.apartamento_id = a.id
                WHERE rfa.fecha_efectiva <= '2025-01-31'
                -- Excluir conceptos de interés del cálculo base
                AND (c.nombre IS NULL OR (
                    c.nombre NOT ILIKE '%interés%' AND 
                    c.nombre NOT ILIKE '%mora%' AND
                    c.nombre NOT ILIKE '%intereses%'
                ))
                GROUP BY rfa.apartamento_id, a.identificador
                HAVING SUM(CASE 
                    WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                    ELSE -rfa.monto 
                END) > 0.01  -- Solo saldos positivos (deudas)
            )
            SELECT 
                apartamento_id,
                apartamento_nombre,
                saldo_pendiente,
                ROUND(saldo_pendiente * 0.0129, 2) as interes_calculado
            FROM saldos_apartamento
            ORDER BY apartamento_id
        """
        
        print(f"\n📊 APARTAMENTOS QUE CALIFICAN PARA INTERESES:")
        print("="*80)
        
        result = session.exec(text(sql_simulacion))
        apartamentos = result.fetchall()
        
        total_saldo = 0
        total_interes = 0
        
        for apto in apartamentos:
            print(f"Apartamento: {apto.apartamento_nombre}")
            print(f"Saldo pendiente al 31/01/2025: ${apto.saldo_pendiente:,.2f}")
            print(f"Interés calculado (1.29%): ${apto.interes_calculado:,.2f}")
            print(f"✅ GENERA interés: Saldo > $0.01")
            print("-" * 50)
            
            total_saldo += apto.saldo_pendiente
            total_interes += apto.interes_calculado
        
        if not apartamentos:
            print("✅ Ningún apartamento califica para intereses (todos están al día)")
        else:
            print(f"\n📈 RESUMEN:")
            print(f"Total apartamentos con saldo: {len(apartamentos)}")
            print(f"Total saldo pendiente: ${total_saldo:,.2f}")
            print(f"Total intereses a generar: ${total_interes:,.2f}")
        
        # 4. Análisis específico apartamento 20 (si existe)
        sql_apto_20 = """
            SELECT 
                rfa.apartamento_id,
                a.identificador as apartamento_nombre,
                SUM(CASE 
                    WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                    ELSE -rfa.monto 
                END) as saldo_pendiente
            FROM registro_financiero_apartamento rfa
            LEFT JOIN concepto c ON rfa.concepto_id = c.id
            LEFT JOIN apartamento a ON rfa.apartamento_id = a.id
            WHERE rfa.fecha_efectiva <= '2025-01-31'
            AND rfa.apartamento_id = 20
            AND (c.nombre IS NULL OR (
                c.nombre NOT ILIKE '%interés%' AND 
                c.nombre NOT ILIKE '%mora%' AND
                c.nombre NOT ILIKE '%intereses%'
            ))
            GROUP BY rfa.apartamento_id, a.identificador
        """
        
        print(f"\n🔍 ANÁLISIS ESPECÍFICO APARTAMENTO 20:")
        
        result_20 = session.exec(text(sql_apto_20)).first()
        if result_20:
            interes_20 = result_20.saldo_pendiente * 0.0129 if result_20.saldo_pendiente > 0 else 0
            
            print(f"Apartamento: {result_20.apartamento_nombre}")
            print(f"Saldo total al 2025-01-31: ${result_20.saldo_pendiente:,.2f}")
            
            if result_20.saldo_pendiente > 0.01:
                print(f"Interés a generar: ${interes_20:,.2f}")
                print(f"✅ GENERA interés: Saldo pendiente > $0.01")
            else:
                print(f"✅ NO genera interés: Saldo ≤ $0.01")
        else:
            print("Apartamento 20 no encontrado o sin movimientos")
        
        print("="*80)

if __name__ == "__main__":
    test_nueva_logica_intereses()
