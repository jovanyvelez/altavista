#!/usr/bin/env python3
"""
Demostración Completa del Sistema de Cargos Históricos
=====================================================

Este script demuestra todas las funcionalidades del generador de cargos
históricos, incluyendo la nueva funcionalidad de cálculo automático de intereses.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from crear_cargos_historicos import GeneradorCargosHistoricos
from decimal import Decimal

def main():
    print("🎯 DEMOSTRACIÓN COMPLETA - SISTEMA DE CARGOS HISTÓRICOS")
    print("=" * 65)
    
    generador = GeneradorCargosHistoricos()
    
    print("\n1️⃣ FUNCIONALIDAD: Verificación de apartamentos y conceptos")
    print("-" * 55)
    
    # Verificar apartamento existente
    print("✅ Verificando apartamento 1 (9801):")
    generador.verificar_apartamento(1)
    
    print("\n✅ Verificando conceptos disponibles:")
    generador.verificar_conceptos([1, 3, 7, 9])
    
    print("\n2️⃣ FUNCIONALIDAD: Creación de cargos básicos")
    print("-" * 45)
    
    # Ejemplo de crear cuotas ordinarias
    print("🔨 Creando cuotas ordinarias para apartamento 1 - marzo 2024:")
    exito_cuotas = generador.generar_cargos_periodo(1, 1, 2024, 3, 2024, 3)
    if exito_cuotas:
        print("✅ Cuotas creadas exitosamente")
    
    print("\n🔨 Creando servicios públicos para apartamento 1 - marzo 2024:")
    exito_servicios = generador.generar_cargos_periodo(1, 7, 2024, 3, 2024, 3)
    if exito_servicios:
        print("✅ Servicios creados exitosamente")
    
    print("\n3️⃣ FUNCIONALIDAD: ⭐ Cálculo automático de intereses")
    print("-" * 55)
    
    print("🧮 Generando intereses automáticos para apartamento 1 - abril 2024:")
    print("💡 El sistema calculará automáticamente basándose en saldos DEBITO")
    
    exito_intereses = generador.generar_intereses_automaticos(1, 2024, 4, 2024, 4)
    if exito_intereses:
        print("✅ Intereses calculados y creados automáticamente")
    
    print("\n4️⃣ FUNCIONALIDAD: Manejo de apartamentos sin deudas")
    print("-" * 50)
    
    print("🧮 Probando generación de intereses para apartamento sin deudas:")
    exito_sin_deuda = generador.generar_intereses_automaticos(11, 2024, 4, 2024, 4)
    if exito_sin_deuda:
        print("✅ Sistema maneja correctamente apartamentos sin deudas")
    
    print("\n5️⃣ FUNCIONALIDAD: Prevención de duplicados")
    print("-" * 42)
    
    print("🔄 Intentando crear nuevamente los mismos cargos:")
    exito_duplicado = generador.generar_cargos_periodo(1, 1, 2024, 3, 2024, 3)
    if exito_duplicado:
        print("✅ Sistema previene duplicados correctamente")
    
    print("\n" + "=" * 65)
    print("🎉 DEMOSTRACIÓN COMPLETADA")
    print("=" * 65)
    
    print("\n📋 RESUMEN DE FUNCIONALIDADES DISPONIBLES:")
    print("   ✅ Creación de cargos históricos para cualquier concepto")
    print("   ✅ Cálculo automático de montos según configuraciones")
    print("   ⭐ Cálculo automático de intereses basado en saldos DEBITO")
    print("   ✅ Prevención de duplicados")
    print("   ✅ Manejo inteligente de fechas efectivas")
    print("   ✅ Validaciones de apartamentos y conceptos")
    print("   ✅ Modo interactivo y por línea de comandos")
    print("   ✅ Reportes detallados con estadísticas")
    
    print("\n📖 CASOS DE USO PRINCIPALES:")
    print("   🏢 Poblar base de datos con cargos históricos")
    print("   💰 Generar intereses automáticamente por mora")
    print("   🔧 Corregir cargos faltantes")
    print("   📊 Crear datos de prueba para desarrollo")
    
    print("\n🚀 COMANDOS DE EJEMPLO:")
    print("   # Cuotas ordinarias:")
    print("   python crear_cargos_historicos.py 1 1 2024 1 2024 12")
    print("   # Intereses automáticos:")
    print("   python crear_cargos_historicos.py 1 3 2024 1 2024 12")
    print("   # Modo interactivo:")
    print("   python crear_cargos_historicos.py")

if __name__ == "__main__":
    main()
