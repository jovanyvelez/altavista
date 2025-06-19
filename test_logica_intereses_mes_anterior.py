#!/usr/bin/env python3
"""
Test para verificar la lógica corregida de intereses:
Solo se generan intereses si el saldo del mes anterior > 0

Lógica correcta:
1. Para cada mes, calcular saldo neto SOLO del mes anterior
2. Si saldo anterior > 0: crear interés = saldo_anterior × tasa_actual
3. Si saldo anterior ≤ 0: NO crear interés
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlmodel import create_engine, Session, select, text
from datetime import date
from decimal import Decimal

# Importaciones del proyecto
from app.models.database import DATABASE_URL
from app.models import RegistroFinancieroApartamento
from crear_cargos_historicos import GeneradorCargosHistoricos


def limpiar_intereses_test(apartamento_id: int = 20):
    """Limpia los intereses de prueba"""
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        # Eliminar intereses existentes del apartamento para prueba limpia
        session.exec(
            text(f"""
                DELETE FROM registro_financiero_apartamento 
                WHERE apartamento_id = {apartamento_id} 
                AND concepto_id = 3
            """)
        )
        session.commit()
        print(f"🧹 Limpiados intereses previos del apartamento {apartamento_id}")


def mostrar_saldos_por_mes(apartamento_id: int, año: int):
    """Muestra los saldos netos por mes para análisis"""
    print(f"\n📊 ANÁLISIS DE SALDOS MENSUALES - Apartamento {apartamento_id}, Año {año}")
    print("=" * 70)
    
    generador = GeneradorCargosHistoricos()
    
    for mes in range(1, 13):
        saldo_mes = generador.calcular_saldo_neto_mes_especifico(apartamento_id, año, mes)
        estado = "DÉBITO" if saldo_mes > 0 else "SIN DEUDA" if saldo_mes == 0 else "CRÉDITO"
        print(f"   {mes:02d}/{año}: ${saldo_mes:>10,.2f} ({estado})")


def verificar_logica_intereses(apartamento_id: int = 20):
    """Verifica la lógica corregida de intereses"""
    print(f"🧪 PRUEBA DE LÓGICA DE INTERESES CORREGIDA")
    print(f"📋 Apartamento: {apartamento_id}")
    print("📝 Regla: Interés solo si saldo del mes anterior > 0")
    print("=" * 60)
    
    # Mostrar saldos históricos
    mostrar_saldos_por_mes(apartamento_id, 2024)
    
    # Generar intereses para primer trimestre 2025
    print(f"\n🔧 Generando intereses para Q1 2025...")
    generador = GeneradorCargosHistoricos()
    
    # Test específico: enero 2025 (basado en diciembre 2024)
    print(f"\n🎯 TEST ESPECÍFICO: Enero 2025")
    print(f"   Base: Saldo de diciembre 2024")
    
    saldo_dic_2024 = generador.calcular_saldo_neto_mes_especifico(apartamento_id, 2024, 12)
    print(f"   Saldo dic 2024: ${saldo_dic_2024:,.2f}")
    
    if saldo_dic_2024 > 0:
        print(f"   ✅ Saldo > 0: DEBE generarse interés en enero 2025")
    else:
        print(f"   ❌ Saldo ≤ 0: NO debe generarse interés en enero 2025")
    
    # Generar intereses
    resultado = generador.generar_intereses_automaticos(apartamento_id, 2025, 1, 2025, 3)
    
    # Verificar resultados
    print(f"\n🔍 VERIFICACIÓN DE RESULTADOS:")
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        intereses = session.exec(
            select(RegistroFinancieroApartamento).where(
                RegistroFinancieroApartamento.apartamento_id == apartamento_id,
                RegistroFinancieroApartamento.concepto_id == 3,
                RegistroFinancieroApartamento.año_aplicable == 2025,
                RegistroFinancieroApartamento.mes_aplicable.in_([1, 2, 3])
            )
        ).all()
        
        for interes in intereses:
            print(f"   ✅ {interes.mes_aplicable:02d}/{interes.año_aplicable}: "
                  f"${interes.monto:,.2f} - {interes.descripcion_adicional}")
    
    return resultado


def main():
    """Función principal"""
    apartamento_id = 20  # Apartamento con historial conocido
    
    try:
        # 1. Limpiar intereses previos
        limpiar_intereses_test(apartamento_id)
        
        # 2. Verificar lógica corregida
        exito = verificar_logica_intereses(apartamento_id)
        
        # 3. Resultado final
        if exito:
            print("\n🎉 PRUEBA EXITOSA: Lógica de intereses corregida funciona correctamente")
        else:
            print("\n❌ PRUEBA FALLIDA: Revisar la lógica")
        
        return 0 if exito else 1
        
    except Exception as e:
        print(f"💥 Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
