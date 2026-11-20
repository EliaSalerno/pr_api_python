import json
import sqlite3
from contextlib import closing
from typing import Any

from fastapi import Body, FastAPI, HTTPException

DB_PATH = "data.db"
app = FastAPI(title="JSON API + SQLite")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_conn()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                data       TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


init_db()


@app.post("/items", status_code=201)
def crea(payload: Any = Body(...)):
    """Riceve un JSON qualsiasi (oggetto, lista, valore) e lo salva."""
    with closing(get_conn()) as conn, conn:
        cur = conn.execute("INSERT INTO items (data) VALUES (?)", (json.dumps(payload),))
        return {"id": cur.lastrowid, "ricevuto": payload}


@app.get("/items")
def elenca(limit: int = 50, offset: int = 0):
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT id, data, created_at FROM items ORDER BY id LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [
        {"id": r["id"], "created_at": r["created_at"], "data": json.loads(r["data"])}
        for r in rows
    ]


@app.get("/items/{item_id}")
def leggi(item_id: int):
    with closing(get_conn()) as conn:
        r = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if r is None:
        raise HTTPException(404, "Non trovato")
    return {"id": r["id"], "created_at": r["created_at"], "data": json.loads(r["data"])}


@app.put("/items/{item_id}")
def sostituisci(item_id: int, payload: Any = Body(...)):
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "UPDATE items SET data = ? WHERE id = ?", (json.dumps(payload), item_id)
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Non trovato")
    return {"id": item_id, "ricevuto": payload}


@app.delete("/items/{item_id}", status_code=204)
def elimina(item_id: int):
    with closing(get_conn()) as conn, conn:
        cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Non trovato")


# Installazione: pip install fastapi uvicorn requests
# Avvio:         uvicorn server:app --reload
# Docs:          http://127.0.0.1:8000/docs