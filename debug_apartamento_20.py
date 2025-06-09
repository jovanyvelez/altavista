#!/usr/bin/env python3
"""
Script para verificar el saldo del apartamento 20 en enero 2025
"""

import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlmodel import create_engine, Session, text
from app.models.database import DATABASE_URL

def main():
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        print("=== Análisis del Apartamento 20 ===")
        
        # Verificar saldo del apartamento 20 al final de enero 2025 (SIN INTERESES)
        sql_saldo = """
            SELECT 
                SUM(CASE 
                    WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                    ELSE -rfa.monto 
                END) as saldo_pendiente
            FROM registro_financiero_apartamento rfa
            LEFT JOIN concepto c ON rfa.concepto_id = c.id
            WHERE rfa.apartamento_id = 20
            AND rfa.fecha_efectiva <= '2025-01-31'
            AND (c.nombre IS NULL OR (
                c.nombre NOT ILIKE '%interés%' AND 
                c.nombre NOT ILIKE '%mora%' AND
                c.nombre NOT ILIKE '%intereses%'
            ))
        """
        
        result = session.exec(text(sql_saldo)).first()
        saldo = result.saldo_pendiente if result.saldo_pendiente else 0
        print(f"1. Saldo apartamento 20 al 31/01/2025 (SIN intereses): ${saldo:.2f}")
        
        # Verificar movimientos en enero 2025
        sql_movimientos = """
            SELECT 
                rfa.fecha_efectiva,
                rfa.tipo_movimiento,
                rfa.monto,
                rfa.descripcion_adicional,
                c.nombre as concepto
            FROM registro_financiero_apartamento rfa
            LEFT JOIN concepto c ON rfa.concepto_id = c.id
            WHERE rfa.apartamento_id = 20
            AND rfa.fecha_efectiva >= '2025-01-01'
            AND rfa.fecha_efectiva <= '2025-01-31'
            ORDER BY rfa.fecha_efectiva
        """
        
        movimientos = session.exec(text(sql_movimientos)).all()
        print(f"\n2. Movimientos apartamento 20 en enero 2025 ({len(movimientos)} registros):")
        for mov in movimientos:
            desc = mov.descripcion_adicional or ""
            print(f"   {mov.fecha_efectiva} | {mov.tipo_movimiento:>6} | ${mov.monto:>8.2f} | {mov.concepto[:30]:30} | {desc[:40]}")
            
        # Verificar si tiene deudas anteriores a enero 2025 (que justificarían intereses)
        sql_deudas_anteriores = """
            SELECT 
                COUNT(*) as cantidad_deudas,
                SUM(rfa.monto) as total_deudas
            FROM registro_financiero_apartamento rfa
            LEFT JOIN concepto c ON rfa.concepto_id = c.id
            WHERE rfa.apartamento_id = 20
            AND rfa.fecha_efectiva < '2025-01-01'
            AND rfa.tipo_movimiento = 'DEBITO'
            AND (c.nombre IS NULL OR (
                c.nombre NOT ILIKE '%interés%' AND 
                c.nombre NOT ILIKE '%mora%' AND
                c.nombre NOT ILIKE '%intereses%'
            ))
        """
        
        result_deudas = session.exec(text(sql_deudas_anteriores)).first()
        print(f"\n3. Deudas anteriores a enero 2025:")
        print(f"   Cantidad: {result_deudas.cantidad_deudas}")
        print(f"   Total: ${result_deudas.total_deudas:.2f}")
        
        # Verificar si cumple la condición para generar intereses según la lógica actual
        sql_verifica_condicion = """
            WITH saldos_apartamento AS (
                SELECT 
                    rfa.apartamento_id,
                    SUM(CASE 
                        WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                        ELSE -rfa.monto 
                    END) as saldo_pendiente
                FROM registro_financiero_apartamento rfa
                LEFT JOIN concepto c ON rfa.concepto_id = c.id
                WHERE rfa.apartamento_id = 20
                AND rfa.fecha_efectiva <= '2025-01-31'  -- fecha_limite para febrero
                AND (c.nombre IS NULL OR (
                    c.nombre NOT ILIKE '%interés%' AND 
                    c.nombre NOT ILIKE '%mora%' AND
                    c.nombre NOT ILIKE '%intereses%'
                ))
                GROUP BY rfa.apartamento_id
                HAVING SUM(CASE 
                    WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                    ELSE -rfa.monto 
                END) > 10.00
            ),
            apartamentos_con_mora AS (
                SELECT sa.apartamento_id, sa.saldo_pendiente
                FROM saldos_apartamento sa
                WHERE EXISTS (
                    SELECT 1 FROM registro_financiero_apartamento rfa_antigua
                    LEFT JOIN concepto c_antigua ON rfa_antigua.concepto_id = c_antigua.id
                    WHERE rfa_antigua.apartamento_id = sa.apartamento_id
                    AND rfa_antigua.tipo_movimiento = 'DEBITO'
                    -- Para febrero 2025, incluir enero y meses anteriores
                    AND rfa_antigua.fecha_efectiva < '2025-02-01'
                    AND (c_antigua.nombre IS NULL OR (
                        c_antigua.nombre NOT ILIKE '%interés%' AND 
                        c_antigua.nombre NOT ILIKE '%mora%' AND
                        c_antigua.nombre NOT ILIKE '%intereses%'
                    ))
                )
            )
            SELECT 
                CASE WHEN EXISTS (SELECT 1 FROM apartamentos_con_mora WHERE apartamento_id = 20) 
                THEN 'SÍ' ELSE 'NO' END as genera_interes,
                COALESCE((SELECT saldo_pendiente FROM saldos_apartamento WHERE apartamento_id = 20), 0) as saldo_base
        """
        
        result_condicion = session.exec(text(sql_verifica_condicion)).first()
        print(f"\n4. ¿Cumple condición para generar intereses en febrero 2025?")
        print(f"   Respuesta: {result_condicion.genera_interes}")
        print(f"   Saldo base: ${result_condicion.saldo_base:.2f}")
        
        # Verificar intereses ya generados para febrero 2025
        sql_intereses_febrero = """
            SELECT COUNT(*) as cantidad, SUM(monto) as total
            FROM registro_financiero_apartamento rfa
            LEFT JOIN concepto c ON rfa.concepto_id = c.id
            WHERE rfa.apartamento_id = 20
            AND rfa.año_aplicable = 2025
            AND rfa.mes_aplicable = 2
            AND c.nombre ILIKE '%interés%'
        """
        
        result_intereses = session.exec(text(sql_intereses_febrero)).first()
        print(f"\n5. Intereses ya generados para febrero 2025:")
        print(f"   Cantidad: {result_intereses.cantidad}")
        print(f"   Total: ${result_intereses.total:.2f if result_intereses.total else 0}")

if __name__ == "__main__":
    main()
