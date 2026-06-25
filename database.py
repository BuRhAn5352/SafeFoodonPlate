import json
import sqlite3
import logging
from config import DB_file

logger = logging.getLogger(__name__)

def init_db():
    "creates the database and tables in the first run"
    con = sqlite3.connect(DB_file)
    cur = con.cursor()

    #stores the user allergy + diet profile
    cur.execute( 
        """
        CREATE TABLE IF NOT EXISTS users (
        user_id   INTEGER PRIMARY KEY,
        allergies TEXT DEFAULT '[]',
        diets     TEXT DEFAULT '[]',
        username  TEXT DEFAULT ''
        )"""
        )
    
    #stores feedback after every dish check
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
    logger.info("Database Initialised")
    

def get_user(user_id: int) -> dict:
    """
    returns the user's saved profile
    If user doesn't exist yet,returns empty profile.
    """
    con = sqlite3.connect(DB_file)
    cur = con.cursor()
    cur.execute(
        "SELECT allergies, diets, username FROM users WHERE user_id=?",
        (user_id,)
    )
    row = cur.fetchone()
    con.close()

    if row:
        return {
            "allergies" : json.loads(row[0]),
            "diets" : json.loads(row[1]),
            "username": row[2],
        }
    
    #new user ko return blank profile 
    return {"allergies" : [] , "diets" : [], "username" : ""}


def save_user(user_id : int, allergies : list, diets : list, username : str = ""):
    """
    saves (or updates) a user's allergy + diet profile
    Uses INSERT OR REPLACE so it works for both new and existing users
    """
    con = sqlite3.connect(DB_file)
    cur = con.cursor()
    cur.execute(
        """ 
        INSERT INTO users (user_id, allergies, diets, username)
        VALUES (?,?,?,?)
        ON CONFLICT (user_id) DO UPDATE SET
        allergies = excluded.allergies,
        diets = excluded.diets,
        username = excluded.username
                     """,(user_id, json.dumps(allergies), json.dumps(diets) ,username)
                     )
    con.commit()
    con.close()


def save_feedback(user_id : int, dish : str, bot_status : str , correct : int, note : str):
    """
    saves users feedback after a dish check, correct =1 means bot was right or else wrong if 0"""
    con = sqlite3.connect(DB_file)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO feedback (user_id,  dish, bot_status, correct, note) VALUES (?,?,?,?,?)",
        (user_id,dish,bot_status,correct,note)
    )
    con.commit()
    con.close()
<<<<<<< HEAD

def update_feedback_note(user_id: int, dish: str, note: str):
    con = sqlite3.connect(DB_file, timeout=10)
    cur = con.cursor()

    cur.execute("""
        UPDATE feedback
        SET note = ?
        WHERE id = (
            SELECT MAX(id)
            FROM feedback
            WHERE user_id = ?
            AND dish = ?
            AND correct = 0
        )""",(note, user_id, dish))

    con.commit()
    con.close()
