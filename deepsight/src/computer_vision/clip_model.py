from sentence_transformers import SentenceTransformer
from PIL import Image

# carico il modello CLIP pretrained UNA volta sola, quando il modulo viene importato
print("Carico il modello CLIP (primo run, scarico pesi, dopo userà la cache)...")
_model = SentenceTransformer("clip-ViT-B-32")
print("Modello CLIP pronto.")


def genera_embedding_immagine(file_path):
    immagine = Image.open(file_path)
    embedding = _model.encode(immagine, normalize_embeddings=True)
    return embedding.tolist()


def genera_embedding_testo(testo):
    embedding = _model.encode(testo, normalize_embeddings=True)
    return embedding.tolist()