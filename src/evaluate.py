"""Retrieval evaluation — compare top-k settings on the planning.md test set.

Runs the 5 evaluation questions from planning.md through the retriever at
several k values and reports, for each, whether the chunk that actually
contains the expected answer was retrieved (and at what rank).

This isolates the RETRIEVAL stage: it checks "did the right chunk make the
cut?", not whether the LLM later words the answer correctly.

Run:
    python src/evaluate.py            # compares k=3 and k=5
    python src/evaluate.py 3 5 10     # compare any k values you pass
"""

from __future__ import annotations

import sys

from vector_store import retrieve

# Each question is paired with the chunk that holds its expected answer
# (source filename prefix + chunk_index), verified by hand against chunks.json.
EVAL = [
    {
        "q": "How does Brooklyn College's CS program compare to NYU and Columbia?",
        "expected": "Brooklyn College = smaller/personalized vs. NYU/Columbia prestige",
        "gold_source": "CollegeVine",
        "gold_index": 2,
    },
    {
        "q": "Which Computer Science course teaches big-O notation?",
        "expected": "Data Structures (CISC 3130)",
        "gold_source": "CISC3130",
        "gold_index": 3,
    },
    {
        "q": "What is Prof. Dina Sokol's overall rating?",
        "expected": "3.7",
        "gold_source": "Sokol",
        "gold_index": 0,
    },
    {
        "q": "What is Prof. Deborah Elefant's level of difficulty?",
        "expected": "3",
        "gold_source": "Elefant",
        "gold_index": 0,
    },
    {
        "q": "How many credits is CISC 3150?",
        "expected": "3 credits",
        "gold_source": "CISC_3150",
        "gold_index": 0,
    },
]


def gold_rank(query: str, gold_source: str, gold_index: int,
              search_depth: int = 49) -> tuple[int | None, float | None]:
    """Return (rank, score) of the expected chunk, searching the whole corpus.

    rank is 1-based; None means the chunk was never retrieved.
    """
    for i, hit in enumerate(retrieve(query, top_k=search_depth), 1):
        if hit["source"].startswith(gold_source) and hit["chunk_index"] == gold_index:
            return i, hit["score"]
    return None, None


def run(k_values: list[int]) -> None:
    header = "Q  Expected answer".ljust(40) + "".join(
        f"k={k}".center(10) for k in k_values
    ) + "  gold rank"
    print(header)
    print("-" * len(header))

    hits_by_k = {k: 0 for k in k_values}

    for n, case in enumerate(EVAL, 1):
        rank, score = gold_rank(case["q"], case["gold_source"], case["gold_index"])
        cells = ""
        for k in k_values:
            found = rank is not None and rank <= k
            hits_by_k[k] += found
            cells += ("HIT" if found else "miss").center(10)
        rank_str = f"#{rank} ({score})" if rank else "not retrieved"
        label = f"{n}  {case['expected']}"[:38].ljust(40)
        print(label + cells + f"  {rank_str}")

    print("-" * len(header))
    summary = "   Recall@k".ljust(40) + "".join(
        f"{hits_by_k[k]}/{len(EVAL)}".center(10) for k in k_values
    )
    print(summary)

    print("\nPer-question detail (top results at largest k):")
    kmax = max(k_values)
    for n, case in enumerate(EVAL, 1):
        print(f"\nQ{n}: {case['q']}")
        print(f"    expected: {case['expected']}")
        for i, hit in enumerate(retrieve(case["q"], top_k=kmax), 1):
            mark = "<-- gold" if (
                hit["source"].startswith(case["gold_source"])
                and hit["chunk_index"] == case["gold_index"]
            ) else ""
            text = " ".join(hit["text"].split())[:75]
            print(f"    {i}. [{hit['source']} #{hit['chunk_index']}] "
                  f"{hit['score']}  {text} {mark}")


def main() -> None:
    args = sys.argv[1:]
    bad = [a for a in args if not a.isdigit()]
    if bad:
        print(f"Ignoring non-integer argument(s): {' '.join(bad)}")
        print("Usage: python src/evaluate.py [K ...]   e.g.  python src/evaluate.py 3 5 10")
    k_values = [int(a) for a in args if a.isdigit()] or [3, 5]
    run(sorted(set(k_values)))


if __name__ == "__main__":
    main()
