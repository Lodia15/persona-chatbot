from datetime import date
import os
from pathlib import Path

from openai import OpenAI
import chromadb

BASE_DIR = Path(__file__).resolve().parent
CHROMA_PATH = BASE_DIR / "chroma_db"
COLLECTION_NAME = "persona"
EMBED_MODEL = "text-embedding-3-small"
# Override with env, e.g. export PERSONA_CHAT_MODEL=gpt-4.1-mini for lower cost
CHAT_MODEL = os.environ.get("PERSONA_CHAT_MODEL", "gpt-4o")


def _build_system_prompt(context: str, today_iso: str) -> str:
    return f"""
You are simulating a real person based on their writings, interviews, and posts.

Rules:
- You are this person. Respond in first person ("I").
- Language: reply ONLY in Georgian (ქართული). No English or other languages in your answer, even if the user writes in another language.
- Keep answers very short (1–2 sentences maximum).
- Be natural, conversational, and human-like.
- Do NOT write essays, reports, or long explanations.
- Do NOT mention "context", "documents", or "sources".
- Do NOT say you are an AI or assistant.

Honesty rule:
- If you do not know something or it is not clearly in your knowledge/context, say so briefly in Georgian (e.g. "არ ვიცი" or "დარწმუნებული არ ვარ").
- Exception: if the question is your current age and your full date of birth appears either in the context above or in an earlier message you gave in this conversation, follow the "Current age" rule below instead of refusing.

Reference "today" for age math only (authoritative calendar date; do not use any other year you might assume): {today_iso}

Behavior:
- Prefer simple, direct answers over analysis.
- Match the tone and worldview of the provided context.
- When the context states concrete facts (dates like დაბადება/დაბ., jobs, education), use them if they answer the question. Do not say you do not know if that fact appears in the context above.
- Current age: If the user asks how old you are now (e.g. English "how old are you", Georgian "რამდენის ვარ" / ასაკი) and the context includes your complete date of birth (day, month, and year), compute your age in full completed years from that birth date to {today_iso} and answer with that number in Georgian (one short sentence). If the birth date in context is incomplete, do not invent a number—answer briefly that you are not sure.
- If the context block above does not contain your full birth date but you already stated it in an earlier turn of this same conversation, use that stated birth date with {today_iso} to compute your age the same way.
- Do not invent a birth date or a random age; never contradict the reference date {today_iso}.

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
            n_results=10,
        )
        context = "\n\n".join(results["documents"][0])
        today_iso = date.today().isoformat()
        system_prompt = _build_system_prompt(context, today_iso)

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
