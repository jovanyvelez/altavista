¡Excelente! Empezar directamente con PostgreSQL es una buena decisión para evitar sorpresas en la migración.
Vamos a ajustar la tabla de presupuesto para que pueda manejar tanto ingresos como gastos presupuestados y luego te proporcionaré el DDL para PostgreSQL.
Modificación Clave para el Presupuesto:
La tabla ItemPresupuesto necesitará un campo para distinguir si es un ítem de ingreso presupuestado o un gasto presupuestado.
ItemPresupuesto:
id: PK
presupuesto_anual_id: FK(PresupuestoAnual.id)
concepto_id: FK(Concepto.id) (puede ser un concepto de ingreso o de gasto)
mes: int (1-12)
monto_presupuestado: float
tipo_item: Enum("INGRESO", "GASTO") <-- Nuevo campo
Con esto, puedes presupuestar "Recaudo Cuotas Ordinarias" como un INGRESO y "Mantenimiento Ascensor" como un GASTO.
Diseño de Tablas en PostgreSQL (DDL):
A continuación, el DDL para crear las tablas en PostgreSQL. He usado BIGSERIAL para las claves primarias, DECIMAL para valores monetarios, y VARCHAR con longitudes razonables. También he añadido algunos índices que podrían ser útiles.
-- Crear ENUM types primero (si no existen)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rol_usuario_enum') THEN
        CREATE TYPE rol_usuario_enum AS ENUM ('administrador', 'propietario_consulta');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_movimiento_enum') THEN
        CREATE TYPE tipo_movimiento_enum AS ENUM ('DEBITO', 'CREDITO');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_item_presupuesto_enum') THEN
        CREATE TYPE tipo_item_presupuesto_enum AS ENUM ('INGRESO', 'GASTO');
    END IF;
END$$;


-- Tabla: Propietario
CREATE TABLE IF NOT EXISTS propietario (
    id BIGSERIAL PRIMARY KEY,
    nombre_completo VARCHAR(255) NOT NULL,
    documento_identidad VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    telefono VARCHAR(50),
    datos_adicionales TEXT,
    fecha_creacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_actualizacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Tabla: Apartamento
CREATE TABLE IF NOT EXISTS apartamento (
    id BIGSERIAL PRIMARY KEY,
    identificador VARCHAR(50) UNIQUE NOT NULL, -- Ej: "Apto 101", "Bloque A - 203"
    coeficiente_copropiedad DECIMAL(8, 6) NOT NULL, -- Ej: 0.012500 para 1.25%
    propietario_id BIGINT REFERENCES propietario(id) ON DELETE SET NULL, -- Un apto puede no tener propietario asignado temporalmente
    fecha_creacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_actualizacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_apartamento_propietario_id ON apartamento(propietario_id);

-- Tabla: Concepto (para ingresos y gastos)
CREATE TABLE IF NOT EXISTS concepto (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(150) UNIQUE NOT NULL,
    -- True si es un concepto que típicamente es un ingreso para la comunidad (Ej: Cuotas, Intereses)
    -- False si es un concepto que típicamente es un gasto (Ej: Mantenimiento, Servicios)
    es_ingreso_tipico BOOLEAN NOT NULL DEFAULT FALSE,
    -- True si este concepto suele aparecer en el presupuesto anual (especialmente gastos)
    es_recurrente_presupuesto BOOLEAN NOT NULL DEFAULT TRUE,
    descripcion TEXT
);

-- Tabla: PresupuestoAnual
CREATE TABLE IF NOT EXISTS presupuesto_anual (
    id BIGSERIAL PRIMARY KEY,
    año INTEGER UNIQUE NOT NULL,
    descripcion TEXT,
    fecha_creacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_actualizacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Tabla: ItemPresupuesto (para ingresos y gastos presupuestados)
CREATE TABLE IF NOT EXISTS item_presupuesto (
    id BIGSERIAL PRIMARY KEY,
    presupuesto_anual_id BIGINT NOT NULL REFERENCES presupuesto_anual(id) ON DELETE CASCADE,
    concepto_id BIGINT NOT NULL REFERENCES concepto(id) ON DELETE RESTRICT,
    mes INTEGER NOT NULL CHECK (mes >= 1 AND mes <= 12),
    monto_presupuestado DECIMAL(12, 2) NOT NULL,
    tipo_item tipo_item_presupuesto_enum NOT NULL, -- 'INGRESO' o 'GASTO'
    UNIQUE (presupuesto_anual_id, concepto_id, mes, tipo_item) -- Asegura que no haya duplicados
);
CREATE INDEX IF NOT EXISTS idx_item_presupuesto_anual_id ON item_presupuesto(presupuesto_anual_id);
CREATE INDEX IF NOT EXISTS idx_item_presupuesto_concepto_id ON item_presupuesto(concepto_id);

-- Tabla: CuotaConfiguracion (valor de la cuota ordinaria mensual por apartamento y año)
CREATE TABLE IF NOT EXISTS cuota_configuracion (
    id BIGSERIAL PRIMARY KEY,
    apartamento_id BIGINT NOT NULL REFERENCES apartamento(id) ON DELETE CASCADE,
    año INTEGER NOT NULL,
    monto_cuota_ordinaria_mensual DECIMAL(12, 2) NOT NULL,
    UNIQUE (apartamento_id, año)
);
CREATE INDEX IF NOT EXISTS idx_cuota_configuracion_apartamento_id ON cuota_configuracion(apartamento_id);

-- Tabla: TasaInteresMora
CREATE TABLE IF NOT EXISTS tasa_interes_mora (
    id BIGSERIAL PRIMARY KEY,
    año INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes >= 1 AND mes <= 12),
    tasa_interes_mensual DECIMAL(5, 4) NOT NULL, -- Ej: 0.0150 para 1.5%
    UNIQUE (año, mes)
);

-- Tabla: RegistroFinancieroApartamento (Estado de cuenta del apartamento: débitos y créditos)
CREATE TABLE IF NOT EXISTS registro_financiero_apartamento (
    id BIGSERIAL PRIMARY KEY,
    apartamento_id BIGINT NOT NULL REFERENCES apartamento(id) ON DELETE CASCADE,
    fecha_registro TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Fecha de la transacción en el sistema
    fecha_efectiva DATE NOT NULL, -- Fecha a la que corresponde el movimiento (ej. pago cuota de enero)
    concepto_id BIGINT NOT NULL REFERENCES concepto(id) ON DELETE RESTRICT,
    descripcion_adicional TEXT,
    tipo_movimiento tipo_movimiento_enum NOT NULL, -- 'DEBITO' (aumenta deuda apto) o 'CREDITO' (disminuye deuda/pago)
    monto DECIMAL(12, 2) NOT NULL,
    mes_aplicable INTEGER CHECK (mes_aplicable IS NULL OR (mes_aplicable >= 1 AND mes_aplicable <= 12)), -- Mes al que aplica el movimiento (ej. cuota de enero)
    año_aplicable INTEGER, -- Año al que aplica el movimiento
    documento_soporte_path VARCHAR(512), -- Ruta al archivo digital de soporte
    referencia_pago VARCHAR(100) -- Ej: Nro de consignación, ID de transacción
);
CREATE INDEX IF NOT EXISTS idx_rfa_apartamento_id ON registro_financiero_apartamento(apartamento_id);
CREATE INDEX IF NOT EXISTS idx_rfa_fecha_efectiva ON registro_financiero_apartamento(fecha_efectiva);
CREATE INDEX IF NOT EXISTS idx_rfa_concepto_id ON registro_financiero_apartamento(concepto_id);
CREATE INDEX IF NOT EXISTS idx_rfa_mes_año_aplicable ON registro_financiero_apartamento(año_aplicable, mes_aplicable);


-- Tabla: GastoComunidad (Gastos generales de la administración)
CREATE TABLE IF NOT EXISTS gasto_comunidad (
    id BIGSERIAL PRIMARY KEY,
    fecha_gasto DATE NOT NULL,
    concepto_id BIGINT NOT NULL REFERENCES concepto(id) ON DELETE RESTRICT,
    descripcion_adicional TEXT,
    monto DECIMAL(12, 2) NOT NULL,
    documento_soporte_path VARCHAR(512), -- Ruta a la factura o documento
    -- Opcional: para vincular con el año presupuestario y el mes para comparativas
    presupuesto_anual_id BIGINT REFERENCES presupuesto_anual(id) ON DELETE SET NULL,
    mes_gasto INTEGER CHECK (mes_gasto >= 1 AND mes_gasto <= 12),
    año_gasto INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_gasto_comunidad_fecha ON gasto_comunidad(fecha_gasto);
CREATE INDEX IF NOT EXISTS idx_gasto_comunidad_concepto_id ON gasto_comunidad(concepto_id);
CREATE INDEX IF NOT EXISTS idx_gasto_comunidad_presupuesto_id ON gasto_comunidad(presupuesto_anual_id);


-- Tabla: Usuario (Para autenticación y roles)
CREATE TABLE IF NOT EXISTS usuario (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(255),
    rol rol_usuario_enum NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    propietario_id BIGINT REFERENCES propietario(id) ON DELETE SET NULL, -- Si el rol es 'propietario_consulta'
    fecha_creacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_actualizacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_usuario_propietario_rol CHECK (
        (rol = 'propietario_consulta' AND propietario_id IS NOT NULL) OR
        (rol != 'propietario_consulta') -- propietario_id puede ser NULL si no es 'propietario_consulta'
    )
);
CREATE INDEX IF NOT EXISTS idx_usuario_propietario_id ON usuario(propietario_id);

-- Funciones para actualizar 'fecha_actualizacion' (opcional, pero buena práctica)
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.fecha_actualizacion = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar triggers a tablas que tienen 'fecha_actualizacion'
DO $$
DECLARE
    t_name TEXT;
BEGIN
    FOR t_name IN SELECT table_name FROM information_schema.columns WHERE column_name = 'fecha_actualizacion' AND table_schema = current_schema()
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS set_timestamp ON %I;
            CREATE TRIGGER set_timestamp
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION trigger_set_timestamp();
        ', t_name, t_name);
    END LOOP;
END$$;
Use code with caution.

SQL
Consideraciones Clave de este DDL:
ENUM Types: Se crean tipos ENUM para rol_usuario_enum, tipo_movimiento_enum, y tipo_item_presupuesto_enum para restringir los valores de esas columnas. El DO $$ ... END$$; bloque asegura que solo se creen si no existen.
BIGSERIAL: Para claves primarias auto-incrementales.
DECIMAL(precision, scale): Para valores monetarios, por ejemplo DECIMAL(12, 2) permite hasta 9,999,999,999.99. Ajusta la precisión según necesites. Para coeficiente_copropiedad usé DECIMAL(8, 6) asumiendo hasta 6 decimales de precisión para el coeficiente (ej. 0.012345).
TIMESTAMPTZ: Para campos de fecha y hora que incluyen la zona horaria. DEFAULT CURRENT_TIMESTAMP es útil para fecha_creacion y fecha_actualizacion.
REFERENCES ... ON DELETE ...:
ON DELETE CASCADE: Si se borra el principal, se borran los dependientes (ej. si borras un apartamento, se borran sus cuota_configuracion y sus registro_financiero_apartamento).
ON DELETE SET NULL: Si se borra el principal, la FK en el dependiente se pone a NULL (ej. si borras un propietario, el apartamento.propietario_id se vuelve NULL).
ON DELETE RESTRICT: Impide borrar el principal si hay registros dependientes (ej. no puedes borrar un concepto si está siendo usado en item_presupuesto o registro_financiero_apartamento).
UNIQUE Constraints: Para asegurar la unicidad donde es necesario (ej. propietario.documento_identidad, apartamento.identificador, presupuesto_anual.año, etc.).
CHECK Constraints: Para validar rangos (ej. mes entre 1 y 12).
Índices (CREATE INDEX): Se crean índices en columnas de clave foránea y otras columnas que probablemente se usen en filtros (WHERE) o JOINs para mejorar el rendimiento de las consultas.
Trigger trigger_set_timestamp: Una función y un trigger genérico para actualizar automáticamente el campo fecha_actualizacion en cualquier tabla que lo tenga cuando una fila es actualizada.
Presupuesto: La tabla item_presupuesto ahora incluye tipo_item tipo_item_presupuesto_enum NOT NULL y la restricción UNIQUE (presupuesto_anual_id, concepto_id, mes, tipo_item) para manejar correctamente ingresos y gastos presupuestados.
Constraint fk_usuario_propietario_rol en usuario: Un CHECK constraint para asegurar que si el rol es 'propietario_consulta', entonces propietario_id debe tener un valor.
Cómo comparar Presupuesto vs. Real con esta estructura:
Ingresos Presupuestados (Ej. para Enero 2024):
SELECT SUM(monto_presupuestado)
FROM item_presupuesto ip
JOIN presupuesto_anual pa ON ip.presupuesto_anual_id = pa.id
WHERE pa.año = 2024 AND ip.mes = 1 AND ip.tipo_item = 'INGRESO';
Use code with caution.
SQL
Ingresos Reales (Pagos recibidos en Enero 2024, que corresponden a conceptos de ingreso):
SELECT SUM(rfa.monto)
FROM registro_financiero_apartamento rfa
JOIN concepto c ON rfa.concepto_id = c.id
WHERE rfa.tipo_movimiento = 'CREDITO'
  AND EXTRACT(YEAR FROM rfa.fecha_efectiva) = 2024 -- o rfa.año_aplicable = 2024
  AND EXTRACT(MONTH FROM rfa.fecha_efectiva) = 1   -- o rfa.mes_aplicable = 1
  AND c.es_ingreso_tipico = TRUE; -- Asegurarse que el concepto del pago es un ingreso
Use code with caution.
SQL
Nota: La forma de determinar el "mes" del ingreso real (si fecha_efectiva o mes_aplicable/año_aplicable) dependerá de tu lógica de negocio.
Gastos Presupuestados (Ej. para Enero 2024):
SELECT ip.concepto_id, c.nombre, ip.monto_presupuestado
FROM item_presupuesto ip
JOIN presupuesto_anual pa ON ip.presupuesto_anual_id = pa.id
JOIN concepto c ON ip.concepto_id = c.id
WHERE pa.año = 2024 AND ip.mes = 1 AND ip.tipo_item = 'GASTO';
Use code with caution.
SQL
Gastos Reales (Ej. para Enero 2024):
SELECT gc.concepto_id, c.nombre, SUM(gc.monto) as total_gastado
FROM gasto_comunidad gc
JOIN concepto c ON gc.concepto_id = c.id
WHERE gc.año_gasto = 2024 AND gc.mes_gasto = 1
GROUP BY gc.concepto_id, c.nombre;
Use code with caution.
SQL
Esta estructura de base de datos debería ser un excelente punto de partida para tu proyecto. Recuerda que los modelos SQLModel se definirán de forma muy similar, y SQLModel/SQLAlchemy se encargarán de mapear tus clases Python a estas tablas.