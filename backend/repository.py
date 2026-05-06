from __future__ import annotations

import json
import logging
import os
import sqlite3
from typing import Any

from flask import g

from backend.models import ChatSession

logger = logging.getLogger("teaching_agent")


def get_db(database_path: str) -> sqlite3.Connection:
    if "db" not in g:
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        g.db = connection
    return g.db


def close_db() -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(database_path: str, force: bool = False):
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    if force and os.path.exists(database_path):
        os.remove(database_path)

    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                messages_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_chats_updated_at ON chats(updated_at DESC);
            """
        )
        connection.commit()
    finally:
        connection.close()


def parse_messages_json(raw_value: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        logger.warning("invalid_messages_json error=%s", exc)
        return []
    return payload if isinstance(payload, list) else []


def row_to_chat(row: sqlite3.Row) -> ChatSession:
    return ChatSession(
        chat_id=row["chat_id"],
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        messages=parse_messages_json(row["messages_json"]),
    )


def fetch_chat_by_id(database_path: str, chat_id: str) -> ChatSession | None:
    row = get_db(database_path).execute(
        "SELECT chat_id, title, created_at, updated_at, messages_json FROM chats WHERE chat_id = ?",
        (chat_id,),
    ).fetchone()
    return row_to_chat(row) if row else None


def fetch_all_chats(database_path: str) -> list[ChatSession]:
    rows = get_db(database_path).execute(
        "SELECT chat_id, title, created_at, updated_at, messages_json FROM chats ORDER BY updated_at DESC"
    ).fetchall()
    return [row_to_chat(row) for row in rows]


def save_chat(database_path: str, chat: ChatSession):
    get_db(database_path).execute(
        """
        INSERT INTO chats(chat_id, title, created_at, updated_at, messages_json)
        VALUES(?, ?, ?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
            title = excluded.title,
            updated_at = excluded.updated_at,
            messages_json = excluded.messages_json
        """,
        (
            chat.chat_id,
            chat.title,
            chat.created_at,
            chat.updated_at,
            json.dumps(chat.messages, ensure_ascii=False),
        ),
    )
    get_db(database_path).commit()


def remove_chat(database_path: str, chat_id: str) -> bool:
    cursor = get_db(database_path).execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
    get_db(database_path).commit()
    return cursor.rowcount > 0
