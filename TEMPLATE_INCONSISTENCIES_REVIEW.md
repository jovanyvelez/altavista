# Revisión de Inconsistencias Template-Rutas

## PROBLEMAS IDENTIFICADOS

### 1. Modelo Propietario - Inconsistencia de nombres
**PROBLEMA**: El modelo define `nombre_completo` pero en el código se usa `nombre`

**Archivos afectados**:
- `app/models/propietario.py` - Define `nombre_completo: str`
- `app/services/initial_data.py` - Usa `nombre=` (líneas 65, 80)
- `app/routes/admin.py` - Usa `nombre=` (líneas 155, 390)
- `templates/admin/propietarios.html` - Usa `{{ propietario.nombre_completo }}`

**CAUSA**: Inconsistencia entre modelo y uso en código

### 2. Variables faltantes en templates
Necesito verificar qué variables esperan cada template y cuáles se pasan desde las rutas

### 3. Relaciones no cargadas
El template `propietarios.html` usa `propietario.apartamentos` pero las relaciones pueden no estar cargándose

### 4. Template presupuesto_detalle.html
Espera variables: `presupuesto`, `total_ingresos`, `total_gastos`, `balance`, `conceptos`

### 5. Template registros_financieros.html  
Espera: `apartamento` con propiedad `identificador`
Modelo Apartamento puede no tener `identificador`, solo `numero`

## ARCHIVOS A REVISAR
1. Todos los templates admin
2. Todas las rutas admin correspondientes 
3. Verificar modelos vs uso
4. Verificar relaciones SQLModel
