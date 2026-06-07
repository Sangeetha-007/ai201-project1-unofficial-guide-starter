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
| 1 | RateMyProfessor | |https://www.ratemyprofessors.com/professor/2995207 |
| 2 | RateMyProfessor | |https://www.ratemyprofessors.com/professor/167158|
| 3 | RateMyProfessor | |https://www.ratemyprofessors.com/professor/334831 |
| 4 | RateMyProfessor| | https://www.ratemyprofessors.com/professor/2722205 |
| 5 | RateMyProfessor | | https://www.ratemyprofessors.com/professor/156077 |
| 6 | Reddit | | https://www.reddit.com/r/CUNY/comments/1ci3hcu/brooklyn_college_professor_review_cisc/ |
| 7 | CollegeVine | | https://www.collegevine.com/faq/40319/thoughts-on-computer-science-program-at-brooklyn-college |
| 8 | Introduction to Programming Using C++ Syllabus | | /Users/sangeetha/Downloads/CISC1110.pdf |
| 9 | Data Structures Syllabus | | /Users/sangeetha/Downloads/CISC3130.pdf |
| 10 | Object-Oriented Programming Syllabus | | /Users/sangeetha/Downloads/CISC_3150.pdf |

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

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

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

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
