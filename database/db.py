"""
database/db.py
─────────────────────────────────────────────────────────────────
Camada de persistência (SQLite). Duas tabelas: insights (matéria-
prima humana) e pareceres_gerados (histórico de cada parecer
aprofundado produzido pela IA).
─────────────────────────────────────────────────────────────────
"""

import sqlite3
import json
import os
import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "app_data.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                texto TEXT NOT NULL,
                sub_nicho TEXT,
                usado_em_geracao INTEGER DEFAULT 0,
                criado_em TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS pareceres_gerados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sub_nichos TEXT,
                publico TEXT,
                objetivo TEXT,
                resultado_json TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
        """)


# ─── INSIGHTS ────────────────────────────────────────────────────
def salvar_insight(texto: str, sub_nicho: str = ""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO insights (texto, sub_nicho, criado_em) VALUES (?, ?, ?)",
            (texto, sub_nicho, datetime.datetime.now().isoformat()),
        )


def listar_insights() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM insights ORDER BY criado_em DESC").fetchall()
        return [dict(r) for r in rows]


def marcar_insights_usados(ids: list[int]):
    if not ids:
        return
    with get_conn() as conn:
        conn.executemany("UPDATE insights SET usado_em_geracao = usado_em_geracao + 1 WHERE id = ?", [(i,) for i in ids])


def excluir_insight(insight_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM insights WHERE id = ?", (insight_id,))


# ─── PARECERES (histórico) ───────────────────────────────────────
def salvar_parecer_gerado(sub_nichos: list[str], publico: str, objetivo: str, resultado: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO pareceres_gerados (sub_nichos, publico, objetivo, resultado_json, criado_em)
               VALUES (?, ?, ?, ?, ?)""",
            (", ".join(sub_nichos), publico, objetivo, json.dumps(resultado, ensure_ascii=False), datetime.datetime.now().isoformat()),
        )
        return cur.lastrowid


def listar_pareceres_gerados(limit: int = 30) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM pareceres_gerados ORDER BY criado_em DESC LIMIT ?", (limit,)
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["resultado"] = json.loads(d.pop("resultado_json"))
            out.append(d)
        return out