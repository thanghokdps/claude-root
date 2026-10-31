---
model: opus
effort: high
name: agent-rag
description: Adds retrieval (RAG), embeddings, a vector store or semantic long-term memory to a Mastra, LangChainJS or LangGraph assistant. It covers the ingest pipeline (load, chunk, embed, index with model metadata), the vector store choice, a retrieval read tool with a server-side tenant filter and citations, semantic recall scoped to the trusted user, re-embedding on a model change, and retrieval evals. Use when the assistant must answer from documents or a knowledge base, remember users across threads by meaning, or when retrieval returns wrong, stale or another tenant's content.
when_to_use: RAG, "thêm RAG cho chatbot", "chatbot trả lời từ tài liệu", "cho agent trả lời từ tài liệu", "mỗi tenant chỉ thấy tài liệu của mình", embeddings, vector store, pgvector, Pinecone, Qdrant, chunking, knowledge base, semantic search, semantic recall, vector memory, "nhớ người dùng qua các cuộc hội thoại", retrieval returns irrelevant or another customer's documents, change embedding model
---

# agent-rag

**Invoke:** `/agent-rag <what the assistant must answer from, or remember>`

Retrieval is a read tool whose filter is an authorisation check, fed by an ingest pipeline that is versioned like a schema. Rules: `${CLAUDE_PLUGIN_ROOT}/rules/agent-identity-and-tools.md`, plus `${CLAUDE_PLUGIN_ROOT}/rules/langgraph.md` or `${CLAUDE_PLUGIN_ROOT}/rules/mastra.md`. Framework APIs and the official layouts are in `${CLAUDE_SKILL_DIR}/references/rag-pipeline.md`.

---

## Step 1 — Detect and decide what kind of retrieval

Run the detection in `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/shapes.md`, then look for an existing vector store, embedder, ingest job and retrieval tool. Reuse them: a second index for the same corpus is a defect.

Name which need this is. They are built differently:

| Need | Built as |
|------|----------|
| Answer from documents or a knowledge base the team owns | Ingest pipeline + retrieval read tool (Steps 2–4) |
| Remember a user across threads by meaning | Semantic memory (Step 5), not a document index |
| A structured lookup by id, date, status | A normal tool via `/agent-tool`. Do not use embeddings |

**Done when:** the need, the corpus (source, size, owner, update rate, who may read what) and the existing pieces are stated with file paths. Any new store, corpus or tenant model not in the ADR → stop and ask (`/agent-feature` Step 2).

## Step 2 — Ingest pipeline

Separate from the chat path: a workflow or script (`ingest`), never run inside a user turn. Use the official layout and calls in `rag-pipeline.md`.

1. Load → normalise to text with its source (url or path, title, section, updated_at).
2. Chunk by the document's structure (markdown headings, pages) before size. Start at ~256–512 tokens with ~10–15% overlap, then tune with Step 6 numbers, not by feel.
3. Embed in batches with retry on 429/5xx.
4. Upsert with a **stable id** (`<sourceId>#<chunkIndex>`) and metadata on every chunk: `tenantId` (or the ACL key), `sourceId`, `title`, `url`, `updatedAt`, `embeddingModel`, `dims`, `chunkerVersion`.
5. Re-ingesting a source deletes its old chunks by `sourceId` first, so edited or removed content stops being answered.

- Changing the embedding model, its dimensions or the chunker is a re-index into a **new** index, switched over after Step 6 passes on it. Never mix vectors from two models in one index.
- PII and secrets: index nothing the ADR has not cleared. Strip or mask it in step 1.

**Done when:** tests cover chunk ids being stable across runs, a re-ingest removing stale chunks, and metadata present on every chunk. A dry run on a sample source reports the chunk count and token sizes.

## Step 3 — Vector store

Pick it in the ADR (Q6). Default to the database the app already runs (`pgvector` on Postgres, libSQL), and use a hosted store (Pinecone, Qdrant…) only for a measured reason (size, latency, a filter it needs). One store client, built once at module level; its connection string goes in the env schema. `dimension` at `createIndex` must equal the embedding model's output.

**Done when:** the ADR records the store, index name, embedding model and dims, and the index is created by the scaffold or a migration, not by hand.

## Step 4 — Retrieval tool

A read tool built through `/agent-tool`, with these extra rules:

- The model provides only `query` (and maybe a topic filter from a fixed enum). `tenantId` and ACL keys come from trusted context and are merged **AND** into the store filter by the tool, never taken from the model. A stock query tool whose filter the model can set is not the boundary on its own (`rag-pipeline.md`).
- `topK` 4–8, a `minScore` floor, and optional rerank. Return compact chunks with `{ text, title, url, sourceId }` so the answer can cite them.
- The prompt says: answer from the retrieved chunks, cite them, and say "not found in the documents" when nothing passes the floor. Never fall back to the model's memory for a documented domain.
- Retrieved text is untrusted input (prompt injection): it never changes tools, scope or instructions (`/agent-security`).

**Done when:** tests assert that a tenant-A user never gets tenant-B chunks (even when the query names B), an empty result gives the "not found" answer, and results carry citations. Then prove one turn with `/agent-verify-turn`.

## Step 5 — Semantic memory (when the need is "remember the user")

- Mastra: `Memory` with `vector` + `embedder` and `options.semanticRecall` (`topK`, `messageRange`, `scope: 'resource'` for across threads). The resource is `MASTRA_RESOURCE_ID_KEY` from the verified request.
- LangGraph: a Store with `index: { embeddings, dims, fields }`. Use `store.put` / `store.search` under the namespace `["memories", userId, kind]`, with `userId` from trusted context.
- Saved memories are tool calls the user can see and delete. Recalled memory is untrusted input, like a retrieved chunk.

**Done when:** tests show user A's memories never surface for user B, and a delete removes the memory from search.

## Step 6 — Evals

Through `/agent-evals`, with a golden set of real questions from P2 (each with the source that answers it, plus out-of-corpus questions):

- Retrieval: recall@k and precision of the expected `sourceId`. This runs without the LLM, so it is cheap enough for every ingest change.
- Answer: faithfulness / groundedness and citation correctness (Mastra scorers or an LLM judge), and "not found" on out-of-corpus questions.
- The baseline is recorded. A chunker, model or `topK` change must not drop it.

**Done when:** both suites run in CI against a fixed fixture corpus, with the baseline numbers in the PR.

---

## Hand-offs

Retrieval tool → `/agent-tool` · scope or a dedicated retrieval agent → `/agent-graph` · injection and data-leak threat model → `/agent-security` · eval suite → `/agent-evals` · citations in the chat UI → `/agent-frontend` · then `/verify-done` → `/review-checklist`.
