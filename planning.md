# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
The domain I chose is "course and professor reviews". While I was a Brooklyn College Student for my undergraduate degree, it was hard to locate information about professors because information was not in one location and rather from different sources. This makes the information valuable. 
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | RateMyProfessor | Review Site of Professors, review of Prof. Panneer Santhalingam |https://www.ratemyprofessors.com/professor/2995207 |
| 2 | RateMyProfessor | Review Site of Professors, review of Prof. Murray Gross |https://www.ratemyprofessors.com/professor/167158|
| 3 | RateMyProfessor | Review Site of Professors, review of Prof. Dina Sokol |https://www.ratemyprofessors.com/professor/334831 |
| 4 | RateMyProfessor| Review Site of Professors, review of Prof. Adele Piontnica | https://www.ratemyprofessors.com/professor/2722205 |
| 5 | RateMyProfessor | Review Site of Professors, review of Prof. Deborah Elefant | https://www.ratemyprofessors.com/professor/156077 |
| 6 | Reddit | Online Forum | https://www.reddit.com/r/CUNY/comments/1ci3hcu/brooklyn_college_professor_review_cisc/ |
| 7 | CollegeVine | | https://www.collegevine.com/faq/40319/thoughts-on-computer-science-program-at-brooklyn-college |
| 8 | Introduction to Programming Using C++ Syllabus | Pdf File | /Users/sangeetha/Downloads/CISC1110.pdf |
| 9 | Data Structures Syllabus | Pdf File | /Users/sangeetha/Downloads/CISC3130.pdf |
| 10 | Object-Oriented Programming Syllabus | Pdf File | /Users/sangeetha/Downloads/CISC_3150.pdf |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

Hybrid: Semantic Chunking and Retrieval Chunking

**Chunk size:**
Chunk size =128
**Overlap:**
Overlap = 13

Overlap defines how much text is shared between consecutive chunks. It is typically used to avoid losing important information at chunk boundaries. A small overlap reduces redundancy but risks cutting explanations in half, while a larger overlap increases robustness at the cost of storing and processing more similar chunks.

**Reasoning:**

---
My sources are online reviews, forums and short documents (2-3 pages). This is why I started the chunk size with a low number (128). I
will increase it if needed. Overlap is considered best if its 10-12% of chunk size so I chose 13 (rounded up from 12.8)

<!--
- Are your documents short reviews (1–3 sentences) or long guides (many paragraphs)? How does that affect the right chunk size?
- If a key fact spans two adjacent chunks, will either chunk be retrievable on its own? What does overlap help with?
- How would you know if your chunks are too small? Too large? What would bad retrieval results look like in each case? -->

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

     sentence-transformers (all-MiniLM-L6-v2) is the embedding model I will be using. 
     The chunk size I hope to use is 128. 

**Embedding model:**
sentence-transformers (all-MiniLM-L6-v2)

**Top-k:**
Initial choice: Top-k=3
The number of retrieved results specifies how many text segments are returned by the retrieval step. A small Top-k can miss relevant context, while a large Top-k increases recall but may introduce noise.

Changed to: Top-k=5

**Production tradeoff reflection:**

So k=10 rescues exactly one of your two failures.

Why that rescue isn't worth it:

Q5's gold chunk sits at rank #10 with score 0.38 — the lowest of the ten, below nine chunks scoring 0.42–0.47 that are not about CISC 3150 credits (Piontnica reviews, Sokol's rating header, a Reddit thread). You'd be handing the LLM the right answer buried under 9 higher-scoring distractors. That's precisely the "dilute the context and pull the response off-target" failure your prompt warns about — the correct chunk being present doesn't mean it wins.
You'd double the context size (and token cost) for every single query to salvage one question, and degrade the 3 questions that currently retrieve cleanly at #1.
The honest conclusion: Q2 and Q5 are a ranking problem, not a k problem. Cranking k doesn't fix a chunk that ranks #10–15; it just floods generation with noise. The right fixes are retrieval-side:

Hybrid keyword + vector search — "3150" and "big-O" are exact terms the embedding model underweights; a keyword signal would pull both gold chunks up fast.
A stronger embedding model (e.g. bge-small-en) — better on short text with course codes.


---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | How does Brooklyn College's CS program compare to NYU and Columbia? | If you value small class sizes and a more personalized learning experience, Brooklyn College's CS program might be a better fit compared to larger, more renowned programs at institutions like NYU or Columbia. However, if prestige and connections to big tech companies are more important to you, the programs at NYU/Columbia may provide more of what you're looking for. |
| 2 | Which Computer Science course teaches big-O notation? | Data Structures |
| 3 | What's Prof. Dina Sokol's overall rating? | 3.7 |
| 4 | What's Prof. Deborah Elefant's level of difficulty? | 3 |
| 5 | How many credits is CISC 3150? | 3 credits |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Wrong Overlap Used

2. Inconsistent documents due to webscraping RateMyProfessor

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

![Pipeline](images/architecture.png)

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

     I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap. I gave low values for chunk size and overlap, which may need to be
     changed based on needs later. 

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
