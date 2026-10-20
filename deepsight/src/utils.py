import hashlib
from pathlib import Path

def hash_file(file_path):
    path = Path(file_path)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blocco in iter(lambda: f.read(8192), b""):
            h.update(blocco)
    return h.hexdigest()

if __name__ == "__main__":
    percorso = "test.jpg"
    print("File:", percorso)
    print("Hash (image_id):", hash_file(percorso))
