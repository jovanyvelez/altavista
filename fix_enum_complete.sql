-- Script para verificar y corregir completamente los problemas de enum
-- Diagnóstico y corrección completa

-- 1. Verificar estado actual de todas las columnas relacionadas
SELECT 
    table_name, 
    column_name, 
    data_type, 
    udt_name,
    character_maximum_length,
    is_nullable
FROM information_schema.columns 
WHERE (table_name = 'registro_financiero_apartamento' AND column_name = 'tipo_movimiento')
   OR (table_name = 'usuario' AND column_name = 'rol')
ORDER BY table_name, column_name;

-- 2. Verificar si hay múltiples columnas tipo_movimiento
SELECT 
    table_name,
    column_name,
    ordinal_position,
    data_type,
    udt_name
FROM information_schema.columns 
WHERE table_name = 'registro_financiero_apartamento'
AND column_name LIKE '%tipo_movimiento%'
ORDER BY ordinal_position;

-- 3. Verificar tipos ENUM existentes
SELECT 
    t.typname as enum_name,
    e.enumlabel as enum_value
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid  
WHERE t.typname LIKE '%movimiento%' OR t.typname LIKE '%rol%'
ORDER BY t.typname, e.enumsortorder;

-- 4. Verificar constraints existentes
SELECT 
    tc.constraint_name,
    tc.table_name,
    tc.constraint_type,
    cc.check_clause
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.check_constraints cc ON tc.constraint_name = cc.constraint_name
WHERE tc.table_name IN ('registro_financiero_apartamento', 'usuario')
AND (tc.constraint_type = 'CHECK' OR tc.constraint_name LIKE '%tipo_movimiento%' OR tc.constraint_name LIKE '%rol%')
ORDER BY tc.table_name, tc.constraint_name;

-- 5. Verificar datos existentes en registro_financiero_apartamento
SELECT 
    tipo_movimiento,
    COUNT(*) as cantidad,
    MIN(fecha_registro) as primera_fecha,
    MAX(fecha_registro) as ultima_fecha
FROM registro_financiero_apartamento 
GROUP BY tipo_movimiento
ORDER BY cantidad DESC;

-- Si encuentra problemas, ejecutar correcciones:

-- CORRECCIÓN 1: Si sigue existiendo enum tipo_movimiento_enum
DO $$
BEGIN
    -- Verificar si la columna sigue siendo enum
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'registro_financiero_apartamento' 
        AND column_name = 'tipo_movimiento'
        AND (udt_name LIKE '%enum%' OR data_type = 'USER-DEFINED')
    ) THEN
        RAISE NOTICE 'CORRECCIÓN: Columna tipo_movimiento sigue siendo enum, convirtiendo a VARCHAR...';
        
        -- Paso 1: Crear columna temporal
        ALTER TABLE registro_financiero_apartamento 
        ADD COLUMN tipo_movimiento_temp VARCHAR(10);
        
        -- Paso 2: Migrar datos convirtiendo a texto y normalizando valores
        UPDATE registro_financiero_apartamento 
        SET tipo_movimiento_temp = CASE 
            WHEN tipo_movimiento::text = 'DEBITO' THEN 'DEBITO'
            WHEN tipo_movimiento::text = 'CREDITO' THEN 'CREDITO'
            WHEN tipo_movimiento::text = 'CREDIT' THEN 'CREDITO'
            WHEN tipo_movimiento::text = 'DEBIT' THEN 'DEBITO'
            ELSE tipo_movimiento::text
        END;
        
        -- Paso 3: Eliminar columna original
        ALTER TABLE registro_financiero_apartamento 
        DROP COLUMN tipo_movimiento CASCADE;
        
        -- Paso 4: Renombrar columna temporal
        ALTER TABLE registro_financiero_apartamento 
        RENAME COLUMN tipo_movimiento_temp TO tipo_movimiento;
        
        -- Paso 5: Agregar constraint
        ALTER TABLE registro_financiero_apartamento 
        ADD CONSTRAINT check_tipo_movimiento 
        CHECK (tipo_movimiento IN ('DEBITO', 'CREDITO'));
        
        -- Paso 6: NOT NULL
        ALTER TABLE registro_financiero_apartamento 
        ALTER COLUMN tipo_movimiento SET NOT NULL;
        
        RAISE NOTICE 'Columna tipo_movimiento convertida a VARCHAR exitosamente';
    ELSE
        RAISE NOTICE 'Columna tipo_movimiento ya es VARCHAR o no existe';
    END IF;
END $$;

-- CORRECCIÓN 2: Limpiar datos incorrectos si existen
UPDATE registro_financiero_apartamento 
SET tipo_movimiento = CASE 
    WHEN tipo_movimiento = 'CREDIT' THEN 'CREDITO'
    WHEN tipo_movimiento = 'DEBIT' THEN 'DEBITO'
    ELSE tipo_movimiento
END
WHERE tipo_movimiento IN ('CREDIT', 'DEBIT');

-- VERIFICACIÓN FINAL
SELECT 'VERIFICACIÓN FINAL:' as status;

SELECT 
    table_name, 
    column_name, 
    data_type, 
    udt_name,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'registro_financiero_apartamento' 
AND column_name = 'tipo_movimiento';

SELECT 
    tipo_movimiento,
    COUNT(*) as cantidad
FROM registro_financiero_apartamento 
GROUP BY tipo_movimiento;

SELECT 'Migración completada correctamente' as resultado;
