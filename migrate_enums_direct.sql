-- Script SQL directo para migrar enums a VARCHAR
-- Ejecutar este script en la consola de PostgreSQL o pgAdmin

BEGIN;

-- Verificar estado actual
SELECT 
    table_name, 
    column_name, 
    data_type, 
    udt_name 
FROM information_schema.columns 
WHERE (table_name = 'registro_financiero_apartamento' AND column_name = 'tipo_movimiento')
   OR (table_name = 'usuario' AND column_name = 'rol');

-- Migrar registro_financiero_apartamento
-- Solo ejecutar si tipo_movimiento es tipo_movimiento_enum
DO $$
BEGIN
    -- Verificar si necesita migración
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'registro_financiero_apartamento' 
        AND column_name = 'tipo_movimiento'
        AND udt_name = 'tipo_movimiento_enum'
    ) THEN
        RAISE NOTICE 'Migrando registro_financiero_apartamento.tipo_movimiento...';
        
        -- Paso 1: Agregar nueva columna
        ALTER TABLE registro_financiero_apartamento 
        ADD COLUMN tipo_movimiento_new VARCHAR(10);
        
        -- Paso 2: Copiar datos
        UPDATE registro_financiero_apartamento 
        SET tipo_movimiento_new = tipo_movimiento::text;
        
        -- Paso 3: Eliminar columna original
        ALTER TABLE registro_financiero_apartamento 
        DROP COLUMN tipo_movimiento;
        
        -- Paso 4: Renombrar nueva columna
        ALTER TABLE registro_financiero_apartamento 
        RENAME COLUMN tipo_movimiento_new TO tipo_movimiento;
        
        -- Paso 5: Agregar constraint
        ALTER TABLE registro_financiero_apartamento 
        ADD CONSTRAINT check_tipo_movimiento 
        CHECK (tipo_movimiento IN ('DEBITO', 'CREDITO'));
        
        -- Paso 6: NOT NULL
        ALTER TABLE registro_financiero_apartamento 
        ALTER COLUMN tipo_movimiento SET NOT NULL;
        
        RAISE NOTICE 'Migración de registro_financiero_apartamento completada';
    ELSE
        RAISE NOTICE 'registro_financiero_apartamento.tipo_movimiento ya migrado o no es enum';
    END IF;
END $$;

-- Migrar usuario
-- Solo ejecutar si rol es rol_usuario_enum  
DO $$
BEGIN
    -- Verificar si necesita migración
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'usuario' 
        AND column_name = 'rol'
        AND udt_name = 'rol_usuario_enum'
    ) THEN
        RAISE NOTICE 'Migrando usuario.rol...';
        
        -- Paso 1: Agregar nueva columna
        ALTER TABLE usuario 
        ADD COLUMN rol_new VARCHAR(20);
        
        -- Paso 2: Copiar datos
        UPDATE usuario 
        SET rol_new = rol::text;
        
        -- Paso 3: Eliminar columna original
        ALTER TABLE usuario 
        DROP COLUMN rol;
        
        -- Paso 4: Renombrar nueva columna
        ALTER TABLE usuario 
        RENAME COLUMN rol_new TO rol;
        
        -- Paso 5: Agregar constraint (incluir valores legacy)
        ALTER TABLE usuario 
        ADD CONSTRAINT check_rol_usuario 
        CHECK (rol IN ('ADMIN', 'PROPIETARIO', 'administrador', 'propietario_consulta'));
        
        -- Paso 6: NOT NULL
        ALTER TABLE usuario 
        ALTER COLUMN rol SET NOT NULL;
        
        RAISE NOTICE 'Migración de usuario completada';
    ELSE
        RAISE NOTICE 'usuario.rol ya migrado o no es enum';
    END IF;
END $$;

-- Verificar resultado final
SELECT 
    table_name, 
    column_name, 
    data_type, 
    character_maximum_length,
    udt_name 
FROM information_schema.columns 
WHERE (table_name = 'registro_financiero_apartamento' AND column_name = 'tipo_movimiento')
   OR (table_name = 'usuario' AND column_name = 'rol')
ORDER BY table_name, column_name;

-- Verificar constraints creados
SELECT 
    conname as constraint_name,
    conrelid::regclass as table_name
FROM pg_constraint 
WHERE contype = 'c' 
AND conname LIKE 'check_%tipo_%' OR conname LIKE 'check_%rol_%'
ORDER BY table_name;

COMMIT;

-- Test de inserción (opcional, comentado por seguridad)
/*
-- Probar inserción en registro_financiero_apartamento
INSERT INTO registro_financiero_apartamento 
(apartamento_id, tipo_movimiento, monto, fecha_efectiva, concepto_id, fecha_registro)
VALUES (1, 'CREDITO', 1000.00, '2025-06-09', 1, NOW())
RETURNING id;

-- Eliminar el registro de prueba
DELETE FROM registro_financiero_apartamento WHERE id = (SELECT MAX(id) FROM registro_financiero_apartamento);
*/
