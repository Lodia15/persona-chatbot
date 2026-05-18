# Persona chatbot

A small **retrieval-augmented (RAG)** chatbot that answers in **first person** as a specific person, using your own `.txt` sources (posts, bio, transcripts). Embeddings live in a local **Chroma** database; the model is **OpenAI** (embeddings + chat).

## What is in this repo

| Piece | Role |
|--------|------|
| `documents/` | Source text files (`*.txt`) used for retrieval. |
| `ingest.py` | Chunks those files, embeds them, writes to `chroma_db/`. |
| `persona_engine.py` | Shared logic: embed query, search Chroma, call the chat model. |
| `chatbot.py` | Terminal chat loop. |
| `app.py` | FastAPI server + `/api/chat` + serves `/` and `/static/…`. |
| `static/` | Web UI: `index.html`, `css/` (tokens, layout, components, chat), `js/` (config, ui, chat module). |
| `transcription.py` | Optional helper: fetch a YouTube transcript into `documents/`. |

## Requirements

- **Python 3.10+** (tested with 3.13 in development).
- An **OpenAI API key** with access to the models below.

## Setup

```bash
cd persona-chatbot
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set your API key in one of these ways:

**Option A — `.env` file (recommended locally)**  
Copy the example and edit:

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
```

The app loads `.env` from the project folder when you run `uvicorn`, `chatbot.py`, or `ingest.py` (via `python-dotenv`).

**Option B — shell only**

```bash
export OPENAI_API_KEY="sk-..."    # Windows (cmd): set OPENAI_API_KEY=sk-...
```

Do **not** commit `.env` or keys; they are listed in `.gitignore`. You **may** commit `.env.example` (no real secrets).

## Build the vector index

1. Add or edit plain text files under **`documents/`** (extension `.txt`).
2. If **`chroma_db/`** already exists from an older run, **delete that folder** (or clear the Chroma collection) before re-ingesting, so chunk IDs do not collide.
3. Run:

```bash
python ingest.py
```

This creates (or updates) the **`persona`** collection under **`chroma_db/`**.

## Run the chatbot

**Web UI** (recommended for browsing):

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** . The API key must be set in the **same** process environment as `uvicorn`. In the chat box, sending **exit** clears the thread and starts a new session (same idea as the terminal CLI).

**Terminal UI**:

```bash
python chatbot.py
```

You do not need both at once; they use the same engine and the same `chroma_db/`.

## Optional: YouTube transcript

`transcription.py` downloads a transcript for a hard-coded video ID and writes **`documents/interview1.txt`**. Adjust the script, then run it and **re-run `ingest.py`** so the new text is embedded.

## Updating the knowledge base

1. Change files in **`documents/`**.
2. Remove **`chroma_db/`** (or wipe the collection) to avoid duplicate chunk IDs.
3. Run **`python ingest.py`** again.
4. Restart **`uvicorn`** if the web server was running.

## Configuration (code)

Defaults live in **`persona_engine.py`**:

- Embedding model: `text-embedding-3-small`
- Chat model: **`gpt-4o`** (default). For a cheaper/faster option:

  ```bash
  export PERSONA_CHAT_MODEL=gpt-4.1-mini
  ```

  Set `PERSONA_CHAT_MODEL` to any chat model your API key supports (see [OpenAI models](https://platform.openai.com/docs/models)).
- Chroma path: `chroma_db/` next to the project files
- Collection name: `persona`
- Retrieval: top **10** chunks per question

## Heroku

Dyno disks are **ephemeral**: anything written during a **`release:`** command does **not** reliably appear on **`web`** dynos, so `release: python ingest.py` will not fix “collection persona not found”.

This repo uses **`scripts/heroku-web.sh`**: on each **web** dyno boot, if `chroma_db/` is empty it runs **`ingest.py`**, then starts **`uvicorn`**. Set **`OPENAI_API_KEY`** (and optional **`PERSONA_CHAT_MODEL`**) in Heroku **Config Vars**. After a **dyno restart** the index is rebuilt once (OpenAI embedding cost on each cold boot).

## Git / GitHub

Commit source, `static/`, `requirements.txt`, and `.gitignore`. Do **not** commit **`venv/`**, **`chroma_db/`**, or secrets. Review **`documents/`** for anything you do not want public before pushing.

## License

No license is set in this repository; add one if you plan to share or accept contributions.
