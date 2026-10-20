import sqlite3
import json
from pathlib import Path
from src.config import SQLITE_PATH
from src.utils import hash_file


def get_connection():
    return sqlite3.connect(str(SQLITE_PATH))


def create_schema():
    con = get_connection()
    try:
        con.execute("""
            CREATE TABLE IF NOT EXISTS media (
                media_id    TEXT PRIMARY KEY,
                file_path   TEXT NOT NULL,
                file_name   TEXT,
                media_type  TEXT,
                theme       TEXT,
                tags        TEXT,
                created_at  TIMESTAMP DEFAULT current_timestamp,
                metadata    TEXT
            );
        """)
        con.commit()
    finally:
        con.close()


def deduci_media_type(file_name):
    estensione = Path(file_name).suffix.lower()
    immagini = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    video = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    if estensione in immagini:
        return "image"
    if estensione in video:
        return "video"
    return "unknown"


def inserisci_media(file_path, theme=None, tags=None, metadata=None):
    percorso = Path(file_path)
    media_id = hash_file(percorso)
    file_name = percorso.name
    media_type = deduci_media_type(file_name)

    con = get_connection()
    try:
        # controlla se questo media_id esiste già
        esiste = con.execute(
            "SELECT 1 FROM media WHERE media_id = ?", (media_id,)
        ).fetchone()

        if esiste:
            # file già presente: non reinserisco
            return media_id, False

        # file nuovo: inserisco
        con.execute(
            """
            INSERT INTO media
                (media_id, file_path, file_name, media_type, theme, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                media_id,
                str(percorso),
                file_name,
                media_type,
                theme,
                json.dumps(tags) if tags is not None else None,
                json.dumps(metadata) if metadata is not None else None,
            )
        )
        con.commit()
        return media_id, True
    finally:
        con.close()


def recupera_media(media_ids):#ponte tra chroma e sqlite
    if not media_ids:
        return []

    con = get_connection()
    try:
        segnaposto = ",".join("?" for _ in media_ids)
        query = f"SELECT * FROM media WHERE media_id IN ({segnaposto})"
        righe = con.execute(query, media_ids).fetchall()
        return righe
    finally:
        con.close()

def elimina_media(media_id):
    con = get_connection()
    try:
        cursore = con.execute(
            "DELETE FROM media WHERE media_id = ?", (media_id,)
        )
        con.commit()
        # rowcount dice quante righe sono state cancellate (0 o 1)
        return cursore.rowcount > 0
    finally:
        con.close()


if __name__ == "__main__":
    create_schema()
    con = get_connection()
    try:
        tabelle = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()
        print("Tabelle nel database:", tabelle)
    finally:
        con.close()

