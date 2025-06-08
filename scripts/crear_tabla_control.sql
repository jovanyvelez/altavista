-- Migración para tabla de control de procesamiento mensual
-- Si la tabla ya existe, este script la actualizará según sea necesario

-- Crear la tabla si no existe
CREATE TABLE IF NOT EXISTS control_procesamiento_mensual (
    id SERIAL PRIMARY KEY,
    año INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes >= 1 AND mes <= 12),
    tipo_procesamiento VARCHAR(50) NOT NULL,
    fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    registros_procesados INTEGER DEFAULT 0,
    monto_total_generado DECIMAL(12, 2) DEFAULT 0.00,
    estado VARCHAR(20) DEFAULT 'COMPLETADO',
    observaciones TEXT,
    
    -- Índices para optimizar consultas
    CONSTRAINT unique_año_mes_tipo UNIQUE (año, mes, tipo_procesamiento)
);

-- Crear índices si no existen
CREATE INDEX IF NOT EXISTS idx_control_año_mes_tipo ON control_procesamiento_mensual (año, mes, tipo_procesamiento);
CREATE INDEX IF NOT EXISTS idx_control_fecha ON control_procesamiento_mensual (fecha_procesamiento);
CREATE INDEX IF NOT EXISTS idx_control_estado ON control_procesamiento_mensual (estado);

-- Comentarios para documentación
COMMENT ON TABLE control_procesamiento_mensual IS 'Control de procesamiento mensual para evitar duplicados en generación de cargos';
COMMENT ON COLUMN control_procesamiento_mensual.tipo_procesamiento IS 'Tipo de procesamiento: CUOTAS, INTERESES, PROCESAMIENTO_COMPLETO';
COMMENT ON COLUMN control_procesamiento_mensual.estado IS 'Estado: PROCESANDO, COMPLETADO, ERROR';
