# 🏢 GUÍA COMPLETA DE CARGOS HISTÓRICOS - Sistema de Administración PIA

## 📋 Descripción General

Este módulo permite crear cargos históricos para apartamentos específicos, incluyendo la nueva funcionalidad de **cálculo automático de intereses por mora** basado en saldos DEBITO pendientes.

## ⭐ NUEVA FUNCIONALIDAD: Cálculo Automático de Intereses

### Características Principales:
- **Cálculo automático**: Los intereses se calculan automáticamente basándose en saldos DEBITO del mes anterior
- **Tasas dinámicas**: Utiliza las tasas de interés configuradas en la tabla `tasa_interes_mora`
- **Prevención de interés sobre interés**: Excluye cargos de intereses previos del cálculo base
- **Manejo inteligente**: No genera intereses si no hay saldos pendientes

### Cómo Funciona:
1. Para cada mes, calcula el saldo DEBITO acumulado hasta el final del mes anterior
2. Obtiene la tasa de interés correspondiente al período
3. Calcula: `Interés = Saldo_Base × Tasa_Interés`
4. Crea el cargo automáticamente con descripción detallada

## 🚀 Scripts Disponibles

### 1. `crear_cargos_historicos.py` - Script Principal
**Funcionalidad completa para creación de cargos históricos**

#### Uso Básico:
```bash
# Sintaxis general
python crear_cargos_historicos.py <apartamento_id> <concepto_id> <año_inicio> <mes_inicio> <año_fin> <mes_fin>

# Ejemplos básicos
python crear_cargos_historicos.py 1 1 2024 1 2024 12    # Cuotas ordinarias
python crear_cargos_historicos.py 1 7 2024 1 2024 12    # Servicios públicos
```

#### ⭐ NUEVO: Generación Automática de Intereses:
```bash
# Intereses automáticos para todo el año 2024
python crear_cargos_historicos.py 1 3 2024 1 2024 12

# Intereses para un período específico
python crear_cargos_historicos.py 1 3 2024 6 2024 8
```

#### Modo Interactivo:
```bash
python crear_cargos_historicos.py
```

### 2. `crear_cargos_rapido.py` - Creación Rápida
**Para poblar rápidamente los últimos 12 meses**

```bash
python crear_cargos_rapido.py <apartamento_id>
python crear_cargos_rapido.py 1
```

### 3. `verificar_bd.py` - Verificación de Base de Datos
**Lista apartamentos y conceptos disponibles**

```bash
python verificar_bd.py
```

### 4. `demo_cargos_historicos_completa.py` - Demostración Completa
**Demuestra todas las funcionalidades del sistema**

```bash
python demo_cargos_historicos_completa.py
```

## 📊 Conceptos Disponibles

| ID | Nombre | Descripción | Cálculo |
|----|--------|-------------|---------|
| 1 | Cuota Ordinaria Administración | Cobro mensual regular | Según configuración |
| 2 | Cuota Extraordinaria | Cobros especiales | Monto fijo |
| **3** | **Intereses por Mora** | **⭐ AUTOMÁTICO** | **Calculado dinámicamente** |
| 7 | Servicios Públicos Comunes | Luz, agua comunes | $25,000 |
| 9 | Servicio Aseo | Personal de aseo | $30,000 |
| 10 | Reparaciones Menores | Mantenimientos | $15,000 |
| 12 | Fondo de Imprevistos | Ahorros | $20,000 |

## 🧮 Detalles del Cálculo de Intereses

### Algoritmo de Cálculo:
1. **Base del cálculo**: Saldo DEBITO acumulado hasta el final del mes anterior
2. **Exclusiones**: No incluye intereses previos para evitar interés sobre interés
3. **Tasa**: Obtiene de la tabla `tasa_interes_mora` o usa 1.5% por defecto
4. **Fórmula**: `Interés = Saldo_DEBITO × Tasa_Mensual`

### Ejemplo de Cálculo:
```
Mes: Junio 2024
Saldo DEBITO Mayo 2024: $920,000
Tasa Mayo 2024: 1.60%
Interés Calculado: $920,000 × 0.016 = $14,720
```

### Fechas Efectivas:
- **Intereses**: Último día del mes aplicable
- **Cuotas ordinarias**: Día 5 del mes
- **Servicios**: Día 15 del mes
- **Otros conceptos**: Día 10 del mes

## 📈 Casos de Uso Principales

### 1. Poblar Base de Datos Nueva
```bash
# Crear todos los conceptos básicos para un apartamento
python crear_cargos_historicos.py 1 1 2024 1 2024 12  # Cuotas
python crear_cargos_historicos.py 1 7 2024 1 2024 12  # Servicios
python crear_cargos_historicos.py 1 9 2024 1 2024 12  # Aseo
python crear_cargos_historicos.py 1 3 2024 2 2024 12  # Intereses desde febrero
```

### 2. Generar Intereses para Apartamentos Morosos
```bash
# Calcular intereses automáticamente
python crear_cargos_historicos.py 1 3 2024 1 2024 12
```

### 3. Corregir Cargos Faltantes
```bash
# Verificar qué existe
python verificar_bd.py

# Crear lo faltante
python crear_cargos_historicos.py 1 10 2024 6 2024 12
```

### 4. Datos de Prueba para Desarrollo
```bash
# Usar el modo rápido
python crear_cargos_rapido.py 1
```

## ⚠️ Consideraciones Importantes

### Intereses Automáticos:
- ✅ **Solo genera intereses si hay saldos DEBITO pendientes**
- ✅ **Excluye intereses previos del cálculo base**
- ✅ **Usa tasas dinámicas según configuración**
- ✅ **Previene duplicados automáticamente**

### Validaciones:
- ✅ **Verifica existencia de apartamentos y conceptos**
- ✅ **Previene creación de duplicados**
- ✅ **Valida rangos de fechas**
- ✅ **Maneja errores de base de datos**

### Montos por Defecto:
- Los montos se configuran automáticamente según el concepto
- Para cuotas ordinarias, busca en la tabla `cuota_configuracion`
- Usa valores por defecto razonables para otros conceptos

## 📊 Reportes y Estadísticas

Cada ejecución proporciona:
- ✅ Cargos creados exitosamente
- ⏭️ Cargos saltados (ya existían)
- ❌ Errores encontrados
- 💰 Montos totales generados (para intereses)
- 📋 Detalles de cada operación

## 🔧 Mantenimiento

### Verificar Estado:
```bash
python verificar_bd.py
```

### Probar Funcionalidad:
```bash
python demo_cargos_historicos_completa.py
```

### Logs y Errores:
- Los errores se muestran en consola con emojis descriptivos
- Las transacciones se revierten automáticamente en caso de error
- Cada cargo incluye referencia única para trazabilidad

## 🎯 Próximas Mejoras Potenciales

1. **Interfaz web** para gestión visual
2. **Carga masiva** desde archivos CSV/Excel
3. **Plantillas personalizables** por edificio
4. **Notificaciones automáticas** por email
5. **Reportes en PDF** de cargos generados

---

## 📞 Soporte

Para dudas o problemas:
1. Ejecutar `python verificar_bd.py` para diagnóstico
2. Revisar logs de error en consola
3. Verificar configuración de base de datos
4. Probar con el script de demostración

---

> ⭐ **NUEVA FUNCIONALIDAD**: El cálculo automático de intereses representa un avance significativo en la automatización del sistema, eliminando la necesidad de cálculos manuales y reduciendo errores.
