"""Strict prompts used by the retrieval-augmented answer service."""

SYSTEM_PROMPT = """You are a knowledge base assistant.

Answer ONLY using the provided context.

If the answer is not available in the context, say:

'I could not find this information in the knowledge base.'

Do not use outside knowledge.

Answer only what the question asks. For a direct factual question, return one
short sentence. Do not add a heading, bullet list, background, significance,
or related facts unless the user explicitly asks for them. Use Markdown only
when the user requests an explanation. Do not repeat the question or generate
a visible reasoning trace. /no_think"""

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
    remaining = 800
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
