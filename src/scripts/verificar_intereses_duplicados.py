#!/usr/bin/env python3
"""
Script de Verificación de Intereses Duplicados
==============================================

Este script verifica si hay registros de intereses calculados incorrectamente
(interés sobre interés) y proporciona estadísticas detalladas.

Uso:
    python scripts/verificar_intereses_duplicados.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import create_engine, Session, text
from decimal import Decimal
from src.models.database import DATABASE_URL


def verificar_intereses_duplicados():
    """Verifica y reporta problemas con intereses calculados incorrectamente"""
    
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        print("🔍 Verificando Registros de Intereses...")
        print("=" * 50)
        
        # 1. Resumen general de intereses
        sql_resumen = """
            SELECT 
                COUNT(*) as total_registros_interes,
                SUM(rfa.monto) as monto_total_intereses,
                MIN(rfa.fecha_efectiva) as primer_interes,
                MAX(rfa.fecha_efectiva) as ultimo_interes
            FROM registro_financiero_apartamento rfa
            JOIN concepto c ON rfa.concepto_id = c.id
            WHERE c.nombre ILIKE '%interés%' OR c.nombre ILIKE '%mora%'
        """
        
        resultado_resumen = session.exec(text(sql_resumen)).first()
        if resultado_resumen:
            print(f"📊 RESUMEN GENERAL:")
            print(f"   Total registros de interés: {resultado_resumen.total_registros_interes}")
            print(f"   Monto total intereses: ${resultado_resumen.monto_total_intereses:,.2f}")
            print(f"   Período: {resultado_resumen.primer_interes} a {resultado_resumen.ultimo_interes}")
            print()
        
        # 2. Intereses por apartamento
        sql_por_apartamento = """
            SELECT 
                a.identificador,
                COUNT(*) as total_intereses,
                SUM(rfa.monto) as total_monto_intereses,
                AVG(rfa.monto) as promedio_interes,
                MAX(rfa.fecha_efectiva) as ultimo_interes
            FROM registro_financiero_apartamento rfa
            JOIN apartamento a ON rfa.apartamento_id = a.id
            JOIN concepto c ON rfa.concepto_id = c.id
            WHERE c.nombre ILIKE '%interés%' OR c.nombre ILIKE '%mora%'
            GROUP BY a.identificador
            ORDER BY total_monto_intereses DESC
            LIMIT 10
        """
        
        print("🏠 TOP 10 APARTAMENTOS CON MÁS INTERESES:")
        resultados_apt = session.exec(text(sql_por_apartamento)).all()
        for apt in resultados_apt:
            print(f"   {apt.identificador}: {apt.total_intereses} registros, ${apt.total_monto_intereses:,.2f} total")
        print()
        
        # 3. Verificar posibles intereses excesivos (indicativo de interés sobre interés)
        sql_intereses_altos = """
            SELECT 
                a.identificador,
                rfa.fecha_efectiva,
                rfa.monto as monto_interes,
                rfa.descripcion_adicional,
                rfa.año_aplicable,
                rfa.mes_aplicable
            FROM registro_financiero_apartamento rfa
            JOIN apartamento a ON rfa.apartamento_id = a.id
            JOIN concepto c ON rfa.concepto_id = c.id
            WHERE (c.nombre ILIKE '%interés%' OR c.nombre ILIKE '%mora%')
            AND rfa.monto > 100000  -- Intereses muy altos (> $100,000)
            ORDER BY rfa.monto DESC
            LIMIT 20
        """
        
        print("⚠️  INTERESES POTENCIALMENTE PROBLEMÁTICOS (> $100,000):")
        intereses_altos = session.exec(text(sql_intereses_altos)).all()
        if intereses_altos:
            for interes in intereses_altos:
                print(f"   {interes.identificador} - {interes.mes_aplicable:02d}/{interes.año_aplicable}: ${interes.monto_interes:,.2f}")
                if interes.descripcion_adicional:
                    print(f"      → {interes.descripcion_adicional}")
        else:
            print("   ✅ No se encontraron intereses excesivamente altos")
        print()
        
        # 4. Verificar saldos actuales sin incluir intereses
        sql_saldos_sin_intereses = """
            SELECT 
                a.identificador,
                SUM(CASE 
                    WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                    ELSE -rfa.monto 
                END) as saldo_sin_intereses,
                COUNT(CASE WHEN rfa.tipo_movimiento = 'DEBITO' THEN 1 END) as total_debitos,
                COUNT(CASE WHEN rfa.tipo_movimiento = 'CREDITO' THEN 1 END) as total_creditos
            FROM registro_financiero_apartamento rfa
            JOIN apartamento a ON rfa.apartamento_id = a.id
            LEFT JOIN concepto c ON rfa.concepto_id = c.id
            WHERE (c.nombre IS NULL OR (
                c.nombre NOT ILIKE '%interés%' AND 
                c.nombre NOT ILIKE '%mora%'
            ))
            GROUP BY a.identificador
            HAVING SUM(CASE 
                WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                ELSE -rfa.monto 
            END) > 0
            ORDER BY saldo_sin_intereses DESC
            LIMIT 10
        """
        
        print("💰 SALDOS PENDIENTES (SIN INCLUIR INTERESES):")
        saldos_pendientes = session.exec(text(sql_saldos_sin_intereses)).all()
        for saldo in saldos_pendientes:
            print(f"   {saldo.identificador}: ${saldo.saldo_sin_intereses:,.2f} "
                  f"({saldo.total_debitos} débitos, {saldo.total_creditos} créditos)")
        print()
        
        # 5. Comparar saldos con y sin intereses
        sql_comparacion = """
            WITH saldos_con_intereses AS (
                SELECT 
                    apartamento_id,
                    SUM(CASE WHEN tipo_movimiento = 'DEBITO' THEN monto ELSE -monto END) as saldo_total
                FROM registro_financiero_apartamento
                GROUP BY apartamento_id
            ),
            saldos_sin_intereses AS (
                SELECT 
                    rfa.apartamento_id,
                    SUM(CASE WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto ELSE -rfa.monto END) as saldo_base
                FROM registro_financiero_apartamento rfa
                LEFT JOIN concepto c ON rfa.concepto_id = c.id
                WHERE (c.nombre IS NULL OR (
                    c.nombre NOT ILIKE '%interés%' AND 
                    c.nombre NOT ILIKE '%mora%'
                ))
                GROUP BY rfa.apartamento_id
            )
            SELECT 
                a.identificador,
                COALESCE(sci.saldo_total, 0) as saldo_con_intereses,
                COALESCE(ssi.saldo_base, 0) as saldo_sin_intereses,
                COALESCE(sci.saldo_total, 0) - COALESCE(ssi.saldo_base, 0) as diferencia_intereses
            FROM apartamento a
            LEFT JOIN saldos_con_intereses sci ON a.id = sci.apartamento_id
            LEFT JOIN saldos_sin_intereses ssi ON a.id = ssi.apartamento_id
            WHERE COALESCE(sci.saldo_total, 0) > 0 OR COALESCE(ssi.saldo_base, 0) > 0
            ORDER BY diferencia_intereses DESC
            LIMIT 10
        """
        
        print("📈 COMPARACIÓN SALDOS (CON vs SIN INTERESES):")
        comparaciones = session.exec(text(sql_comparacion)).all()
        for comp in comparaciones:
            print(f"   {comp.identificador}:")
            print(f"      Con intereses: ${comp.saldo_con_intereses:,.2f}")
            print(f"      Sin intereses: ${comp.saldo_sin_intereses:,.2f}")
            print(f"      Diferencia:    ${comp.diferencia_intereses:,.2f}")
        print()
        
        # 6. Estadísticas de procesamiento mensual
        sql_procesamiento = """
            SELECT 
                año_aplicable,
                mes_aplicable,
                COUNT(*) as registros_interes,
                SUM(monto) as total_intereses_mes
            FROM registro_financiero_apartamento rfa
            JOIN concepto c ON rfa.concepto_id = c.id
            WHERE c.nombre ILIKE '%interés%' OR c.nombre ILIKE '%mora%'
            GROUP BY año_aplicable, mes_aplicable
            ORDER BY año_aplicable DESC, mes_aplicable DESC
            LIMIT 12
        """
        
        print("📅 INTERESES POR MES (ÚLTIMOS 12 MESES):")
        proc_mensual = session.exec(text(sql_procesamiento)).all()
        for proc in proc_mensual:
            print(f"   {proc.mes_aplicable:02d}/{proc.año_aplicable}: {proc.registros_interes} registros, ${proc.total_intereses_mes:,.2f}")

    print("\n✅ Verificación completada.")
    print("\n💡 RECOMENDACIONES:")
    print("   - Si hay intereses > $100,000, revisar cálculos")
    print("   - Verificar que los saldos base sean consistentes")
    print("   - Considerar limpiar intereses incorrectos si es necesario")


if __name__ == "__main__":
    verificar_intereses_duplicados()
