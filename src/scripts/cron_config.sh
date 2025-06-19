#!/bin/bash
# Configuración de cron job para la generación automática mensual de cargos
# Este script debe ejecutarse el día 1 de cada mes a las 02:00 AM

# Configurar variables de entorno
SCRIPT_DIR="/home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio"
VENV_PATH="$SCRIPT_DIR/.venv"
PYTHON_PATH="$VENV_PATH/bin/python"
SCRIPT_PATH="$SCRIPT_DIR/scripts/generador_v3_funcional.py"
LOG_PATH="$SCRIPT_DIR/logs/cron_generacion_automatica.log"

# Crear directorio de logs si no existe
mkdir -p "$SCRIPT_DIR/logs"

# Función para logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_PATH"
}

# Activar entorno virtual y ejecutar script
cd "$SCRIPT_DIR"

# Inicializar log
touch "$LOG_PATH"
log "=== INICIO GENERACIÓN AUTOMÁTICA MENSUAL ==="
log "Directorio de trabajo: $(pwd)"
log "Activando entorno virtual: $VENV_PATH"

# Verificar que el entorno virtual existe
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    log "❌ ERROR: No se encuentra el entorno virtual en $VENV_PATH"
    exit 1
fi

source "$VENV_PATH/bin/activate"
log "✅ Entorno virtual activado"

# Verificar que el script existe
if [ ! -f "$SCRIPT_PATH" ]; then
    log "❌ ERROR: No se encuentra el script en $SCRIPT_PATH"
    exit 1
fi

log "Ejecutando generador V3 funcional..."
log "Comando: $PYTHON_PATH $SCRIPT_PATH"

# Ejecutar el generador V3
$PYTHON_PATH "$SCRIPT_PATH" >> "$LOG_PATH" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "✅ Generación automática completada exitosamente"
else
    log "❌ Error en la generación automática (código de salida: $EXIT_CODE)"
fi

log "=== FIN GENERACIÓN AUTOMÁTICA MENSUAL ==="
echo "" >> "$LOG_PATH"

deactivate
log "Entorno virtual desactivado"
