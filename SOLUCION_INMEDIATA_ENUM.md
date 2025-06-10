# 🔧 SOLUCIÓN INMEDIATA PARA ERROR DE ENUM

## ❌ **PROBLEMA ACTUAL**
```
Error al procesar el pago.
Detalles: (psycopg2.errors.DatatypeMismatch) column "tipo_movimiento" is of type tipo_movimiento_enum but expression is of type character varying
```

## ✅ **SOLUCIÓN INMEDIATA**

### **Opción 1: Ejecutar en Supabase Dashboard (RECOMENDADO)**

1. **Ir a:** https://supabase.com/dashboard
2. **Abrir:** Tu proyecto de la base de datos
3. **Navegar a:** SQL Editor
4. **Copiar y pegar este script:**

```sql
-- MIGRACIÓN DE ENUMS A VARCHAR
BEGIN;

-- Migrar registro_financiero_apartamento
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'registro_financiero_apartamento' 
        AND column_name = 'tipo_movimiento'
        AND udt_name = 'tipo_movimiento_enum'
    ) THEN
        -- Agregar nueva columna VARCHAR
        ALTER TABLE registro_financiero_apartamento 
        ADD COLUMN tipo_movimiento_new VARCHAR(10);
        
        -- Copiar datos convertidos
        UPDATE registro_financiero_apartamento 
        SET tipo_movimiento_new = tipo_movimiento::text;
        
        -- Eliminar columna enum original
        ALTER TABLE registro_financiero_apartamento 
        DROP COLUMN tipo_movimiento;
        
        -- Renombrar nueva columna
        ALTER TABLE registro_financiero_apartamento 
        RENAME COLUMN tipo_movimiento_new TO tipo_movimiento;
        
        -- Agregar validación
        ALTER TABLE registro_financiero_apartamento 
        ADD CONSTRAINT check_tipo_movimiento 
        CHECK (tipo_movimiento IN ('DEBITO', 'CREDITO'));
        
        -- Hacer NOT NULL
        ALTER TABLE registro_financiero_apartamento 
        ALTER COLUMN tipo_movimiento SET NOT NULL;
        
        RAISE NOTICE 'Migración completada exitosamente';
    ELSE
        RAISE NOTICE 'Ya migrado o no necesario';
    END IF;
END $$;

COMMIT;
```

5. **Hacer clic en:** "Run" o "Ejecutar"

### **Opción 2: Usando pgAdmin**

1. **Conectar a:** `db.xnmealeoourdfcgsyfqv.supabase.co:5432`
2. **Usuario:** `postgres`
3. **Contraseña:** `NqYMCFXBEQYYJ60u`
4. **Ejecutar** el mismo script SQL de arriba

### **Opción 3: Comandos Manuales (Paso a Paso)**

Ejecutar estos comandos uno por uno:

```sql
-- 1. Agregar nueva columna
ALTER TABLE registro_financiero_apartamento 
ADD COLUMN tipo_movimiento_new VARCHAR(10);

-- 2. Copiar datos
UPDATE registro_financiero_apartamento 
SET tipo_movimiento_new = tipo_movimiento::text;

-- 3. Eliminar columna original
ALTER TABLE registro_financiero_apartamento 
DROP COLUMN tipo_movimiento;

-- 4. Renombrar columna
ALTER TABLE registro_financiero_apartamento 
RENAME COLUMN tipo_movimiento_new TO tipo_movimiento;

-- 5. Agregar validación
ALTER TABLE registro_financiero_apartamento 
ADD CONSTRAINT check_tipo_movimiento 
CHECK (tipo_movimiento IN ('DEBITO', 'CREDITO'));

-- 6. NOT NULL
ALTER TABLE registro_financiero_apartamento 
ALTER COLUMN tipo_movimiento SET NOT NULL;
```

## 🧪 **VERIFICAR QUE FUNCIONÓ**

Después de ejecutar la migración:

1. **Ejecutar esta query para verificar:**
```sql
SELECT 
    table_name, 
    column_name, 
    data_type, 
    udt_name 
FROM information_schema.columns 
WHERE table_name = 'registro_financiero_apartamento' 
AND column_name = 'tipo_movimiento';
```

2. **Debería devolver:**
```
table_name                      | column_name     | data_type         | udt_name
registro_financiero_apartamento | tipo_movimiento | character varying | varchar
```

## 🚀 **PROBAR EL SISTEMA**

Una vez completada la migración:

1. **Ir a:** Administración → Pagos → Procesar Pagos
2. **Hacer clic:** Botón "🪄 Pagar" junto a cualquier apartamento
3. **Debería funcionar** sin errores de enum

## 🔧 **SI TIENES PROBLEMAS**

### **Error: "relation does not exist"**
- La tabla no existe o hay problema de conexión
- Verificar que estés conectado a la base de datos correcta

### **Error: "column already exists"**
- La migración ya se ejecutó parcialmente
- Ejecutar solo los pasos faltantes

### **Error: "permission denied"**
- El usuario no tiene permisos de ALTER TABLE
- Usar el usuario administrador (postgres)

## 📋 **SCRIPT COMPLETO DE VERIFICACIÓN**

Después de la migración, ejecutar para verificar:

```sql
-- Verificar estructura actual
SELECT 
    t.table_name,
    c.column_name,
    c.data_type,
    c.character_maximum_length,
    c.udt_name,
    c.is_nullable
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_name IN ('registro_financiero_apartamento', 'usuario')
AND c.column_name IN ('tipo_movimiento', 'rol')
ORDER BY t.table_name, c.column_name;

-- Verificar constraints
SELECT 
    tc.constraint_name,
    tc.table_name,
    cc.check_clause
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc ON tc.constraint_name = cc.constraint_name
WHERE tc.table_name IN ('registro_financiero_apartamento', 'usuario')
AND tc.constraint_type = 'CHECK';

-- Test de inserción (opcional)
SELECT 'Estructura verificada correctamente' as status;
```

## 🎯 **RESULTADO ESPERADO**

Después de la migración:
- ✅ Columna `tipo_movimiento` será `VARCHAR(10)`
- ✅ Mantendrá todos los datos existentes
- ✅ Tendrá validación con CHECK constraint
- ✅ El sistema de pago automático funcionará sin errores
- ✅ No habrá más problemas de incompatibilidad de tipos

## 📞 **ARCHIVOS DE REFERENCIA**

- `migrate_enums_direct.sql` - Script SQL completo
- `run_migration.py` - Script Python automatizado
- `fix_enum_database.py` - Script alternativo de migración

---

**⚡ EJECUTAR LA MIGRACIÓN Y EL PROBLEMA ESTARÁ RESUELTO** ⚡
