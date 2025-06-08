# Configuración de Cron Job para Generación Automática de Cargos
# ================================================================

## INSTALACIÓN DEL CRON JOB

### 1. Editar el crontab del usuario:
```bash
crontab -e
```

### 2. Agregar la siguiente línea al final del archivo:
```
# Generación automática de cargos el día 1 de cada mes a las 02:00 AM
0 2 1 * * /home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio/scripts/cron_config.sh
```

### 3. Verificar que el cron job fue instalado correctamente:
```bash
crontab -l
```

## EXPLICACIÓN DEL HORARIO

- `0 2 1 * *` significa:
  - `0`: minuto 0
  - `2`: hora 2 (02:00 AM)
  - `1`: día 1 del mes
  - `*`: cualquier mes
  - `*`: cualquier día de la semana

## LOGS Y MONITOREO

- **Log principal**: `/home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio/logs/cron_generacion_automatica.log`
- **Log del generador**: `/home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio/logs/generacion_automatica.log`

## VERIFICACIÓN MANUAL

Para probar manualmente el script antes de configurar cron:
```bash
cd /home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio
./scripts/cron_config.sh
```

## CONFIGURACIONES ALTERNATIVAS

### Para pruebas (cada 5 minutos):
```
*/5 * * * * /home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio/scripts/cron_config.sh
```

### Para ejecutar semanalmente (domingos a las 02:00):
```
0 2 * * 0 /home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio/scripts/cron_config.sh
```

### Para ejecutar diariamente a las 03:00:
```
0 3 * * * /home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio/scripts/cron_config.sh
```

## TROUBLESHOOTING

### Ver logs de cron del sistema:
```bash
sudo tail -f /var/log/syslog | grep CRON
```

### Ver logs específicos de la aplicación:
```bash
tail -f /home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio/logs/cron_generacion_automatica.log
```

### Verificar que el entorno virtual funciona:
```bash
source /home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio/.venv/bin/activate
python /home/jovany/Documentos/DESARROLLO/python/proyecto_pia_edificio/scripts/generador_v3_funcional.py
```
