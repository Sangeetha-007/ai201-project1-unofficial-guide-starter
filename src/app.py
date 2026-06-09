"""Milestone 5 — Grounded generation + Gradio interface.

Final stage of the pipeline (see planning.md architecture diagram):

    Ingestion -> Chunking -> Embedding + Vector Store -> Retrieval -> [Generation -> UI]
                                                                       ^^^^^^^^^^^^^^^^^^
                                                                       this module

Flow per question:
    1. retrieve() pulls the top-k chunks from ChromaDB (Milestone 4).
    2. Those chunks — and only those — are passed to the LLM as context.
    3. A grounding system prompt forces the model to answer ONLY from that
       context and to say so when the answer isn't present.
    4. The response is returned as: an answer, followed by a Sources list of
       the documents the answer was drawn from.

Run the UI:   python src/app.py
Ask in code:  from app import answer_question; answer_question("...")

Requires GROQ_API_KEY in .env (see .env.example).
"""

from __future__ import annotations

import os

import gradio as gr
from dotenv import load_dotenv
from groq import Groq

from vector_store import TOP_K, retrieve

load_dotenv()

# Groq's hosted Llama model; override with GROQ_MODEL in .env if you like.
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# --- Grounding ---------------------------------------------------------------

SYSTEM_PROMPT = """\
You are "The Unofficial Guide" to Brooklyn College's Computer Science program.
You answer questions about CS courses and professors using ONLY the numbered
context passages provided with each question.

Rules:
- Use only facts found in the context. Do not use outside knowledge.
- If the context does not contain the answer, reply exactly:
  "I don't have enough information in my sources to answer that."
- Do not guess, infer beyond the text, or invent ratings, names, or numbers.
- When you use a fact, attribute it to its source in-line, e.g. (Sokol.txt).
- Be concise and answer the question directly."""

NO_ANSWER = "I don't have enough information in my sources to answer that."


def format_context(hits: list[dict]) -> str:
    """Render retrieved chunks as a numbered, source-labeled context block."""
    blocks = []
    for i, hit in enumerate(hits, 1):
        blocks.append(f"[{i}] (source: {hit['source']})\n{hit['text']}")
    return "\n\n".join(blocks)


def build_messages(query: str, hits: list[dict]) -> list[dict]:
    """Assemble the chat messages: grounding system prompt + context + question."""
    context = format_context(hits)
    user_content = (
        f"Context passages:\n\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer using only the context above."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


# --- Generation --------------------------------------------------------------

_client: Groq | None = None


def get_client() -> Groq:
    """Lazily create the Groq client; fail loudly if the key is missing."""
    global _client
    if _client is None:
        if not os.getenv("GROQ_API_KEY"):
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        _client = Groq()
    return _client


def answer_question(query: str, top_k: int = TOP_K) -> dict:
    """Retrieve, generate a grounded answer, and collect source attribution.

    Returns {"answer": str, "sources": list[str], "hits": list[dict]}.
    Sources are the distinct documents that were actually fed to the model,
    in retrieval-rank order.
    """
    query = (query or "").strip()
    if not query:
        return {"answer": "Please enter a question.", "sources": [], "hits": []}

    hits = retrieve(query, top_k=top_k)
    if not hits:
        return {"answer": NO_ANSWER, "sources": [], "hits": []}

    response = get_client().chat.completions.create(
        model=GROQ_MODEL,
        messages=build_messages(query, hits),
        temperature=0,  # deterministic, grounded answers
    )
    answer = response.choices[0].message.content.strip()

    # Distinct sources in rank order (de-duplicated, preserving first-seen order).
    sources = list(dict.fromkeys(h["source"] for h in hits))
    return {"answer": answer, "sources": sources, "hits": hits}


def format_response(result: dict) -> str:
    """Format as: answer + a Markdown Sources list (the output format spec)."""
    answer = result["answer"]
    if not result["sources"] or answer == NO_ANSWER:
        return answer
    source_lines = "\n".join(f"- {s}" for s in result["sources"])
    return f"{answer}\n\n**Sources:**\n{source_lines}"


# --- Gradio interface --------------------------------------------------------

EXAMPLE_QUESTIONS = [
    "What is Prof. Dina Sokol's overall rating?",
    "What is Prof. Deborah Elefant's level of difficulty?",
    "How does Brooklyn College's CS program compare to NYU and Columbia?",
]


def _ui_handler(query: str) -> str:
    """Gradio callback: question string -> formatted answer + sources."""
    return format_response(answer_question(query))


def build_interface() -> gr.Blocks:
    """Construct the Gradio app skeleton (no network calls at build time)."""
    with gr.Blocks(title="The Unofficial Guide") as demo:
        gr.Markdown(
            "# The Unofficial Guide — Brooklyn College CS\n"
            "Ask about CS courses and professors. Answers come **only** from the "
            "retrieved source documents, with attribution."
        )
        with gr.Row():
            query_box = gr.Textbox(
                label="Your question",
                placeholder="e.g. What is Prof. Sokol's overall rating?",
                lines=2,
                scale=4,
            )
            ask_btn = gr.Button("Ask", variant="primary", scale=1)

        answer_box = gr.Markdown(label="Answer")

        gr.Examples(examples=EXAMPLE_QUESTIONS, inputs=query_box)

        ask_btn.click(fn=_ui_handler, inputs=query_box, outputs=answer_box)
        query_box.submit(fn=_ui_handler, inputs=query_box, outputs=answer_box)

    return demo


def main() -> None:
    build_interface().launch(share=True)


if __name__ == "__main__":
    main()
