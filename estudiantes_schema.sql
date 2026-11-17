-- ============================================================================
-- EcoRanking · Base de datos de ESTUDIANTES  (db/estudiantes.db · SQLite)
-- Guarda: cuentas de estudiantes y su puntaje (libro de movimientos).
-- El puntaje no es un contador editable: se calcula sumando `puntos`,
-- así cada punto queda trazado (reciclaje, penalización o bonificación).
-- salon_id es una referencia LÓGICA a directivos.db → salones.id
-- (SQLite no permite FK entre archivos distintos; el servidor la valida).
-- ============================================================================
PRAGMA foreign_keys = ON;

CREATE TABLE estudiantes (
  id             TEXT PRIMARY KEY,
  nombre         TEXT NOT NULL,
  email          TEXT NOT NULL UNIQUE COLLATE NOCASE,
  password_hash  TEXT NOT NULL,
  salon_id       TEXT NOT NULL,
  activo         INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
  ultimo_login   TEXT,
  created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX ix_estudiantes_salon ON estudiantes (salon_id);

CREATE TABLE puntos (
  id              TEXT PRIMARY KEY,
  tipo            TEXT NOT NULL CHECK (tipo IN ('reciclaje', 'penalizacion', 'bonificacion')),
  salon_id        TEXT NOT NULL,
  estudiante_id   TEXT REFERENCES estudiantes(id),    -- NULL = movimiento colectivo del salón
  material        TEXT NOT NULL DEFAULT '-',
  puntos          INTEGER NOT NULL,
  descripcion     TEXT NOT NULL DEFAULT '',
  registrado_por  TEXT NOT NULL,                      -- id del admin o 'Sistema IoT'
  fecha           TEXT NOT NULL,                      -- ISO 8601
  -- penalización resta; reciclaje y bonificación suman
  CHECK ((tipo = 'penalizacion' AND puntos < 0) OR (tipo <> 'penalizacion' AND puntos > 0))
);
CREATE INDEX ix_puntos_salon      ON puntos (salon_id);
CREATE INDEX ix_puntos_estudiante ON puntos (estudiante_id);
