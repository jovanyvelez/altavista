# 🪄 Sistema de Pago Automático - Guía de Usuario

## 📋 Descripción General

El nuevo sistema de pago automático permite procesar pagos de forma inteligente, distribuyendo automáticamente el dinero según las prioridades establecidas:

1. **Intereses por mora** (más antiguos primero)
2. **Cuotas ordinarias** (más antiguas primero)  
3. **Pago en exceso** (si sobra dinero)

## 🎯 Funcionalidades Implementadas

### ✨ Botón "Pagar Valor" (Automático)
- **Ubicación**: En la tabla de apartamentos con saldos pendientes
- **Función**: Abre un modal con información detallada de la deuda
- **Distribución**: Automática según prioridades establecidas

### 💡 Lógica de Distribución

#### Caso 1: Apartamento al día con solo una cuota pendiente
- Si el monto = cuota pendiente → Se registra pago completo
- Si el monto ≠ cuota pendiente → Se registra pago parcial o exceso

#### Caso 2: Apartamento con cuotas atrasadas
**Orden de aplicación:**
1. Intereses más antiguos (concepto ID: 4)
2. Cuotas más antiguas (concepto ID: 5)
3. Exceso si sobra dinero (concepto ID: 15)

**Ejemplo práctico:**
```
Deuda del apartamento:
- Interés Ene/2025: $1,000
- Cuota Ene/2025: $80,000  
- Interés Feb/2025: $900
- Cuota Feb/2025: $80,000

Con un pago de $85,000:
✅ Interés Ene/2025: $1,000 (COMPLETO)
✅ Cuota Ene/2025: $80,000 (COMPLETO) 
✅ Interés Feb/2025: $900 (COMPLETO)
✅ Cuota Feb/2025: $3,100 (PARCIAL)
Pendiente: $76,900 en cuota Feb/2025
```

## 🖥️ Interfaz de Usuario

### 🆕 Nuevos Elementos

1. **Botón "🪄 Pagar"** (amarillo/warning)
   - Abre modal de pago automático
   - Carga información de deuda en tiempo real

2. **Modal de Pago Automático**
   - Resumen de deuda (total, intereses, cuotas)
   - Campo de monto del pago
   - Campo de referencia (opcional)
   - Explicación de la distribución automática

3. **Mensajes de Confirmación Mejorados**
   - Información específica del pago automático
   - Monto procesado y número de registros creados

### 🔄 Flujo de Uso

1. **Acceder a la página**: `/admin/pagos/procesar`
2. **Localizar apartamento** con saldo pendiente
3. **Hacer clic** en el botón "🪄 Pagar"
4. **Revisar resumen** de deuda cargado automáticamente
5. **Ingresar monto** a pagar
6. **Agregar referencia** (opcional)
7. **Confirmar pago** automático
8. **Verificar resultado** en la página de confirmación

## 🔧 Aspectos Técnicos

### 📡 Nuevas Rutas API

- `POST /admin/pagos/pago-automatico` - Procesa pago automático
- `GET /admin/pagos/resumen-deuda/{apartamento_id}` - Obtiene resumen de deuda

### 🗄️ Registros Creados

El sistema crea automáticamente registros de tipo CREDITO con:
- **Concepto correcto** (Pago de Cuota o Pago de Intereses)
- **Fecha efectiva** ajustada al período correspondiente
- **Descripción** descriptiva del pago
- **Referencia** proporcionada por el usuario

### 📊 Estructura de Respuesta

```json
{
  "success": true,
  "monto_original": 85000.00,
  "monto_procesado": 85000.00,
  "monto_restante": 0.00,
  "pagos_realizados": [
    {
      "concepto_id": 4,
      "periodo": "01/2025", 
      "monto": 1000.00,
      "tipo": "Interés"
    },
    // ... más pagos
  ],
  "mensaje": "Intereses: $1,900.00 (2 períodos) | Cuotas: $83,100.00 (2 períodos)"
}
```

## ✅ Ventajas del Sistema

1. **Automatización**: Sin cálculos manuales
2. **Consistencia**: Aplicación uniforme de prioridades  
3. **Transparencia**: Información clara de la distribución
4. **Flexibilidad**: Maneja cualquier monto de pago
5. **Auditoría**: Registros detallados de cada transacción

## 🚨 Consideraciones Importantes

- ⚠️ **Validación**: El sistema valida montos y disponibilidad
- 🔄 **Transacciones**: Operaciones atómicas (todo o nada)
- 📝 **Auditoría**: Cada pago genera registros rastreables
- 🔒 **Seguridad**: Requiere permisos de administrador

## 🧪 Testing

Se incluyen scripts de prueba:
- `test_pago_automatico.py` - Pruebas unitarias
- `demo_pago_automatico.py` - Demostración con casos reales

---

**💡 Tip**: El botón manual (💲) sigue disponible para casos especiales que requieran procesamiento manual específico.
