"""Strict prompts used by the retrieval-augmented answer service."""

SYSTEM_PROMPT = """You are a knowledge base assistant.

Answer ONLY using the provided context.

If the answer is not available in the context, say:

'I could not find this information in the knowledge base.'

Do not use outside knowledge."""

FALLBACK_ANSWER = "I could not find this information in the knowledge base."


def build_rag_prompt(
    question: str,
    context: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """Build a grounded prompt with bounded conversation memory."""

    history_text = "\n".join(
        f"{item.get('role', 'user').title()}: {item.get('content', '')}"
        for item in (history or [])[-10:]
        if item.get("content")
    )
    memory_section = (
        f"\nPrevious conversation (for continuity only):\n{history_text}\n"
        if history_text
        else ""
    )

    return f"""{SYSTEM_PROMPT}

Retrieved context:
---
{context}
---
{memory_section}

Question: {question}

Answer only from the retrieved context."""
