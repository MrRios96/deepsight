from src.db_relational import inserisci_media, recupera_media, elimina_media
from src.db_vector import salva_embedding, collection, elimina_embedding, salva_volto, cerca_volti
from src.computer_vision.clip_model import genera_embedding_immagine, genera_embedding_testo
from src.computer_vision.face_model import estrai_volti

def aggiungi_media(file_path, theme=None, tags=None, metadata=None):
    # 1. scrivo PRIMA su SQLite (integrità del dato)
    media_id, inserito = inserisci_media(
        file_path, theme=theme, tags=tags, metadata=metadata
    )

    # 2. se era già presente, non tocco Chroma e avviso
    if not inserito:
        return media_id, "gia_presente"

    # 3. file nuovo: salvo l'embedding su Chroma con lo STESSO media_id
    try:
        embedding = genera_embedding_immagine(file_path)
        salva_embedding(media_id, embedding)
    except Exception as errore:
        # SQLite è andato ma Chroma no: lo segnalo, i metadati restano recuperabili
        return media_id, f"errore_chroma: {errore}"

    
    # 4. estraggo i volti e li salvo nella collection separata
    try:
        volti = estrai_volti(file_path)
        for i, volto in enumerate(volti):
            volto_id = f"{media_id}_{i}"
            salva_volto(volto_id, media_id, volto["embedding"])
    except Exception as errore:
        return media_id, f"inserito_senza_volti: {errore}"

    return media_id, "inserito"

# soglie di similarità (calibrate sperimentalmente)
SOGLIA_TESTO = 1.547
SOGLIA_IMMAGINE = 0.65

def cerca_simili(embedding_query, n_risultati=5, soglia=None, escludi_identici=False):
    risultati_chroma = collection.query(
        query_embeddings=[embedding_query],
        n_results=n_risultati + 5,   # chiedo qualcuno in più, poi filtro
    )
    ids = risultati_chroma["ids"][0]
    distanze = risultati_chroma["distances"][0]
    if not ids:
        return []

    righe_map = {r[0]: r for r in recupera_media(ids)}

    risultati_finali = []
    for media_id, distanza in zip(ids, distanze):
        if escludi_identici and distanza < 0.001:   # scarta il match con sé stesso
            continue
        if soglia is not None and distanza > soglia:  # filtro per soglia
            continue
        riga = righe_map.get(media_id)
        if riga is not None:
            risultati_finali.append({
                "media_id": media_id,
                "file_name": riga[2],
                "media_type": riga[3],
                "theme": riga[4],
                "tags": riga[5],
                "distanza": distanza,
            })
        if len(risultati_finali) >= n_risultati:
            break

    return risultati_finali

def cerca_per_testo(testo, n_risultati=5):
    embedding = genera_embedding_testo(testo)
    return cerca_simili(embedding, n_risultati=n_risultati, soglia=SOGLIA_TESTO)


def cerca_per_immagine(file_path, n_risultati=5):
    embedding = genera_embedding_immagine(file_path)
    return cerca_simili(
        embedding,
        n_risultati=n_risultati,
        soglia=SOGLIA_TESTO,
        escludi_identici=True,
    )   

def cerca_per_volto(file_path_query, soglia=1.0):
    # 1. estraggo il volto dall'immagine di query
    volti = estrai_volti(file_path_query)
    if not volti:
        return []

    embedding_query = volti[0]["embedding"]

    # 2. cerco volti simili (chiedo più risultati del necessario, poi filtro e deduplico)
    risultati = cerca_volti(embedding_query, n_risultati=20)

    ids_volti = risultati["ids"][0]
    distanze = risultati["distances"][0]
    metadatas = risultati["metadatas"][0]

    if not ids_volti:
        return []

    # 3. filtro per soglia + deduplico per media_id (tengo la distanza migliore)
    migliori = {}   # media_id -> distanza minima
    for distanza, meta in zip(distanze, metadatas):
        if distanza > soglia:
            continue                     # scarto i volti troppo lontani
        media_id = meta["media_id"]
        if media_id not in migliori or distanza < migliori[media_id]:
            migliori[media_id] = distanza

    if not migliori:
        return []

    # 4. recupero i metadati da SQLite e costruisco i risultati, ordinati per distanza
    risultati_finali = []
    for media_id, distanza in sorted(migliori.items(), key=lambda x: x[1]):
        righe = recupera_media([media_id])
        if righe:
            riga = righe[0]
            risultati_finali.append({
                "media_id": media_id,
                "file_name": riga[2],
                "distanza": distanza,
            })

    return risultati_finali

def rimuovi_media(media_id):
    # 1. tolgo PRIMA da Chroma (così non restano embedding orfani)
    try:
        elimina_embedding(media_id)
    except Exception as errore:
        return media_id, f"errore_chroma: {errore}"

    # 2. poi tolgo da SQLite (fonte di verità, ultimo a perdere il record)
    cancellato = elimina_media(media_id)

    if cancellato:
        return media_id, "rimosso"
    else:
        return media_id, "non_trovato"



