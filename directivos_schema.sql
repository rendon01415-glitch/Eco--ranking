-- ============================================================================
-- EcoRanking · Base de datos de DIRECTIVOS  (db/directivos.db · SQLite)
-- Guarda: administradores, directores de grupo y los salones (grupos).
-- Los puntos NO viven aquí: están en estudiantes.db y el servidor los suma.
-- ============================================================================
PRAGMA foreign_keys = ON;

CREATE TABLE directivos (
  id             TEXT PRIMARY KEY,
  nombre         TEXT NOT NULL,
  email          TEXT NOT NULL UNIQUE COLLATE NOCASE,
  password_hash  TEXT NOT NULL,                       -- PBKDF2-SHA256, nunca texto plano
  rol            TEXT NOT NULL CHECK (rol IN ('administrador', 'director')),
  activo         INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
  ultimo_login   TEXT,
  created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE salones (
  id           TEXT PRIMARY KEY,
  nombre       TEXT NOT NULL UNIQUE,                  -- '4A', '7B', '11A'
  grado        INTEGER NOT NULL CHECK (grado BETWEEN 1 AND 11),
  -- Categoría derivada del grado: A = 1°–5°, B = 6°–11° (no puede quedar inconsistente)
  categoria    TEXT GENERATED ALWAYS AS (CASE WHEN grado <= 5 THEN 'A' ELSE 'B' END) STORED,
  director_id  TEXT REFERENCES directivos(id) ON DELETE SET NULL,
  activo       INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
  created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- Un director solo puede dirigir un salón
CREATE UNIQUE INDEX uq_salon_director ON salones (director_id) WHERE director_id IS NOT NULL;
