# DeepSight — Ricerca semantica multimodale su immagini

DeepSight indicizza una raccolta di immagini e permette di cercarle in tre modi:

- **per testo**: descrivi cosa cerchi ("un cane su una spiaggia") e trova le immagini più vicine;
- **per immagine**: dai un'immagine e trova quelle simili;
- **per volto**: dai la foto di una persona e trova le immagini in cui compare.

Progetto *Learning by Project* — ITS Academy ICT Piemonte, percorso Data Analyst & AI Specialist (2026). Lavoro di gruppo: mi sono occupato dello schema dati e della parte di computer vision (moduli CLIP e InsightFace).

## Come funziona

```
            immagine
               │
      ┌────────┴─────────┐
      ▼                  ▼
  hash SHA-256       CLIP ViT-B/32 ──► embedding 512-d ──► Chroma: media_images
  = media_id         InsightFace   ──► un embedding 512-d per volto ──► Chroma: media_faces
      │
      ▼
  SQLite: tabella media (percorso, tipo, tema, tag, metadati)
```

Ogni file riceve come identificativo l'**hash SHA-256 del suo contenuto**. Lo stesso `media_id` lega i metadati in SQLite agli embedding in Chroma, e caricare due volte lo stesso file non crea duplicati.

Le ricerche lavorano tutte allo stesso modo: si genera l'embedding della query (testo, immagine o volto), Chroma restituisce i vettori più vicini, si filtra per soglia di distanza, e i metadati si recuperano da SQLite.

## Scelte tecniche

- **Due database, due ruoli.** SQLite è la fonte di verità per i metadati; Chroma conserva solo gli embedding. Volti e immagini stanno in due collection separate, perché CLIP e InsightFace producono vettori in spazi diversi e non confrontabili.
- **Ordine delle scritture.** In inserimento si scrive prima su SQLite e poi su Chroma; in cancellazione si toglie prima da Chroma e poi da SQLite. In caso di errore a metà non restano embedding orfani, e i metadati restano sempre recuperabili.
- **Embedding normalizzati.** Gli embedding CLIP di testo e immagini sono normalizzati a norma unitaria, e per i volti si usa l'embedding già normalizzato di InsightFace. Senza normalizzazione le distanze dipendono anche dalla lunghezza dei vettori, non solo dalla loro direzione, e il confronto tra un testo e un'immagine perde affidabilità.
- **Soglie calibrate sui dati.** Le soglie di distanza per la ricerca testuale e per i volti sono state tarate sperimentalmente su immagini reali, così vengono scartati i risultati troppo lontani invece di restituire sempre i primi N.
- **Deduplica dei volti.** Un'immagine può contenere più volti simili alla query: la ricerca tiene per ogni immagine solo la distanza migliore.
- **Modelli caricati una volta sola**, all'import del modulo, per non ricaricarli a ogni ricerca.

## Struttura

```
src/
  config.py              # percorsi di SQLite e Chroma (cartella data/)
  utils.py               # hash SHA-256 dei file
  db_relational.py       # schema e operazioni su SQLite
  db_vector.py           # collection Chroma per immagini e volti
  media_manager.py       # inserimento, ricerca e rimozione: coordina i due database
  computer_vision/
    clip_model.py        # embedding CLIP di immagini e testo
    face_model.py        # rilevamento volti ed embedding con InsightFace
vedi_db.py               # stampa il contenuto della tabella media
```

## Come usarlo

```bash
python -m venv venv
venv\Scripts\activate            # su Windows
pip install -r requirements.txt
```

Al primo avvio i modelli (CLIP `clip-ViT-B-32` e InsightFace `buffalo_l`) vengono scaricati in automatico. Database e indici vengono creati nella cartella `data/`.

Esempio, dalla cartella principale del progetto:

```python
from src.db_relational import create_schema
from src.media_manager import aggiungi_media, cerca_per_testo, cerca_per_immagine, cerca_per_volto

create_schema()

aggiungi_media("foto/spiaggia.jpg", theme="vacanze", tags=["mare", "estate"])

cerca_per_testo("un tramonto sul mare")
cerca_per_immagine("foto/query.jpg")
cerca_per_volto("foto/persona.jpg")
```

## Privacy

Il repository contiene solo il codice. Le immagini usate per i test, i database e gli embedding dei volti non sono pubblicati: gli embedding facciali sono dati biometrici.

## Stack

Python · CLIP (sentence-transformers) · InsightFace · ChromaDB · SQLite · OpenCV · Pillow
