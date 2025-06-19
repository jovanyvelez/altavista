#!/usr/bin/env python3
"""
Verificador de Conceptos en Base de Datos
========================================

Script para verificar qué conceptos existen en la base de datos
y obtener información sobre apartamentos.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlmodel import create_engine, Session, select

# Importaciones del proyecto
from app.models.database import DATABASE_URL
from app.models import Apartamento, Concepto


def verificar_conceptos():
    """Muestra todos los conceptos disponibles"""
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        conceptos = session.exec(select(Concepto)).all()
        
        print("📋 CONCEPTOS DISPONIBLES EN LA BASE DE DATOS:")
        print("=" * 60)
        
        if not conceptos:
            print("❌ No hay conceptos en la base de datos")
            return
        
        for concepto in conceptos:
            ingreso = "✅ SÍ" if concepto.es_ingreso_tipico else "❌ NO"
            recurrente = "✅ SÍ" if concepto.es_recurrente_presupuesto else "❌ NO"
            
            print(f"ID {concepto.id:2d}: {concepto.nombre}")
            print(f"       Es ingreso típico: {ingreso}")
            print(f"       Es recurrente: {recurrente}")
            if concepto.descripcion:
                print(f"       Descripción: {concepto.descripcion}")
            print()


def verificar_apartamentos():
    """Muestra información de apartamentos"""
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        apartamentos = session.exec(select(Apartamento)).all()
        
        print("🏢 APARTAMENTOS DISPONIBLES:")
        print("=" * 40)
        
        if not apartamentos:
            print("❌ No hay apartamentos en la base de datos")
            return
        
        for apt in apartamentos[:10]:  # Mostrar solo los primeros 10
            print(f"ID {apt.id:2d}: {apt.identificador}")
        
        if len(apartamentos) > 10:
            print(f"... y {len(apartamentos) - 10} apartamentos más")
        
        print(f"\n📊 Total de apartamentos: {len(apartamentos)}")


def main():
    print("🔍 VERIFICADOR DE BASE DE DATOS")
    print("=" * 50)
    
    try:
        verificar_conceptos()
        print("\n")
        verificar_apartamentos()
        
        print("\n" + "=" * 50)
        print("✅ Verificación completada")
        
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
