-- Script para migrar de ENUMs a VARCHAR con CHECK constraints
-- Esto elimina las dependencias complejas de los enums de PostgreSQL

BEGIN;

-- 1. Cambiar tipo_movimiento_enum a VARCHAR
-- Primero crear una nueva columna temporal
ALTER TABLE registro_financiero_apartamento 
ADD COLUMN tipo_movimiento_new VARCHAR(10);

-- Copiar datos convirtiendo enum a string
UPDATE registro_financiero_apartamento 
SET tipo_movimiento_new = tipo_movimiento::text;

-- Eliminar la columna original
ALTER TABLE registro_financiero_apartamento 
DROP COLUMN tipo_movimiento;

-- Renombrar la nueva columna
ALTER TABLE registro_financiero_apartamento 
RENAME COLUMN tipo_movimiento_new TO tipo_movimiento;

-- Agregar constraint para validar valores
ALTER TABLE registro_financiero_apartamento 
ADD CONSTRAINT check_tipo_movimiento 
CHECK (tipo_movimiento IN ('DEBITO', 'CREDITO'));

-- Hacer NOT NULL
ALTER TABLE registro_financiero_apartamento 
ALTER COLUMN tipo_movimiento SET NOT NULL;

-- 2. Hacer lo mismo para rol_usuario_enum en la tabla usuario
ALTER TABLE usuario 
ADD COLUMN rol_new VARCHAR(20);

UPDATE usuario 
SET rol_new = rol::text;

ALTER TABLE usuario 
DROP COLUMN rol;

ALTER TABLE usuario 
RENAME COLUMN rol_new TO rol;

ALTER TABLE usuario 
ADD CONSTRAINT check_rol_usuario 
CHECK (rol IN ('ADMIN', 'PROPIETARIO'));

ALTER TABLE usuario 
ALTER COLUMN rol SET NOT NULL;

-- 3. Para tipo_item_presupuesto_enum (si existe)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'item_presupuesto' 
               AND column_name = 'tipo_item') THEN
        
        ALTER TABLE item_presupuesto 
        ADD COLUMN tipo_item_new VARCHAR(10);
        
        UPDATE item_presupuesto 
        SET tipo_item_new = tipo_item::text;
        
        ALTER TABLE item_presupuesto 
        DROP COLUMN tipo_item;
        
        ALTER TABLE item_presupuesto 
        RENAME COLUMN tipo_item_new TO tipo_item;
        
        ALTER TABLE item_presupuesto 
        ADD CONSTRAINT check_tipo_item_presupuesto 
        CHECK (tipo_item IN ('INGRESO', 'GASTO'));
        
        ALTER TABLE item_presupuesto 
        ALTER COLUMN tipo_item SET NOT NULL;
    END IF;
END $$;

-- 4. Eliminar los tipos ENUM (opcional, pueden quedarse sin usar)
-- DROP TYPE IF EXISTS tipo_movimiento_enum CASCADE;
-- DROP TYPE IF EXISTS rol_usuario_enum CASCADE;
-- DROP TYPE IF EXISTS tipo_item_presupuesto_enum CASCADE;

COMMIT;
