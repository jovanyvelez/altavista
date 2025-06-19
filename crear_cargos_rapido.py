#!/usr/bin/env python3
"""
Script Rápido para Crear Cargos de Apartamento Específico
========================================================

Script simplificado para crear cargos rápidamente para un apartamento específico.

Uso:
  python crear_cargos_rapido.py <apartamento_id>

Este script creará cargos para los últimos 12 meses automáticamente.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlmodel import create_engine, Session, select
from datetime import date, datetime, timedelta
from decimal import Decimal
import calendar

# Importaciones del proyecto
from app.models.database import DATABASE_URL
from app.models import (
    Apartamento, Concepto, RegistroFinancieroApartamento
)


def crear_cargos_rapido(apartamento_id: int):
    """Crear cargos rápidos para los últimos 12 meses"""
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        # Verificar apartamento
        apartamento = session.exec(
            select(Apartamento).where(Apartamento.id == apartamento_id)
        ).first()
        
        if not apartamento:
            print(f"❌ No se encontró apartamento con ID {apartamento_id}")
            return False
        
        print(f"🏢 Creando cargos para apartamento: {apartamento.identificador}")
        
        # Verificar conceptos
        concepto1 = session.exec(select(Concepto).where(Concepto.id == 1)).first()
        concepto3 = session.exec(select(Concepto).where(Concepto.id == 3)).first()
        
        if not concepto1:
            print("❌ No se encontró concepto 1")
            return False
        
        print(f"📋 Concepto 1: {concepto1.nombre}")
        if concepto3:
            print(f"📋 Concepto 3: {concepto3.nombre}")
        
        # Crear cargos para los últimos 12 meses
        hoy = date.today()
        cargos_creados = 0
        
        for i in range(12):
            # Calcular fecha del mes
            if hoy.month - i <= 0:
                mes = hoy.month - i + 12
                año = hoy.year - 1
            else:
                mes = hoy.month - i
                año = hoy.year
            
            print(f"\n📅 Procesando {mes:02d}/{año}...")
            
            # Verificar si ya existen cargos
            existe_c1 = session.exec(
                select(RegistroFinancieroApartamento).where(
                    RegistroFinancieroApartamento.apartamento_id == apartamento_id,
                    RegistroFinancieroApartamento.concepto_id == 1,
                    RegistroFinancieroApartamento.año_aplicable == año,
                    RegistroFinancieroApartamento.mes_aplicable == mes,
                    RegistroFinancieroApartamento.tipo_movimiento == "DEBITO"
                )
            ).first()
            
            if existe_c1:
                print(f"   ⏭️  Cuota ordinaria ya existe")
            else:
                # Crear cuota ordinaria
                cargo1 = RegistroFinancieroApartamento(
                    apartamento_id=apartamento_id,
                    concepto_id=1,
                    tipo_movimiento="DEBITO",
                    monto=Decimal("150000.00"),  # Monto por defecto
                    fecha_efectiva=date(año, mes, 5),
                    mes_aplicable=mes,
                    año_aplicable=año,
                    descripcion_adicional=f"Cuota ordinaria {mes:02d}/{año} - Carga rápida",
                    referencia_pago=f"RAPIDO-C1-{año}{mes:02d}-{apartamento_id}"
                )
                session.add(cargo1)
                print(f"   ✅ Cuota ordinaria creada: $150,000.00")
                cargos_creados += 1
            
            # Crear concepto 3 si existe
            if concepto3:
                existe_c3 = session.exec(
                    select(RegistroFinancieroApartamento).where(
                        RegistroFinancieroApartamento.apartamento_id == apartamento_id,
                        RegistroFinancieroApartamento.concepto_id == 3,
                        RegistroFinancieroApartamento.año_aplicable == año,
                        RegistroFinancieroApartamento.mes_aplicable == mes,
                        RegistroFinancieroApartamento.tipo_movimiento == "DEBITO"
                    )
                ).first()
                
                if existe_c3:
                    print(f"   ⏭️  Cargo concepto 3 ya existe")
                else:
                    cargo3 = RegistroFinancieroApartamento(
                        apartamento_id=apartamento_id,
                        concepto_id=3,
                        tipo_movimiento="DEBITO",
                        monto=Decimal("15000.00"),  # 10% de la cuota
                        fecha_efectiva=date(año, mes, 10),
                        mes_aplicable=mes,
                        año_aplicable=año,
                        descripcion_adicional=f"{concepto3.nombre} {mes:02d}/{año} - Carga rápida",
                        referencia_pago=f"RAPIDO-C3-{año}{mes:02d}-{apartamento_id}"
                    )
                    session.add(cargo3)
                    print(f"   ✅ Cargo concepto 3 creado: $15,000.00")
                    cargos_creados += 1
        
        # Guardar cambios
        session.commit()
        
        print(f"\n🎉 Proceso completado: {cargos_creados} cargos creados")
        return True


def main():
    if len(sys.argv) != 2:
        print("Uso: python crear_cargos_rapido.py <apartamento_id>")
        print("Ejemplo: python crear_cargos_rapido.py 1")
        sys.exit(1)
    
    try:
        apartamento_id = int(sys.argv[1])
        crear_cargos_rapido(apartamento_id)
    except ValueError:
        print("❌ El apartamento_id debe ser un número entero")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
