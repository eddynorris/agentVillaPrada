-- Migration: 20260729000001_init_villa_prada_schema.sql
-- Description: Schema inicial para el Agente Secretario de Villa Prada

-- 1. ENUMS
DO $$ BEGIN
    CREATE TYPE tipo_evento_enum AS ENUM ('boda', 'quinceanero', 'institucional', 'alquiler_local');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE paquete_enum AS ENUM ('basico', 'premium', 'no_aplica');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE turno_enum AS ENUM ('almuerzo', 'cena');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE estado_evento_enum AS ENUM ('tentativo', 'prereservado', 'confirmado', 'cancelado', 'finalizado');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE tipo_pago_enum AS ENUM ('prereserva_300', 'adelanto_30pct', 'saldo_final', 'hora_extra');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE estado_pago_enum AS ENUM ('pendiente', 'verificado', 'rechazado');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE rol_personal_enum AS ENUM ('mozo', 'lider_mozos', 'chef', 'ayudante_cocina', 'dj', 'hora_loca');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE estado_confirmacion_enum AS ENUM ('pendiente', 'confirmado', 'rechazado');
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- 2. TABLA CLIENTES
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL,
    telefono VARCHAR(20) UNIQUE NOT NULL,
    ruc_dni VARCHAR(20),
    email TEXT,
    ciudad VARCHAR(100) DEFAULT 'Andahuaylas',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. TABLA EVENTOS
CREATE TABLE IF NOT EXISTS eventos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID REFERENCES clientes(id) ON DELETE CASCADE,
    tipo_evento tipo_evento_enum NOT NULL,
    paquete paquete_enum DEFAULT 'basico',
    fecha_evento DATE NOT NULL,
    turno turno_enum NOT NULL,
    nro_invitados INT NOT NULL CHECK (nro_invitados > 0),
    duracion_horas INT DEFAULT 8,
    horas_extras INT DEFAULT 0,
    precio_por_pax NUMERIC(10,2) NOT NULL,
    total_estimado NUMERIC(12,2) NOT NULL,
    estado estado_evento_enum DEFAULT 'tentativo',
    notas_decoracion TEXT,
    paleta_colores VARCHAR(255),
    disenio_pantalla TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_fecha_turno UNIQUE (fecha_evento, turno)
);

-- 4. TABLA PAGOS
CREATE TABLE IF NOT EXISTS pagos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evento_id UUID REFERENCES eventos(id) ON DELETE CASCADE,
    tipo_pago tipo_pago_enum NOT NULL,
    monto NUMERIC(10,2) NOT NULL,
    metodo_pago VARCHAR(50) DEFAULT 'yape_plin',
    referencia VARCHAR(100),
    url_comprobante TEXT,
    estado estado_pago_enum DEFAULT 'pendiente',
    fecha_pago TIMESTAMPTZ DEFAULT NOW()
);

-- 5. TABLA PERSONAL
CREATE TABLE IF NOT EXISTS personal_evento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evento_id UUID REFERENCES eventos(id) ON DELETE CASCADE,
    nombre_trabajador VARCHAR(255) NOT NULL,
    telefono_telegram VARCHAR(50),
    rol rol_personal_enum DEFAULT 'mozo',
    pago_acordado NUMERIC(10,2) DEFAULT 70.00,
    estado_confirmacion estado_confirmacion_enum DEFAULT 'pendiente',
    asistio BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. TABLA COMPRAS CHEF
CREATE TABLE IF NOT EXISTS compras_chef (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evento_id UUID REFERENCES eventos(id) ON DELETE CASCADE,
    lista_insumos_json JSONB NOT NULL,
    costo_estimado NUMERIC(10,2),
    estado VARCHAR(20) DEFAULT 'generado',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. TABLA CONTRATOS
CREATE TABLE IF NOT EXISTS contratos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evento_id UUID REFERENCES eventos(id) ON DELETE CASCADE,
    url_pdf TEXT NOT NULL,
    firmado BOOLEAN DEFAULT FALSE,
    fecha_firma TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. ÍNDICES Y SEGURIDAD (RLS)
CREATE INDEX IF NOT EXISTS idx_eventos_fecha ON eventos(fecha_evento);
CREATE INDEX IF NOT EXISTS idx_eventos_cliente ON eventos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pagos_evento ON pagos(evento_id);
CREATE INDEX IF NOT EXISTS idx_personal_evento ON personal_evento(evento_id);

-- Activar RLS en todas las tablas expuestas
ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE eventos ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagos ENABLE ROW LEVEL SECURITY;
ALTER TABLE personal_evento ENABLE ROW LEVEL SECURITY;
ALTER TABLE compras_chef ENABLE ROW LEVEL SECURITY;
ALTER TABLE contratos ENABLE ROW LEVEL SECURITY;

-- Políticas de RLS por defecto para el rol 'authenticated' y 'service_role'
DROP POLICY IF EXISTS "Permitir todo a service_role" ON clientes;
CREATE POLICY "Permitir todo a service_role" ON clientes FOR ALL TO service_role USING (true);

DROP POLICY IF EXISTS "Permitir todo a service_role" ON eventos;
CREATE POLICY "Permitir todo a service_role" ON eventos FOR ALL TO service_role USING (true);

DROP POLICY IF EXISTS "Permitir todo a service_role" ON pagos;
CREATE POLICY "Permitir todo a service_role" ON pagos FOR ALL TO service_role USING (true);

DROP POLICY IF EXISTS "Permitir todo a service_role" ON personal_evento;
CREATE POLICY "Permitir todo a service_role" ON personal_evento FOR ALL TO service_role USING (true);

DROP POLICY IF EXISTS "Permitir todo a service_role" ON compras_chef;
CREATE POLICY "Permitir todo a service_role" ON compras_chef FOR ALL TO service_role USING (true);

DROP POLICY IF EXISTS "Permitir todo a service_role" ON contratos;
CREATE POLICY "Permitir todo a service_role" ON contratos FOR ALL TO service_role USING (true);
