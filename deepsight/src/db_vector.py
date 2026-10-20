import chromadb
from src.config import CHROMA_PATH

# dimensione degli embedding (512 = CLIP ViT-B/32)
EMBEDDING_DIM = 512

# client persistente: scrive su disco in data/vector
client = chromadb.PersistentClient(path=str(CHROMA_PATH))

# collection per gli embedding delle immagini
collection = client.get_or_create_collection(name="media_images")

def salva_embedding(media_id, embedding):
    collection.add(
        ids=[media_id],
        embeddings=[embedding],
    )

def elimina_embedding(media_id):
    collection.delete(ids=[media_id])

# collection separata per gli embedding dei volti (spazio diverso da CLIP)
collection_volti = client.get_or_create_collection(name="media_faces")


def salva_volto(volto_id, media_id, embedding):
    collection_volti.add(
        ids=[volto_id],
        embeddings=[embedding],
        metadatas=[{"media_id": media_id}],
    )


def cerca_volti(embedding_query, n_risultati=5):
    return collection_volti.query(
        query_embeddings=[embedding_query],
        n_results=n_risultati,
    )