import json
import sqlite3
import logging
from config import DB_file

logger = logging.getLogger(__name__)


def init_db():
    """Creates the database and tables on first run."""
    con = sqlite3.connect(DB_file)
    cur = con.cursor()

    # Stores the user allergy + diet profile
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY,
            allergies TEXT DEFAULT '[]',
            diets     TEXT DEFAULT '[]',
            username  TEXT DEFAULT ''
        )"""
    )

    # Stores feedback after every dish check
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            dish       TEXT,
            bot_status TEXT,
            correct    INTEGER,
            note       TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    )

    con.commit()
    con.close()
    logger.info("Database initialised.")


def get_user(user_id: int) -> dict:
    """Returns the user's saved profile. If user doesn't exist, returns empty profile."""
    con = sqlite3.connect(DB_file)
    cur = con.cursor()
    cur.execute(
        "SELECT allergies, diets, username FROM users WHERE user_id=?", (user_id,)
    )
    row = cur.fetchone()
    con.close()

    if row:
        return {
            "allergies": json.loads(row[0]),
            "diets": json.loads(row[1]),
            "username": row[2],
        }

    return {"allergies": [], "diets": [], "username": ""}


def save_user(user_id: int, allergies: list, diets: list, username: str = ""):
    """Saves (or updates) a user's allergy + diet profile."""
    con = sqlite3.connect(DB_file)
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO users (user_id, allergies, diets, username)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (user_id) DO UPDATE SET
            allergies = excluded.allergies,
            diets     = excluded.diets,
            username  = excluded.username
        """,
        (user_id, json.dumps(allergies), json.dumps(diets), username),
    )
    con.commit()
    con.close()


def save_feedback(user_id: int, dish: str, bot_status: str, correct: int, note: str):
    """Saves user feedback after a dish check. correct=1 means bot was right, 0 = wrong."""
    con = sqlite3.connect(DB_file)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO feedback (user_id, dish, bot_status, correct, note) VALUES (?,?,?,?,?)",
        (user_id, dish, bot_status, correct, note),
    )
    con.commit()
    con.close()


def update_feedback_note(user_id: int, dish: str, note: str):
    """Updates the note on the most recent wrong-feedback record for this user+dish."""
    con = sqlite3.connect(DB_file, timeout=10)
    cur = con.cursor()
    cur.execute(
        """
        UPDATE feedback
        SET note = ?
        WHERE id = (
            SELECT MAX(id)
            FROM feedback
            WHERE user_id = ?
            AND dish = ?
            AND correct = 0
        )
        """,
        (note, user_id, dish),
    )
    con.commit()
    con.close()
