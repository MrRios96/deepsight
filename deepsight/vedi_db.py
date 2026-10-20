from src.db_relational import get_connection

con = get_connection()
try:
    righe = con.execute(
        "SELECT media_id, file_name, media_type, theme, tags FROM media"
    ).fetchall()

    print(f"Totale righe nel db: {len(righe)}\n")
    for r in righe:
        print("media_id:  ", r[0][:16], "...")   # solo i primi 16 caratteri dell'hash, per leggibilità
        print("file_name: ", r[1])
        print("media_type:", r[2])
        print("theme:     ", r[3])
        print("tags:      ", r[4])
        print("-" * 40)
finally:
    con.close()