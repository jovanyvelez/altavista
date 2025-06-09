#!/usr/bin/env python3
"""
Script de depuración para investigar por qué no se generan intereses en febrero 2025
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlmodel import create_engine, Session, text
from app.models.database import DATABASE_URL

def debug_febrero_2025():
    """Investigar por qué no se generan intereses en febrero 2025"""
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        print("🔍 DEPURACIÓN FEBRERO 2025 - INTERESES NO GENERADOS")
        print("=" * 60)
        
        # 1. Verificar registros de enero 2025
        print("\n1. REGISTROS DE ENERO 2025:")
        sql_enero = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN tipo_movimiento = 'DEBITO' THEN 1 ELSE 0 END) as debitos,
                SUM(CASE WHEN tipo_movimiento = 'CREDITO' THEN 1 ELSE 0 END) as creditos,
                SUM(CASE WHEN tipo_movimiento = 'DEBITO' THEN monto ELSE 0 END) as total_debitos,
                SUM(CASE WHEN tipo_movimiento = 'CREDITO' THEN monto ELSE 0 END) as total_creditos
            FROM registro_financiero_apartamento
            WHERE año_aplicable = 2025 AND mes_aplicable = 1
        """
        
        result = session.exec(text(sql_enero)).first()
        if result:
            print(f"   Total registros: {result.total}")
            print(f"   Débitos: {result.debitos} (${result.total_debitos:,.2f})")
            print(f"   Créditos: {result.creditos} (${result.total_creditos:,.2f})")
            print(f"   Saldo neto enero: ${result.total_debitos - result.total_creditos:,.2f}")
        
        # 2. Verificar saldos al 31/01/2025 (SIN excluir intereses)
        print("\n2. SALDOS AL 31/01/2025 (TODOS LOS CONCEPTOS):")
        sql_saldos_todos = """
            SELECT 
                rfa.apartamento_id,
                SUM(CASE 
                    WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                    ELSE -rfa.monto 
                END) as saldo_pendiente
            FROM registro_financiero_apartamento rfa
            WHERE rfa.fecha_efectiva <= '2025-01-31'
            GROUP BY rfa.apartamento_id
            HAVING SUM(CASE 
                WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                ELSE -rfa.monto 
            END) > 10.00
            ORDER BY saldo_pendiente DESC
        """
        
        saldos_todos = session.exec(text(sql_saldos_todos)).all()
        print(f"   Apartamentos con saldo > $10: {len(saldos_todos)}")
        
        if saldos_todos:
            total_saldos = sum(r.saldo_pendiente for r in saldos_todos)
            print(f"   Total saldos pendientes: ${total_saldos:,.2f}")
            print("   Primeros 5 apartamentos:")
            for r in saldos_todos[:5]:
                print(f"     Apt {r.apartamento_id}: ${r.saldo_pendiente:,.2f}")
        
        # 3. Verificar saldos al 31/01/2025 (EXCLUYENDO intereses - como hace el generador)
        print("\n3. SALDOS AL 31/01/2025 (EXCLUYENDO INTERESES):")
        sql_saldos_base = """
            SELECT 
                rfa.apartamento_id,
                SUM(CASE 
                    WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                    ELSE -rfa.monto 
                END) as saldo_pendiente
            FROM registro_financiero_apartamento rfa
            LEFT JOIN concepto c ON rfa.concepto_id = c.id
            WHERE rfa.fecha_efectiva <= '2025-01-31'
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
            ORDER BY saldo_pendiente DESC
        """
        
        saldos_base = session.exec(text(sql_saldos_base)).all()
        print(f"   Apartamentos con saldo base > $10: {len(saldos_base)}")
        
        if saldos_base:
            total_saldos_base = sum(r.saldo_pendiente for r in saldos_base)
            print(f"   Total saldos BASE pendientes: ${total_saldos_base:,.2f}")
            print("   Primeros 5 apartamentos:")
            for r in saldos_base[:5]:
                print(f"     Apt {r.apartamento_id}: ${r.saldo_pendiente:,.2f}")
        
        # 4. Verificar deudas antiguas (más de 30 días antes del 31/01/2025)
        print("\n4. VERIFICAR DEUDAS ANTIGUAS (> 30 DÍAS AL 31/01/2025):")
        sql_deudas_antiguas = """
            SELECT DISTINCT rfa.apartamento_id
            FROM registro_financiero_apartamento rfa
            LEFT JOIN concepto c ON rfa.concepto_id = c.id
            WHERE rfa.tipo_movimiento = 'DEBITO'
            AND rfa.fecha_efectiva <= DATE('2025-01-31') - INTERVAL '30 days'
            AND (c.nombre IS NULL OR (
                c.nombre NOT ILIKE '%interés%' AND 
                c.nombre NOT ILIKE '%mora%' AND
                c.nombre NOT ILIKE '%intereses%'
            ))
        """
        
        deudas_antiguas = session.exec(text(sql_deudas_antiguas)).all()
        print(f"   Apartamentos con deudas > 30 días: {len(deudas_antiguas)}")
        
        if deudas_antiguas:
            print("   Apartamentos:")
            for i, r in enumerate(deudas_antiguas[:10]):
                print(f"     Apt {r.apartamento_id}")
        
        # 5. Verificar la consulta completa del generador
        print("\n5. SIMULACIÓN COMPLETA DE LA CONSULTA DEL GENERADOR:")
        sql_completa = """
            WITH saldos_apartamento AS (
                SELECT 
                    rfa.apartamento_id,
                    SUM(CASE 
                        WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                        ELSE -rfa.monto 
                    END) as saldo_pendiente
                FROM registro_financiero_apartamento rfa
                LEFT JOIN concepto c ON rfa.concepto_id = c.id
                WHERE rfa.fecha_efectiva <= '2025-01-31'
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
                    AND rfa_antigua.fecha_efectiva <= DATE('2025-01-31') - INTERVAL '30 days'
                    AND (c_antigua.nombre IS NULL OR (
                        c_antigua.nombre NOT ILIKE '%interés%' AND 
                        c_antigua.nombre NOT ILIKE '%mora%' AND
                        c_antigua.nombre NOT ILIKE '%intereses%'
                    ))
                )
            )
            SELECT 
                apartamento_id,
                saldo_pendiente
            FROM apartamentos_con_mora
            WHERE saldo_pendiente > 10.00
            ORDER BY saldo_pendiente DESC
        """
        
        candidatos = session.exec(text(sql_completa)).all()
        print(f"   Apartamentos candidatos para interés: {len(candidatos)}")
        
        if candidatos:
            total_base = sum(r.saldo_pendiente for r in candidatos)
            print(f"   Total base para intereses: ${total_base:,.2f}")
            print("   Candidatos:")
            for r in candidatos[:5]:
                print(f"     Apt {r.apartamento_id}: ${r.saldo_pendiente:,.2f}")
        
        # 6. Verificar tasa de interés
        print("\n6. VERIFICAR TASA DE INTERÉS:")
        sql_tasa = """
            SELECT * FROM tasa_interes_mora
            WHERE año = 2025 AND mes = 1
        """
        
        tasa = session.exec(text(sql_tasa)).first()
        if tasa:
            print(f"   Tasa enero 2025: {tasa.tasa_interes_mensual} ({tasa.tasa_interes_mensual * 100}%)")
        else:
            print("   ❌ NO HAY TASA DE INTERÉS PARA ENERO 2025")
        
        # 7. Verificar concepto de interés
        print("\n7. VERIFICAR CONCEPTO DE INTERÉS:")
        sql_concepto = """
            SELECT id, nombre FROM concepto
            WHERE nombre ILIKE '%interés%' OR nombre ILIKE '%mora%'
        """
        
        conceptos = session.exec(text(sql_concepto)).all()
        print(f"   Conceptos de interés encontrados: {len(conceptos)}")
        for c in conceptos:
            print(f"     ID {c.id}: {c.nombre}")
        
        # 8. Verificar duplicados existentes
        print("\n8. VERIFICAR INTERESES YA EXISTENTES PARA FEBRERO 2025:")
        if conceptos:
            for concepto in conceptos:
                sql_existentes = f"""
                    SELECT COUNT(*) as total
                    FROM registro_financiero_apartamento
                    WHERE concepto_id = {concepto.id}
                    AND año_aplicable = 2025
                    AND mes_aplicable = 2
                    AND descripcion_adicional LIKE 'Interés moratorio automático%'
                """
                
                existentes = session.exec(text(sql_existentes)).first()
                print(f"   Concepto {concepto.nombre}: {existentes.total} intereses ya generados")

if __name__ == "__main__":
    debug_febrero_2025()
