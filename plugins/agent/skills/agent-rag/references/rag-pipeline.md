# RAG pipeline per framework

Checked against mastra.ai and docs.langchain.com on 2026-10-23. Confirm every export on the **installed** package (`node_modules/<pkg>/package.json` → `exports`, or its `.d.ts`) before relying on it; resolve versions at install time and pin them exactly.

## Official layouts to mirror

| Framework | Repo · path | Layout |
|-----------|-------------|--------|
| LangGraph | `langchain-ai/retrieval-agent-template-js` · `src/retrieval_graph/` | `index_graph.ts` (ingest graph) apart from `graph.ts` (retrieval graph), `retrieval.ts` (vector store factory), `configuration.ts`, `prompts.ts`, `state.ts`, `tests/` |
| LangGraph (agentic RAG) | docs: `oss/javascript/langgraph/agentic-rag` | `generateQueryOrRespond` → `retrieve` (ToolNode) → `gradeDocuments` edge → `generate` or `rewrite` → back |
| Mastra | `mastra-ai/mastra` · `templates/template-chat-with-pdf`, `template-company-knowledge` | `src/mastra/workflows/` (ingest) · `tools/` (retrieval) · `agents/` · `lib/` |

Ingest is always its own graph, workflow or script, never a step inside the chat turn.

## Mastra

```ts
import { MDocument } from '@mastra/rag'
import { ModelRouterEmbeddingModel } from '@mastra/core/llm'
import { embedMany } from 'ai'
import { PgVector } from '@mastra/pg'            // or LibSQLVector from '@mastra/libsql'

const chunks = await MDocument.fromMarkdown(text).chunk({ strategy: 'markdown', maxSize: 512, overlap: 50 })
const { embeddings } = await embedMany({ model: embedder, values: chunks.map(c => c.text) })
await store.createIndex({ indexName, dimension })            // = the model's output size
await store.upsert({ indexName, vectors: embeddings, metadata, ids })
await store.deleteVectors({ indexName, filter: { sourceId } })   // before re-ingesting a source
await store.query({ indexName, queryVector, topK, filter, minScore })
```

- `createVectorQueryTool({ vectorStoreName, indexName, model, enableFilter, reranker, includeSources })` exists, but its `filter` can come from the model's input or `requestContext`, and the docs do not say which wins. For tenant isolation, write the retrieval tool with `createTool` and call `store.query` with `{ ...modelFilter, tenantId }` built in `execute` from `requestContext`. Alternatively, resolve a per-tenant store or namespace on the server.
- Rerank: `rerank()` / `rerankWithScorer()` from `@mastra/rag`.
- Semantic memory: `new Memory({ storage, vector, embedder, options: { semanticRecall: { topK, messageRange, scope: 'resource' } } })`. It is off by default and needs `vector` + `embedder`.
- Evals: the Faithfulness, Context Relevance, Context Precision and Context Recall scorers.

## LangChain / LangGraph

- Splitters: `RecursiveCharacterTextSplitter` (and markdown-aware splitters) from `@langchain/textsplitters`.
- Embeddings and vector stores: the provider package (e.g. `OpenAIEmbeddings` from `@langchain/openai`) and a store from the vector store integrations index. Check the import path on the installed version. The tutorial's `MemoryVectorStore` and `createRetrieverTool` come from `@langchain/classic`: fine for a demo, but for production write the retrieval tool with `tool()` and a server-side filter.
- Retrieval tool: `tool(async ({ query }, config) => store.similaritySearchWithScore(query, k, { ...filter, tenantId }), { name, description, schema })`, with `tenantId` read from trusted context (`config.configurable` / request scope). Filter syntax is store-specific; read the store's docs.
- Semantic memory: a LangGraph Store with `index: { embeddings, dims, fields }`, then `store.put(namespace, key, value)` and `store.search(namespace, { query, limit })`. On LangSmith deployments, configure `store.index` in `langgraph.json` instead of in code.

## Metadata every chunk carries

`tenantId` (or the ACL key) · `sourceId` · `chunkIndex` · `title` · `url` · `updatedAt` · `embeddingModel` · `dims` · `chunkerVersion`. The id is `<sourceId>#<chunkIndex>`.
