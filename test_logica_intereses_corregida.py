#!/usr/bin/env python3
"""
Script para probar la lógica corregida de intereses moratorios
"""

import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlmodel import create_engine, Session, select, text
from app.models.database import DATABASE_URL
from app.models import TasaInteresMora, Concepto

def test_logica_intereses(año: int, mes: int):
    """Probar la nueva lógica de intereses"""
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        print(f"=== PROBANDO LÓGICA DE INTERESES PARA {mes:02d}/{año} ===")
        
        # Obtener tasa de interés
        mes_tasa = mes - 1 if mes > 1 else 12
        año_tasa = año if mes > 1 else año - 1
        
        stmt_tasa = select(TasaInteresMora).where(
            TasaInteresMora.año == año_tasa,
            TasaInteresMora.mes == mes_tasa
        ).limit(1)
        
        tasa_record = session.exec(stmt_tasa).first()
        if not tasa_record:
            print(f"❌ No se encontró tasa de interés para {mes_tasa:02d}/{año_tasa}")
            return
        
        print(f"✅ Tasa de interés: {tasa_record.tasa_interes_mensual:.4f} para {mes_tasa:02d}/{año_tasa}")
        
        # Obtener concepto de interés
        stmt_concepto = select(Concepto).where(
            Concepto.nombre.ilike('%interés%') | Concepto.nombre.ilike('%mora%')
        ).limit(1)
        
        concepto_interes = session.exec(stmt_concepto).first()
        if not concepto_interes:
            print("❌ No se encontró concepto de interés")
            return
        
        print(f"✅ Concepto de interés: {concepto_interes.nombre} (ID: {concepto_interes.id})")
        
        # Calcular fecha límite
        if mes == 1:
            fecha_limite = f"{año-1}-12-31"
        else:
            import calendar
            ultimo_dia = calendar.monthrange(año, mes-1)[1]
            fecha_limite = f"{año}-{mes-1:02d}-{ultimo_dia}"
        
        print(f"📅 Fecha límite: {fecha_limite}")
        
        # Ejecutar la nueva lógica de intereses (solo para verificar qué apartamentos califican)
        tasa_porcentaje = float(tasa_record.tasa_interes_mensual) * 100
        
        sql_test = f"""
            WITH saldos_apartamento AS (
                SELECT 
                    rfa.apartamento_id,
                    SUM(CASE 
                        WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                        ELSE -rfa.monto 
                    END) as saldo_pendiente
                FROM registro_financiero_apartamento rfa
                LEFT JOIN concepto c ON rfa.concepto_id = c.id
                WHERE rfa.fecha_efectiva <= '{fecha_limite}'
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
            saldos_morosos AS (
                SELECT 
                    sa.apartamento_id,
                    sa.saldo_pendiente,
                    COALESCE(SUM(CASE 
                        WHEN rfa_moroso.tipo_movimiento = 'DEBITO' THEN rfa_moroso.monto 
                        ELSE -rfa_moroso.monto 
                    END), 0) as saldo_moroso_real
                FROM saldos_apartamento sa
                LEFT JOIN registro_financiero_apartamento rfa_moroso ON sa.apartamento_id = rfa_moroso.apartamento_id
                LEFT JOIN concepto c_moroso ON rfa_moroso.concepto_id = c_moroso.id
                WHERE rfa_moroso.fecha_efectiva <= '{fecha_limite}'::date - INTERVAL '30 days'
                AND (c_moroso.nombre IS NULL OR (
                    c_moroso.nombre NOT ILIKE '%interés%' AND 
                    c_moroso.nombre NOT ILIKE '%mora%' AND
                    c_moroso.nombre NOT ILIKE '%intereses%'
                ))
                GROUP BY sa.apartamento_id, sa.saldo_pendiente
            ),
            apartamentos_con_mora AS (
                SELECT 
                    sm.apartamento_id, 
                    sm.saldo_pendiente,
                    sm.saldo_moroso_real
                FROM saldos_morosos sm
                WHERE sm.saldo_moroso_real > 10.00
                AND sm.saldo_pendiente > 10.00
            )
            SELECT 
                acm.apartamento_id,
                a.identificador,
                acm.saldo_pendiente,
                acm.saldo_moroso_real,
                ROUND(LEAST(acm.saldo_pendiente, acm.saldo_moroso_real) * ({tasa_porcentaje} / 100), 2) as interes_calculado
            FROM apartamentos_con_mora acm
            JOIN apartamento a ON acm.apartamento_id = a.id
            ORDER BY acm.apartamento_id
        """
        
        results = session.exec(text(sql_test)).all()
        
        print(f"\n📊 APARTAMENTOS QUE CALIFICAN PARA INTERESES ({len(results)}):")
        print("=" * 80)
        
        if results:
            for row in results:
                print(f"Apto {row.apartamento_id:2d} ({row.identificador:6s}) | "
                      f"Saldo: ${row.saldo_pendiente:8.2f} | "
                      f"Moroso: ${row.saldo_moroso_real:8.2f} | "
                      f"Interés: ${row.interes_calculado:6.2f}")
        else:
            print("✅ Ningún apartamento califica para intereses (correcto si no hay mora)")
        
        # Verificar específicamente el apartamento 20
        print(f"\n🔍 ANÁLISIS ESPECÍFICO APARTAMENTO 20:")
        sql_apto20 = f"""
            SELECT 
                a.identificador,
                -- Saldo total al corte
                COALESCE((
                    SELECT SUM(CASE 
                        WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                        ELSE -rfa.monto 
                    END)
                    FROM registro_financiero_apartamento rfa
                    LEFT JOIN concepto c ON rfa.concepto_id = c.id
                    WHERE rfa.apartamento_id = 20
                    AND rfa.fecha_efectiva <= '{fecha_limite}'
                    AND (c.nombre IS NULL OR (
                        c.nombre NOT ILIKE '%interés%' AND 
                        c.nombre NOT ILIKE '%mora%' AND
                        c.nombre NOT ILIKE '%intereses%'
                    ))
                ), 0) as saldo_total,
                -- Saldo moroso (más de 30 días)
                COALESCE((
                    SELECT SUM(CASE 
                        WHEN rfa.tipo_movimiento = 'DEBITO' THEN rfa.monto 
                        ELSE -rfa.monto 
                    END)
                    FROM registro_financiero_apartamento rfa
                    LEFT JOIN concepto c ON rfa.concepto_id = c.id
                    WHERE rfa.apartamento_id = 20
                    AND rfa.fecha_efectiva <= '{fecha_limite}'::date - INTERVAL '30 days'
                    AND (c.nombre IS NULL OR (
                        c.nombre NOT ILIKE '%interés%' AND 
                        c.nombre NOT ILIKE '%mora%' AND
                        c.nombre NOT ILIKE '%intereses%'
                    ))
                ), 0) as saldo_moroso
            FROM apartamento a
            WHERE a.id = 20
        """
        
        result_20 = session.exec(text(sql_apto20)).first()
        
        if result_20:
            print(f"Apartamento: {result_20.identificador}")
            print(f"Saldo total al {fecha_limite}: ${result_20.saldo_total:.2f}")
            print(f"Saldo moroso (>30 días): ${result_20.saldo_moroso:.2f}")
            
            if result_20.saldo_total <= 10.00:
                print("✅ NO genera interés: Saldo total ≤ $10.00")
            elif result_20.saldo_moroso <= 10.00:
                print("✅ NO genera interés: Saldo moroso ≤ $10.00 (no hay deuda antigua)")
            else:
                interes = result_20.saldo_moroso * (tasa_porcentaje / 100)
                print(f"❌ SÍ generaría interés: ${interes:.2f}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    # Probar para febrero 2025
    test_logica_intereses(2025, 2)
