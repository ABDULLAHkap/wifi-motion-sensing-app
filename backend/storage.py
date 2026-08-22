import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any

DB_PATH = Path(__file__).with_name("wifi_motion.db")
_LOCK = Lock()


def init_db() -> None:
    with _LOCK, sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wifi_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                room_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                rssi INTEGER NOT NULL,
                frequency_mhz INTEGER,
                link_speed_mbps INTEGER,
                motion_score REAL,
                motion_state TEXT
            )
            """
        )
        conn.commit()


def insert_sample(sample: dict[str, Any]) -> int:
    with _LOCK, sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO wifi_samples (
                device_id, room_id, timestamp, rssi, frequency_mhz,
                link_speed_mbps, motion_score, motion_state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sample["device_id"], sample["room_id"], sample["timestamp"],
                sample["rssi"], sample.get("frequency_mhz"),
                sample.get("link_speed_mbps"), sample.get("motion_score"),
                sample.get("motion_state"),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def latest_sample(room_id: str) -> dict[str, Any] | None:
    with _LOCK, sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM wifi_samples WHERE room_id = ? ORDER BY id DESC LIMIT 1",
            (room_id,),
        ).fetchone()
        return dict(row) if row else None


def recent_samples(room_id: str, limit: int = 120) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 1000))
    with _LOCK, sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM wifi_samples WHERE room_id = ? ORDER BY id DESC LIMIT ?",
            (room_id, limit),
        ).fetchall()
        return [dict(row) for row in reversed(rows)]
