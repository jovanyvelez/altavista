# 📋 Guía de Scripts para Crear Cargos Históricos

## 🎯 Objetivo
Poblar la base de datos con cargos históricos para apartamentos que no han realizado pagos o que necesitan datos de ejemplo.

## 🛠️ Scripts Disponibles

### 1. `verificar_bd.py` - Verificar Base de Datos
**Propósito**: Ver qué conceptos y apartamentos existen en la base de datos.

```bash
python verificar_bd.py
```

**Salida**: Muestra todos los conceptos disponibles y los primeros 10 apartamentos.

---

### 2. `crear_cargos_historicos.py` - Crear Cargos Específicos
**Propósito**: Crear cargos para un concepto específico en un período determinado.

#### Sintaxis:
```bash
python crear_cargos_historicos.py <apartamento_id> <concepto_id> <año_inicio> <mes_inicio> <año_fin> <mes_fin>
```

#### Ejemplos:
```bash
# Crear cuotas ordinarias para apartamento 1 (enero-marzo 2024)
python crear_cargos_historicos.py 1 1 2024 1 2024 3

# Crear servicios públicos para apartamento 5 (todo 2024)
python crear_cargos_historicos.py 5 7 2024 1 2024 12

# Crear servicio de aseo para apartamento 10 (primer semestre 2025)
python crear_cargos_historicos.py 10 9 2025 1 2025 6
```

#### Modo Interactivo:
```bash
# Sin parámetros para modo interactivo
python crear_cargos_historicos.py
```

---

### 3. `crear_cargos_rapido.py` - Cargos Rápidos
**Propósito**: Crear cargos básicos (concepto 1 y 3) para los últimos 12 meses automáticamente.

```bash
python crear_cargos_rapido.py <apartamento_id>
```

#### Ejemplo:
```bash
# Crear cargos básicos para apartamento 1
python crear_cargos_rapido.py 1
```

---

## 📋 Conceptos Disponibles

Según tu base de datos:

| ID | Concepto | Tipo | Monto Sugerido |
|----|----------|------|----------------|
| **1** | **Cuota Ordinaria Administración** | Ingreso | $150,000 |
| **2** | **Cuota Extraordinaria** | Ingreso | $200,000 |
| 3 | Intereses por Mora | Ingreso | (Calculado) |
| 5 | Pago de Cuota | Pago | - |
| **7** | **Servicios Públicos Comunes** | Gasto | $25,000 |
| **9** | **Servicio Aseo** | Gasto | $30,000 |
| **10** | **Reparaciones Menores** | Gasto | $15,000 |
| 12 | Fondo de Imprevistos | Gasto | $20,000 |

**Los conceptos en negrita son los más comunes para cargos históricos.**

---

## 🏢 Apartamentos Disponibles

Algunos apartamentos de ejemplo:
- ID 1: 9801
- ID 2: 9802  
- ID 3: 9901
- ID 4: 9902
- ID 5: 9903
- ID 6: 101
- ID 7: 102
- ...

---

## 💡 Casos de Uso Comunes

### Escenario 1: Nuevo Apartamento Sin Historial
**Objetivo**: Crear historial completo de cuotas para un apartamento.

```bash
# Crear cuotas ordinarias para todo 2024
python crear_cargos_historicos.py 1 1 2024 1 2024 12

# Agregar servicios públicos
python crear_cargos_historicos.py 1 7 2024 1 2024 12

# Agregar servicio de aseo
python crear_cargos_historicos.py 1 9 2024 1 2024 12
```

### Escenario 2: Poblado Rápido
**Objetivo**: Crear datos básicos rápidamente.

```bash
# Usar el script rápido
python crear_cargos_rapido.py 1
```

### Escenario 3: Período Específico
**Objetivo**: Crear cargos solo para ciertos meses.

```bash
# Solo primer trimestre 2025
python crear_cargos_historicos.py 5 1 2025 1 2025 3
```

### Escenario 4: Múltiples Apartamentos
**Objetivo**: Aplicar a varios apartamentos.

```bash
# Script bash para múltiples apartamentos
for apt in 1 2 3 4 5; do
    echo "Procesando apartamento $apt..."
    python crear_cargos_historicos.py $apt 1 2024 1 2024 12
done
```

---

## ⚠️ Consideraciones Importantes

### ✅ Ventajas:
- **Control de duplicados**: No crea cargos que ya existen
- **Fechas realistas**: Asigna fechas apropiadas según el concepto
- **Montos inteligentes**: Usa configuraciones existentes o valores por defecto
- **Flexibilidad**: Permite crear cualquier concepto en cualquier período

### 🚨 Precauciones:
- **Verificar conceptos**: Usar `verificar_bd.py` antes de crear cargos
- **Validar montos**: Los montos por defecto pueden necesitar ajuste
- **Revisar fechas**: Asegurar que las fechas sean coherentes
- **Backup**: Hacer respaldo antes de crear muchos registros

---

## 🔄 Flujo Recomendado

1. **Verificar base de datos**:
   ```bash
   python verificar_bd.py
   ```

2. **Crear cargos para un apartamento de prueba**:
   ```bash
   python crear_cargos_historicos.py 1 1 2024 1 2024 3
   ```

3. **Verificar resultados** en la aplicación web o base de datos

4. **Aplicar a más apartamentos** según necesidad

5. **Usar modo interactivo** para casos complejos:
   ```bash
   python crear_cargos_historicos.py
   ```

---

## 📊 Monitoreo y Verificación

Después de crear cargos, puedes verificar:

1. **En la aplicación web**: Ir al dashboard del apartamento
2. **En base de datos**: 
   ```sql
   SELECT * FROM registro_financiero_apartamento 
   WHERE apartamento_id = 1 
   ORDER BY fecha_efectiva DESC;
   ```
3. **Saldo del apartamento**:
   ```sql
   SELECT 
       SUM(CASE WHEN tipo_movimiento = 'DEBITO' THEN monto ELSE -monto END) as saldo
   FROM registro_financiero_apartamento 
   WHERE apartamento_id = 1;
   ```

---

## 🎉 ¡Scripts Listos para Usar!

Todos los scripts están configurados y probados. Puedes comenzar a poblar tu base de datos de inmediato con datos realistas y coherentes.
