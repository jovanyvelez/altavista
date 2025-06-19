#!/usr/bin/env python3
"""
Generador de Cargos Históricos para Apartamentos
===============================================

Este script permite crear cargos históricos para apartamentos específicos
que no han realizado pagos. Útil para poblar la base de datos con datos
de ejemplo o para corregir cargos faltantes.

Conceptos típicos:
- Concepto 1: Cuota Ordinaria Administración ✅
- Concepto 2: Cuota Extraordinaria
- Concepto 3: Intereses por Mora (calculados automáticamente) ⭐
- Concepto 7: Servicios Públicos Comunes
- Concepto 9: Servicio Aseo
- Concepto 10: Reparaciones Menores

Uso:
  python crear_cargos_historicos.py <apartamento_id> <concepto_id> <año_inicio> <mes_inicio> <año_fin> <mes_fin>
  python crear_cargos_historicos.py 1 1 2024 1 2025 6

Ejemplos:
  # Crear cuotas ordinarias para apartamento 1 desde enero 2024 hasta junio 2025
  python crear_cargos_historicos.py 1 1 2024 1 2025 6
  
  # Crear servicios públicos para apartamento 5 todo el año 2024
  python crear_cargos_historicos.py 5 7 2024 1 2024 12
  
  # Crear intereses automáticos para apartamento 1 todo el año 2024
  python crear_cargos_historicos.py 1 3 2024 1 2024 12
  
  # Crear múltiples conceptos (use el script interactivo)
  python crear_cargos_historicos.py 1
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlmodel import create_engine, Session, select, text
from datetime import date, datetime
from decimal import Decimal
import calendar

# Importaciones del proyecto
from app.models.database import DATABASE_URL
from app.models import (
    Apartamento, Concepto, RegistroFinancieroApartamento,
    CuotaConfiguracion
)
from app.models.enums import TipoMovimientoEnum


class GeneradorCargosHistoricos:
    """
    Generador de cargos históricos para apartamentos específicos.
    """
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        
    def verificar_apartamento(self, apartamento_id: int) -> bool:
        """Verifica que el apartamento existe"""
        with Session(self.engine) as session:
            apartamento = session.exec(
                select(Apartamento).where(Apartamento.id == apartamento_id)
            ).first()
            
            if apartamento:
                print(f"✅ Apartamento encontrado: {apartamento.identificador}")
                return True
            else:
                print(f"❌ No se encontró apartamento con ID {apartamento_id}")
                return False
    
    def verificar_conceptos(self, concepto_ids: list = None):
        """Verifica y muestra los conceptos disponibles"""
        with Session(self.engine) as session:
            if concepto_ids:
                conceptos = session.exec(
                    select(Concepto).where(Concepto.id.in_(concepto_ids))
                ).all()
            else:
                conceptos = session.exec(select(Concepto)).all()
            
            print("📋 Conceptos disponibles:")
            for concepto in conceptos:
                print(f"   ID {concepto.id}: {concepto.nombre}")
            
            return conceptos
    
    def obtener_monto_cuota(self, apartamento_id: int, año: int, mes: int) -> Decimal:
        """Obtiene el monto de la cuota configurada o usa un valor por defecto"""
        with Session(self.engine) as session:
            # Buscar configuración específica
            config = session.exec(
                select(CuotaConfiguracion).where(
                    CuotaConfiguracion.apartamento_id == apartamento_id,
                    CuotaConfiguracion.año == año,
                    CuotaConfiguracion.mes == mes
                )
            ).first()
            
            if config:
                return config.monto_cuota_ordinaria_mensual
            
            # Buscar configuración del año sin mes específico
            config_año = session.exec(
                select(CuotaConfiguracion).where(
                    CuotaConfiguracion.apartamento_id == apartamento_id,
                    CuotaConfiguracion.año == año
                ).limit(1)
            ).first()
            
            if config_año:
                return config_año.monto_cuota_ordinaria_mensual
            
            # Valor por defecto
            return Decimal("150000.00")  # Ajustar según sea necesario
    
    def verificar_cargo_existente(self, apartamento_id: int, concepto_id: int, año: int, mes: int) -> bool:
        """Verifica si ya existe un cargo para el período específico"""
        with Session(self.engine) as session:
            cargo = session.exec(
                select(RegistroFinancieroApartamento).where(
                    RegistroFinancieroApartamento.apartamento_id == apartamento_id,
                    RegistroFinancieroApartamento.concepto_id == concepto_id,
                    RegistroFinancieroApartamento.año_aplicable == año,
                    RegistroFinancieroApartamento.mes_aplicable == mes,
                    RegistroFinancieroApartamento.tipo_movimiento == "DEBITO"
                )
            ).first()
            
            return cargo is not None
    
    def crear_cargo_cuota_ordinaria(self, apartamento_id: int, año: int, mes: int, monto: Decimal) -> bool:
        """Crea un cargo por cuota ordinaria (concepto 1)"""
        with Session(self.engine) as session:
            try:
                # Fecha efectiva: día 5 del mes
                fecha_efectiva = date(año, mes, 5)
                
                cargo = RegistroFinancieroApartamento(
                    apartamento_id=apartamento_id,
                    concepto_id=1,  # Cuota Ordinaria Administración
                    tipo_movimiento="DEBITO",
                    monto=monto,
                    fecha_efectiva=fecha_efectiva,
                    mes_aplicable=mes,
                    año_aplicable=año,
                    descripcion_adicional=f"Cuota ordinaria {mes:02d}/{año} - Carga histórica",
                    referencia_pago=f"HIST-CUOTA-{año}{mes:02d}-{apartamento_id}"
                )
                
                session.add(cargo)
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                print(f"❌ Error creando cuota ordinaria {mes:02d}/{año}: {e}")
                return False
    
    def crear_cargo_concepto(self, apartamento_id: int, concepto_id: int, año: int, mes: int, monto: Decimal) -> bool:
        """Crea un cargo para cualquier concepto específico"""
        with Session(self.engine) as session:
            try:
                # Verificar que el concepto existe
                concepto = session.exec(
                    select(Concepto).where(Concepto.id == concepto_id)
                ).first()
                
                if not concepto:
                    print(f"❌ Concepto {concepto_id} no existe")
                    return False
                
                # Determinar fecha efectiva según el concepto
                if concepto_id == 1:  # Cuota ordinaria
                    dia = 5
                elif concepto_id in [7, 9, 10]:  # Servicios/gastos
                    dia = 15
                else:
                    dia = 10
                
                fecha_efectiva = date(año, mes, dia)
                
                cargo = RegistroFinancieroApartamento(
                    apartamento_id=apartamento_id,
                    concepto_id=concepto_id,
                    tipo_movimiento="DEBITO",
                    monto=monto,
                    fecha_efectiva=fecha_efectiva,
                    mes_aplicable=mes,
                    año_aplicable=año,
                    descripcion_adicional=f"{concepto.nombre} {mes:02d}/{año} - Carga histórica",
                    referencia_pago=f"HIST-C{concepto_id}-{año}{mes:02d}-{apartamento_id}"
                )
                
                session.add(cargo)
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                print(f"❌ Error creando cargo concepto {concepto_id} {mes:02d}/{año}: {e}")
                return False
    
    def generar_cargos_periodo(self, apartamento_id: int, concepto_id: int, año_inicio: int, mes_inicio: int, 
                              año_fin: int, mes_fin: int, monto_personalizado: Decimal = None):
        """Genera cargos para un concepto específico en un período"""
        
        # Si es concepto 3 (intereses), usar método especializado
        if concepto_id == 3:
            return self.generar_intereses_automaticos(apartamento_id, año_inicio, mes_inicio, año_fin, mes_fin)
        
        print(f"🚀 Generando cargos históricos para apartamento {apartamento_id}")
        print(f"📋 Concepto: {concepto_id}")
        print(f"📅 Período: {mes_inicio:02d}/{año_inicio} - {mes_fin:02d}/{año_fin}")
        print("=" * 60)
        
        # Verificaciones iniciales
        if not self.verificar_apartamento(apartamento_id):
            return False
        
        conceptos = self.verificar_conceptos([concepto_id])
        if not conceptos:
            print(f"❌ No se encontró el concepto {concepto_id}")
            return False
        
        concepto = conceptos[0]
        cargos_creados = 0
        cargos_saltados = 0
        errores = 0
        
        # Determinar montos según concepto
        montos_default = {
            1: Decimal("150000.00"),   # Cuota ordinaria
            2: Decimal("200000.00"),   # Cuota extraordinaria
            7: Decimal("25000.00"),    # Servicios públicos
            9: Decimal("30000.00"),    # Servicio aseo
            10: Decimal("15000.00"),   # Reparaciones menores
            12: Decimal("20000.00"),   # Fondo imprevistos
        }
        
        # Iterar por cada mes en el período
        año_actual = año_inicio
        mes_actual = mes_inicio
        
        while (año_actual < año_fin) or (año_actual == año_fin and mes_actual <= mes_fin):
            print(f"\n📆 Procesando {mes_actual:02d}/{año_actual}...")
            
            # Determinar monto
            if monto_personalizado:
                monto = monto_personalizado
            elif concepto_id == 1:
                monto = self.obtener_monto_cuota(apartamento_id, año_actual, mes_actual)
            else:
                monto = montos_default.get(concepto_id, Decimal("50000.00"))
            
            # Verificar si ya existe el cargo
            if self.verificar_cargo_existente(apartamento_id, concepto_id, año_actual, mes_actual):
                print(f"   ⏭️  Cargo ya existe")
                cargos_saltados += 1
            else:
                if self.crear_cargo_concepto(apartamento_id, concepto_id, año_actual, mes_actual, monto):
                    print(f"   ✅ Cargo creado: ${monto:,.2f}")
                    cargos_creados += 1
                else:
                    errores += 1
            
            # Avanzar al siguiente mes
            if mes_actual == 12:
                mes_actual = 1
                año_actual += 1
            else:
                mes_actual += 1
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE GENERACIÓN:")
        print(f"   ✅ Cargos creados: {cargos_creados}")
        print(f"   ⏭️  Cargos saltados (ya existían): {cargos_saltados}")
        print(f"   ❌ Errores: {errores}")
        
        if errores == 0:
            print("🎉 Generación completada exitosamente!")
        else:
            print("⚠️  Generación completada con errores")
        
        return errores == 0

    def calcular_saldo_acumulado_hasta_mes(self, apartamento_id: int, año: int, mes: int) -> Decimal:
        """
        Calcula el saldo neto ACUMULADO hasta el final del mes específico (incluido).
        
        Para el cálculo de intereses:
        - Incluye TODOS los movimientos desde el inicio hasta el final del mes indicado
        - Excluye intereses (concepto 3) para evitar interés sobre interés
        - Retorna el saldo neto: positivo = débito pendiente, negativo/cero = sin deuda
        """
        with Session(self.engine) as session:
            periodo_limite = año * 100 + mes

            sql_saldo = f"""
                SELECT 
                    COALESCE(SUM(CASE 
                        WHEN tipo_movimiento = 'DEBITO' THEN monto 
                        WHEN tipo_movimiento = 'CREDITO' THEN -monto 
                        ELSE 0
                    END), 0) as saldo_neto
                FROM registro_financiero_apartamento
                WHERE apartamento_id = {apartamento_id}
                AND (año_aplicable * 100 + mes_aplicable) <= {periodo_limite};
            """
            
            resultado = session.exec(text(sql_saldo)).first()
            saldo_neto = resultado.saldo_neto if resultado and resultado.saldo_neto else Decimal('0.00')
            
            return saldo_neto

    def obtener_tasa_interes(self, año: int, mes: int) -> Decimal:
        """Obtiene la tasa de interés para un período específico"""
        with Session(self.engine) as session:
            # Buscar en tabla tasa_interes_mora
            from app.models import TasaInteresMora
            
            tasa = session.exec(
                select(TasaInteresMora).where(
                    TasaInteresMora.año == año,
                    TasaInteresMora.mes == mes
                )
            ).first()
            
            if tasa:
                return tasa.tasa_interes_mensual
            
            # Buscar tasa del año
            tasa_año = session.exec(
                select(TasaInteresMora).where(
                    TasaInteresMora.año == año
                ).limit(1)
            ).first()
            
            if tasa_año:
                return tasa_año.tasa_interes_mensual
            
            # Tasa por defecto (1.5% mensual)
            return Decimal("0.015")

    def crear_cargo_interes_calculado(self, apartamento_id: int, año: int, mes: int) -> bool:
        """
        Crea un cargo de interés calculado automáticamente basado en el saldo neto del mes anterior.
        
        LÓGICA CORRECTA PARA INTERESES:
        1. Calcula saldo acumulado hasta el final del mes anterior
        2. Si saldo acumulado > 0 (hay débito pendiente), crea interés
        3. Interés = saldo_acumulado_mes_anterior × tasa_interés_mes_actual
        4. Si saldo acumulado <= 0, NO se crea interés
        """
        
        # Calcular mes anterior
        if mes == 1:
            año_anterior = año - 1
            mes_anterior = 12
        else:
            año_anterior = año
            mes_anterior = mes - 1
        
        # Obtener saldo neto ACUMULADO hasta el final del mes anterior
        saldo_mes_anterior = self.calcular_saldo_acumulado_hasta_mes(apartamento_id, año_anterior, mes_anterior)
        
        if saldo_mes_anterior <= Decimal('0.00'):
            print(f"   ℹ️  Saldo acumulado al {mes_anterior:02d}/{año_anterior}: ${saldo_mes_anterior:,.2f} - No se genera interés")
            return True  # No es error, simplemente no hay saldo débito para generar interés
        
        # Obtener tasa de interés del mes actual
        tasa_decimal = self.obtener_tasa_interes(año_anterior, mes_anterior)
        tasa_porcentaje = float(tasa_decimal) * 100
        
        # Calcular monto del interés: saldo_débito_anterior × tasa_actual
        monto_interes = saldo_mes_anterior * tasa_decimal
        monto_interes = monto_interes.quantize(Decimal('0.01'))  # Redondear a centavos
        
        if monto_interes <= Decimal('0.01'):
            print(f"   ℹ️  Interés calculado muy pequeño (${monto_interes}), se omite")
            return True
        
        with Session(self.engine) as session:
            try:
                # Verificar que el concepto 3 existe
                concepto = session.exec(
                    select(Concepto).where(Concepto.id == 3)
                ).first()
                
                if not concepto:
                    print(f"❌ Concepto 3 (Intereses) no existe")
                    return False
                
                # Fecha efectiva: último día del mes actual
                import calendar
                ultimo_dia = calendar.monthrange(año, mes)[1]
                fecha_efectiva = date(año, mes, ultimo_dia)
                
                descripcion = (f"Interés {tasa_porcentaje:.2f}% sobre saldo acumulado "
                             f"${saldo_mes_anterior:,.2f} al {mes_anterior:02d}/{año_anterior}")
                
                cargo = RegistroFinancieroApartamento(
                    apartamento_id=apartamento_id,
                    concepto_id=3,
                    tipo_movimiento="DEBITO",
                    monto=monto_interes,
                    fecha_efectiva=fecha_efectiva,
                    mes_aplicable=mes,
                    año_aplicable=año,
                    descripcion_adicional=descripcion,
                    referencia_pago=f"HIST-INT-{año}{mes:02d}-{apartamento_id}"
                )
                
                session.add(cargo)
                session.commit()
                
                print(f"   ✅ Interés: ${monto_interes:,.2f} "
                      f"({tasa_porcentaje:.2f}% sobre ${saldo_mes_anterior:,.2f} de {mes_anterior:02d}/{año_anterior})")
                return True
                
            except Exception as e:
                session.rollback()
                print(f"❌ Error creando interés calculado {mes:02d}/{año}: {e}")
                return False

    def generar_intereses_automaticos(self, apartamento_id: int, año_inicio: int, mes_inicio: int, 
                                    año_fin: int, mes_fin: int):
        """
        Genera intereses automáticos para un período basándose en la lógica corregida:
        
        PARA CADA MES:
        1. Calcula saldo acumulado hasta el final del mes anterior
        2. Si saldo acumulado > 0: crea interés = saldo_acumulado × tasa_mes_actual
        3. Si saldo acumulado ≤ 0: NO crea interés para ese mes
        """
        
        print(f"🧮 Generando intereses automáticos para apartamento {apartamento_id}")
        print(f"📅 Período: {mes_inicio:02d}/{año_inicio} - {mes_fin:02d}/{año_fin}")
        print("💡 Base: Saldo acumulado hasta el final del mes anterior")
        print("✅ Solo crea interés si saldo acumulado anterior > 0")
        print("=" * 60)
        
        # Verificaciones iniciales
        if not self.verificar_apartamento(apartamento_id):
            return False
        
        conceptos = self.verificar_conceptos([3])
        if not conceptos:
            print("❌ No se encontró el concepto 3 (Intereses por Mora)")
            return False
        
        intereses_creados = 0
        intereses_saltados = 0
        sin_base_para_interes = 0
        errores = 0
        monto_total = Decimal('0.00')
        
        # Iterar por cada mes en el período
        año_actual = año_inicio
        mes_actual = mes_inicio
        
        while (año_actual < año_fin) or (año_actual == año_fin and mes_actual <= mes_fin):
            print(f"\n📆 Procesando intereses para {mes_actual:02d}/{año_actual}...")
            
            # Verificar si ya existe el interés
            if self.verificar_cargo_existente(apartamento_id, 3, año_actual, mes_actual):
                print(f"   ⏭️  Interés ya existe")
                intereses_saltados += 1
            else:
                resultado = self.crear_cargo_interes_calculado(apartamento_id, año_actual, mes_actual)
                if resultado:
                    # Verificar si realmente se creó un cargo (o si no había base para interés)
                    with Session(self.engine) as session:
                        cargo_creado = session.exec(
                            select(RegistroFinancieroApartamento).where(
                                RegistroFinancieroApartamento.apartamento_id == apartamento_id,
                                RegistroFinancieroApartamento.concepto_id == 3,
                                RegistroFinancieroApartamento.año_aplicable == año_actual,
                                RegistroFinancieroApartamento.mes_aplicable == mes_actual
                            )
                        ).first()
                        
                        if cargo_creado:
                            monto_total += cargo_creado.monto
                            intereses_creados += 1
                        else:
                            sin_base_para_interes += 1
                else:
                    errores += 1
            
            # Avanzar al siguiente mes
            if mes_actual == 12:
                mes_actual = 1
                año_actual += 1
            else:
                mes_actual += 1
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE INTERESES AUTOMÁTICOS:")
        print(f"   ✅ Intereses creados: {intereses_creados}")
        print(f"   💰 Monto total generado: ${monto_total:,.2f}")
        print(f"   ⏭️  Intereses saltados (ya existían): {intereses_saltados}")
        print(f"   ℹ️  Sin base para interés (saldo ≤ 0): {sin_base_para_interes}")
        print(f"   ❌ Errores: {errores}")
        
        if errores == 0:
            print("🎉 Generación de intereses completada exitosamente!")
            print("💡 Los intereses se generan solo cuando el saldo del mes anterior > 0")
        else:
            print("⚠️  Generación completada con errores")
        
        return errores == 0


def mostrar_ayuda():
    """Muestra la ayuda del script"""
    print("""
🏢 GENERADOR DE CARGOS HISTÓRICOS

Uso:
  python crear_cargos_historicos.py <apartamento_id> <concepto_id> <año_inicio> <mes_inicio> <año_fin> <mes_fin>

Parámetros:
  apartamento_id  : ID del apartamento (número entero)
  concepto_id     : ID del concepto a crear (1, 2, 7, 9, 10, etc.)
  año_inicio      : Año de inicio (ej: 2024)
  mes_inicio      : Mes de inicio (1-12)
  año_fin         : Año de fin (ej: 2025)
  mes_fin         : Mes de fin (1-12)

Ejemplos:
  # Apartamento 1, concepto 1 (cuotas), desde enero 2024 hasta junio 2025
  python crear_cargos_historicos.py 1 1 2024 1 2025 6
  
  # Apartamento 5, concepto 7 (servicios públicos), todo el año 2024
  python crear_cargos_historicos.py 5 7 2024 1 2024 12
  
  # Ver conceptos disponibles
  python verificar_bd.py

Conceptos más comunes:
  1 - Cuota Ordinaria Administración
  2 - Cuota Extraordinaria  
  7 - Servicios Públicos Comunes
  9 - Servicio Aseo
  10 - Reparaciones Menores

Notas:
  - Solo crea cargos que no existan previamente
  - Usa montos apropiados según el concepto
  - Crea fechas efectivas realistas según el tipo de concepto
""")


def modo_interactivo():
    """Modo interactivo para crear múltiples cargos"""
    print("🔧 MODO INTERACTIVO")
    print("=" * 40)
    
    try:
        # Obtener apartamento
        apartamento_id = int(input("Ingrese ID del apartamento: "))
        
        # Obtener período
        año_inicio = int(input("Año de inicio (ej: 2024): "))
        mes_inicio = int(input("Mes de inicio (1-12): "))
        año_fin = int(input("Año de fin (ej: 2025): "))
        mes_fin = int(input("Mes de fin (1-12): "))
        
        # Mostrar conceptos comunes
        print("\n📋 Conceptos comunes:")
        print("1 - Cuota Ordinaria Administración")
        print("2 - Cuota Extraordinaria")
        print("7 - Servicios Públicos Comunes")
        print("9 - Servicio Aseo")
        print("10 - Reparaciones Menores")
        
        conceptos_str = input("\nIngrese IDs de conceptos separados por coma (ej: 1,7,9): ")
        conceptos = [int(c.strip()) for c in conceptos_str.split(",")]
        
        # Generar cargos
        generador = GeneradorCargosHistoricos()
        
        for concepto_id in conceptos:
            print(f"\n🔄 Procesando concepto {concepto_id}...")
            generador.generar_cargos_periodo(
                apartamento_id, concepto_id, año_inicio, mes_inicio, año_fin, mes_fin
            )
        
        print("\n🎉 Procesamiento interactivo completado!")
        
    except ValueError:
        print("❌ Error: Ingrese solo números válidos")
    except KeyboardInterrupt:
        print("\n⚠️ Cancelado por el usuario")
    except Exception as e:
        print(f"💥 Error: {e}")


def main():
    """Función principal"""
    if len(sys.argv) == 1:
        # Modo interactivo
        modo_interactivo()
        return
    elif len(sys.argv) < 7:
        mostrar_ayuda()
        sys.exit(1)
    
    try:
        apartamento_id = int(sys.argv[1])
        concepto_id = int(sys.argv[2])
        año_inicio = int(sys.argv[3])
        mes_inicio = int(sys.argv[4])
        año_fin = int(sys.argv[5])
        mes_fin = int(sys.argv[6])
        
        # Validaciones básicas
        if not (1 <= mes_inicio <= 12) or not (1 <= mes_fin <= 12):
            print("❌ Los meses deben estar entre 1 y 12")
            sys.exit(1)
        
        if año_inicio > año_fin or (año_inicio == año_fin and mes_inicio > mes_fin):
            print("❌ La fecha de inicio debe ser anterior a la fecha de fin")
            sys.exit(1)
        
        # Ejecutar generación
        generador = GeneradorCargosHistoricos()
        exito = generador.generar_cargos_periodo(
            apartamento_id, concepto_id, año_inicio, mes_inicio, año_fin, mes_fin
        )
        
        sys.exit(0 if exito else 1)
        
    except ValueError:
        print("❌ Todos los parámetros deben ser números enteros")
        mostrar_ayuda()
        sys.exit(1)
    except Exception as e:
        print(f"💥 Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
