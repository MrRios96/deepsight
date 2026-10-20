import numpy as np
from insightface.app import FaceAnalysis
import os
from PIL import Image

# carico il modello UNA volta sola all'import
print("Carico il modello volti (InsightFace)...")
_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
_app.prepare(ctx_id=-1, det_size=(640, 640))
print("Modello volti pronto.")


def estrai_volti(file_path):
    import cv2
    immagine = cv2.imread(file_path)
    if immagine is None:
        return []

    volti = _app.get(immagine)

    risultati = []
    for volto in volti:
        risultati.append({
            "embedding": volto.normed_embedding.tolist(),
            "bbox": volto.bbox.tolist(),
            "score": float(volto.det_score),
        })
    return risultati


def salva_ritagli_volti(file_path, media_id, cartella_output="data/volti"):
    os.makedirs(cartella_output, exist_ok=True)

    volti = estrai_volti(file_path)
    immagine = Image.open(file_path).convert("RGB")

    percorsi_ritagli = []
    for i, volto in enumerate(volti):
        x1, y1, x2, y2 = [int(c) for c in volto["bbox"]]
        # allargo un po' il ritaglio per non tagliare troppo stretto
        margine = 20
        x1, y1 = max(0, x1 - margine), max(0, y1 - margine)
        x2, y2 = x2 + margine, y2 + margine

        ritaglio = immagine.crop((x1, y1, x2, y2))
        nome_file = f"{media_id}_{i}.jpg"
        percorso = os.path.join(cartella_output, nome_file)
        ritaglio.save(percorso, "JPEG")
        percorsi_ritagli.append(percorso)

    return percorsi_ritagli