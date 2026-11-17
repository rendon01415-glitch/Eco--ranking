#!/usr/bin/env python3
"""Crea y siembra las dos bases de datos de EcoRanking.

    python3 db/init_db.py            # crea las que falten
    python3 db/init_db.py --reset    # borra y vuelve a crear ambas

Resultado:  db/directivos.db   (administrador, directores, salones)
            db/estudiantes.db  (estudiantes y su puntaje)
"""
import hashlib
import os
import secrets
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DIRECTIVOS_DB = os.path.join(HERE, "directivos.db")
ESTUDIANTES_DB = os.path.join(HERE, "estudiantes.db")
ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt, digest = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iters))
    except ValueError:
        return False
    import hmac
    return hmac.compare_digest(dk.hex(), digest)


def _create(path: str, schema_file: str) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    with open(os.path.join(HERE, schema_file), encoding="utf-8") as f:
        con.executescript(f.read())
    return con


# ── Datos de prueba (mismos de la demo original) ─────────────────────────────
SALONES = [  # id, nombre, grado, director_id
    ("sal-1", "3A", 3, None),
    ("sal-2", "4A", 4, "dir-001"),
    ("sal-3", "4B", 4, "dir-002"),
    ("sal-4", "5A", 5, None),
    ("sal-5", "7A", 7, "dir-003"),
    ("sal-6", "7B", 7, "dir-004"),
    ("sal-7", "9A", 9, None),
    ("sal-8", "11A", 11, None),
]
DIRECTIVOS = [  # id, nombre, email, password, rol
    ("admin-001", "Carlos Mendoza",     "admin@ecoranking.edu",   "Admin2025!", "administrador"),
    ("dir-001",   "Prof. Luisa Torres", "luisa.torres@eco.edu",   "Profe2025",  "director"),
    ("dir-002",   "Prof. Mario Ríos",   "mario.rios@eco.edu",     "Profe2025",  "director"),
    ("dir-003",   "Prof. Sandra Gómez", "sandra.gomez@eco.edu",   "Profe2025",  "director"),
    ("dir-004",   "Prof. Julián Pérez", "julian.perez@eco.edu",   "Profe2025",  "director"),
]
ESTUDIANTES = [  # id, nombre, email, salon_id
    ("est-001", "Sofía Ramírez",    "sofia.ramirez@eco.edu",    "sal-2"),
    ("est-002", "Miguel Herrera",   "miguel.herrera@eco.edu",   "sal-2"),
    ("est-003", "Valentina Cruz",   "valentina.cruz@eco.edu",   "sal-2"),
    ("est-004", "Juan Morales",     "juan.morales@eco.edu",     "sal-2"),
    ("est-005", "Camila Vargas",    "camila.vargas@eco.edu",    "sal-2"),
    ("est-006", "Andrés López",     "andres.lopez@eco.edu",     "sal-3"),
    ("est-007", "Laura Sánchez",    "laura.sanchez@eco.edu",    "sal-3"),
    ("est-008", "Diego Castro",     "diego.castro@eco.edu",     "sal-5"),
    ("est-009", "Isabella Rojas",   "isabella.rojas@eco.edu",   "sal-5"),
    ("est-010", "Sebastián Flores", "sebastian.flores@eco.edu", "sal-6"),
]
MATERIAL = {  # nombre → puntos
    "Plástico PET": 10, "Aluminio": 15, "Cartón": 10, "Papel": 5, "Vidrio": 12,
}
# Depósitos con estudiante identificado: salón, estudiante, material, fecha
DEPOSITOS = [
    ("sal-2", "est-001", "Plástico PET", "2025-09-15T08:30:00-05:00"),
    ("sal-2", "est-002", "Aluminio",     "2025-09-15T09:15:00-05:00"),
    ("sal-2", "est-003", "Cartón",       "2025-09-15T10:00:00-05:00"),
    ("sal-2", "est-001", "Plástico PET", "2025-09-16T08:45:00-05:00"),
    ("sal-2", "est-004", "Papel",        "2025-09-16T09:30:00-05:00"),
    ("sal-2", "est-005", "Aluminio",     "2025-09-17T14:00:00-05:00"),
    ("sal-2", "est-001", "Plástico PET", "2025-09-18T08:00:00-05:00"),
    ("sal-2", "est-005", "Papel",        "2025-09-19T09:00:00-05:00"),
    ("sal-2", "est-004", "Cartón",       "2025-09-19T11:15:00-05:00"),
    ("sal-2", "est-002", "Aluminio",     "2025-09-20T08:30:00-05:00"),
    ("sal-3", "est-006", "Plástico PET", "2025-09-15T09:00:00-05:00"),
    ("sal-3", "est-007", "Papel",        "2025-09-15T10:30:00-05:00"),
    ("sal-5", "est-008", "Aluminio",     "2025-09-15T11:00:00-05:00"),
    ("sal-5", "est-009", "Cartón",       "2025-09-15T12:00:00-05:00"),
]
# Volumen sin estudiante identificado (suma al salón): salón, material, cantidad
VOLUMEN = [
    ("sal-4", "Aluminio", 12), ("sal-1", "Papel", 15), ("sal-6", "Plástico PET", 13),
    ("sal-7", "Vidrio", 5), ("sal-8", "Aluminio", 10), ("sal-8", "Papel", 5),
]
AJUSTES = [  # tipo, salón, estudiante, puntos, motivo, fecha
    ("penalizacion", "sal-2", "est-002", -10, "Penalización: depositar basura no reciclable",
     "2025-09-17T11:00:00-05:00"),
    ("bonificacion", "sal-2", "est-003", 20, "Bonificación: campaña especial semana del medio ambiente",
     "2025-09-18T10:30:00-05:00"),
]


def seed_directivos(con: sqlite3.Connection) -> None:
    con.executemany(
        "INSERT INTO directivos (id, nombre, email, password_hash, rol) VALUES (?,?,?,?,?)",
        [(i, n, e, hash_password(p), r) for i, n, e, p, r in DIRECTIVOS],
    )
    con.executemany(
        "INSERT INTO salones (id, nombre, grado, director_id) VALUES (?,?,?,?)", SALONES
    )
    con.commit()


def seed_estudiantes(con: sqlite3.Connection) -> None:
    con.executemany(
        "INSERT INTO estudiantes (id, nombre, email, password_hash, salon_id) VALUES (?,?,?,?,?)",
        [(i, n, e, hash_password("Eco2025"), s) for i, n, e, s in ESTUDIANTES],
    )
    n = 0

    def add(tipo, salon, est, material, pts, desc, por, fecha):
        nonlocal n
        n += 1
        con.execute(
            "INSERT INTO puntos (id, tipo, salon_id, estudiante_id, material, puntos,"
            " descripcion, registrado_por, fecha) VALUES (?,?,?,?,?,?,?,?,?)",
            (f"ev-{n:04d}", tipo, salon, est, material, pts, desc, por, fecha),
        )

    for salon, est, mat, fecha in DEPOSITOS:
        add("reciclaje", salon, est, mat, MATERIAL[mat], f"Depósito de {mat}", "Sistema IoT", fecha)
    base = datetime(2025, 9, 16, 7, 30, tzinfo=timezone(timedelta(hours=-5)))
    for salon, mat, cantidad in VOLUMEN:
        for g in range(1, cantidad + 1):
            fecha = (base + timedelta(hours=2 * g)).isoformat()
            add("reciclaje", salon, None, mat, MATERIAL[mat], f"Depósito de {mat}", "Sistema IoT", fecha)
    for tipo, salon, est, pts, motivo, fecha in AJUSTES:
        add(tipo, salon, est, "-", pts, motivo, "admin-001", fecha)
    con.commit()


def init(reset: bool = False) -> None:
    if reset:
        for p in (DIRECTIVOS_DB, ESTUDIANTES_DB):
            if os.path.exists(p):
                os.remove(p)
    if not os.path.exists(DIRECTIVOS_DB):
        con = _create(DIRECTIVOS_DB, "directivos_schema.sql")
        seed_directivos(con)
        con.close()
        print("✔ creada", DIRECTIVOS_DB)
    if not os.path.exists(ESTUDIANTES_DB):
        con = _create(ESTUDIANTES_DB, "estudiantes_schema.sql")
        seed_estudiantes(con)
        con.close()
        print("✔ creada", ESTUDIANTES_DB)


if __name__ == "__main__":
    init(reset="--reset" in sys.argv)
