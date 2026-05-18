from pathlib import Path

from openai import OpenAI
import chromadb

BASE_DIR = Path(__file__).resolve().parent
CHROMA_PATH = BASE_DIR / "chroma_db"
COLLECTION_NAME = "persona"
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-mini"


def _build_system_prompt(context: str) -> str:
    return f"""
You are simulating a real person based on their writings, interviews, and posts.

Rules:
- You are this person. Respond in first person ("I").
- Keep answers very short (1–2 sentences maximum).
- Be natural, conversational, and human-like.
- Do NOT write essays, reports, or long explanations.
- Do NOT mention "context", "documents", or "sources".
- Do NOT say you are an AI or assistant.

Honesty rule:
- If you do not know something or it is not clearly in your knowledge/context, explicitly say:
  "I don’t know" or "I’m not sure about that."

Behavior:
- Prefer simple, direct answers over analysis.
- Match the tone and worldview of the provided context.

Context:
{context}
"""


class PersonaBot:
    """RAG persona chat: retrieve from Chroma, answer with OpenAI."""

    def __init__(
        self,
        client: OpenAI | None = None,
        chroma_path: Path | None = None,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self.client = client or OpenAI()
        path = chroma_path or CHROMA_PATH
        self._chroma = chromadb.PersistentClient(path=str(path))
        self._collection = self._chroma.get_collection(name=collection_name)
        self.conversation: list[dict[str, str]] = []

    def ask(self, question: str) -> str:
        q_embedding = self.client.embeddings.create(
            model=EMBED_MODEL,
            input=question,
        ).data[0].embedding

        results = self._collection.query(
            query_embeddings=[q_embedding],
            n_results=5,
        )
        context = "\n\n".join(results["documents"][0])
        system_prompt = _build_system_prompt(context)

        self.conversation.append({"role": "user", "content": question})
        if len(self.conversation) > 10:
            self.conversation = self.conversation[-10:]

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation)

        response = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=400,
        )
        answer = response.choices[0].message.content or ""
        self.conversation.append({"role": "assistant", "content": answer})
        return answer
