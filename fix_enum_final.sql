-- ============================================================================
-- SCRIPT FINAL DE LIMPIEZA DE ENUMS
-- ============================================================================

-- 1. Verificar el estado actual
SELECT 'ESTADO ACTUAL DE ENUMS' as info;

SELECT 
    t.typname as enum_name,
    array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid 
WHERE t.typtype = 'e' 
  AND t.typname LIKE '%movimiento%'
GROUP BY t.typname
ORDER BY t.typname;

-- 2. Verificar restricciones que podrían estar usando enums
SELECT 'RESTRICCIONES ACTIVAS' as info;

SELECT 
    conname as constraint_name,
    conrelid::regclass as table_name,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint 
WHERE pg_get_constraintdef(oid) LIKE '%tipomovimientoenum%'
   OR pg_get_constraintdef(oid) LIKE '%CARGO%'
   OR pg_get_constraintdef(oid) LIKE '%ABONO%';

-- 3. Eliminar restricciones que usen el enum viejo
DO $$
DECLARE
    constraint_record RECORD;
BEGIN
    FOR constraint_record IN 
        SELECT 
            conname as constraint_name,
            conrelid::regclass as table_name
        FROM pg_constraint 
        WHERE pg_get_constraintdef(oid) LIKE '%tipomovimientoenum%'
           OR pg_get_constraintdef(oid) LIKE '%CARGO%'
           OR pg_get_constraintdef(oid) LIKE '%ABONO%'
    LOOP
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT IF EXISTS %s', 
            constraint_record.table_name, 
            constraint_record.constraint_name);
        RAISE NOTICE 'Eliminada restricción % de tabla %', 
            constraint_record.constraint_name, 
            constraint_record.table_name;
    END LOOP;
END $$;

-- 4. Asegurar que las columnas sean VARCHAR con restricciones correctas
ALTER TABLE registro_financiero_apartamento 
    DROP CONSTRAINT IF EXISTS registro_financiero_apartamento_tipo_movimiento_check;

ALTER TABLE registro_financiero_apartamento 
    ADD CONSTRAINT registro_financiero_apartamento_tipo_movimiento_check 
    CHECK (tipo_movimiento IN ('DEBITO', 'CREDITO'));

-- 5. Actualizar datos existentes si es necesario
UPDATE registro_financiero_apartamento 
SET tipo_movimiento = 'DEBITO' 
WHERE tipo_movimiento IN ('CARGO', 'DEBIT');

UPDATE registro_financiero_apartamento 
SET tipo_movimiento = 'CREDITO' 
WHERE tipo_movimiento IN ('ABONO', 'CREDIT');

-- 6. Eliminar enums no utilizados
DROP TYPE IF EXISTS tipomovimientoenum CASCADE;
DROP TYPE IF EXISTS rolusuarioenum CASCADE;
DROP TYPE IF EXISTS tipoitempresupuestoenum CASCADE;

-- 7. Verificar el resultado final
SELECT 'RESULTADO FINAL' as info;

SELECT 
    table_name,
    column_name,
    data_type,
    udt_name
FROM information_schema.columns 
WHERE table_name IN ('registro_financiero_apartamento', 'usuario', 'item_presupuesto')
  AND column_name IN ('tipo_movimiento', 'rol', 'tipo_item')
ORDER BY table_name, column_name;

SELECT 'ENUMS RESTANTES' as info;

SELECT 
    t.typname as enum_name,
    array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid 
WHERE t.typtype = 'e' 
  AND t.typname LIKE '%movimiento%'
GROUP BY t.typname
ORDER BY t.typname;
