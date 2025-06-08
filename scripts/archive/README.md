# Scripts Archivados - Versiones Anteriores

Este directorio contiene versiones anteriores del sistema de generación automática que presentaron problemas técnicos y fueron reemplazadas por la **versión V3 funcional**.

## Archivos Archivados

### `generador_automatico_mensual.py` (V1)
- **Problema**: Incompatibilidad con enums de SQLModel/PostgreSQL
- **Estado**: Obsoleto - Reemplazado por V3
- **Fecha de archivo**: Junio 8, 2025

### `generador_v2_sql_directo.py` (V2)
- **Problema**: Problemas con SQLModel API y binding de parámetros
- **Estado**: Obsoleto - Reemplazado por V3  
- **Fecha de archivo**: Junio 8, 2025

### `generador_v2_mejorado.py` (V2 Mejorado)
- **Problema**: Archivo vacío - Creación fallida
- **Estado**: Sin implementar
- **Fecha de archivo**: Junio 8, 2025

## Versión Actual

**✅ Usar**: `../generador_v3_funcional.py` - **VERSIÓN FUNCIONAL Y ESTABLE**

## Historial de Desarrollo

1. **V1**: Intento inicial con SQLModel puro - Falló por problemas de enum
2. **V2**: Intento con SQL directo - Falló por problemas de API 
3. **V3**: Solución funcional con string formatting - ✅ **ÉXITO**

## Notas

Estos archivos se mantienen únicamente para referencia histórica. 
**NO USAR** para producción - pueden causar errores en la base de datos.

Para cualquier desarrollo nuevo, partir de la **versión V3** estable.
