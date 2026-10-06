"""Strict prompts used by the retrieval-augmented answer service."""

SYSTEM_PROMPT = """You are a knowledge base assistant.

Answer ONLY using the provided context.

If the answer is not available in the context, say:

'I could not find this information in the knowledge base.'

Do not use outside knowledge.

Give a concise, complete answer. Use Markdown headings, lists, and emphasis
when they improve readability. Do not repeat the question."""

FALLBACK_ANSWER = "I could not find this information in the knowledge base."


def build_rag_prompt(
    question: str,
    context: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """Build a grounded prompt with bounded conversation memory."""

    # Keep recent turns for follow-up questions without growing the prompt
    # indefinitely. Document context remains the only source of facts.
    recent_turns: list[str] = []
    remaining = 4_000
    for item in reversed((history or [])[-10:]):
        content = item.get("content", "")
        if not content or remaining <= 0:
            continue
        turn = f"{item.get('role', 'user').title()}: {content}"
        recent_turns.append(turn[:remaining])
        remaining -= len(recent_turns[-1]) + 1
    history_text = "\n".join(reversed(recent_turns))
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
