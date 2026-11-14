# DeepWiki Generator (`wikigen` + `llm-wiki`)

Generate [DeepWiki](https://deepwiki.com)-grade multi-page documentation, architecture diagrams, and interactive knowledge graphs by dynamically linking a **`codebase-memory-mcp` code graph** with an **`llm-wiki` collection** (Karpathy's 3-layer knowledge base architecture) or an **HTTP/Qdrant RAG collection**.

## Repository Structure

```text
deepwiki/
├── SKILL.md                                           # Agent Skill specification (deepwiki-generator)
├── .agents/skills/deepwiki-generator/                 # Workspace-discoverable Agent Skill + CLI script
│   ├── SKILL.md
│   └── scripts/deepwiki_cli.py
├── wikigen/                                           # Core Python package (zero external LLM API required)
│   ├── cbm.py                                         # codebase-memory-mcp CLI client (cursor pagination)
│   ├── extract.py                                     # Code graph extraction + Louvain community detection
│   ├── plan.py                                        # Deterministic 2-level numbered DeepWiki outline planner
│   ├── pages.py                                       # DeepWiki page & Mermaid diagram synthesizer
│   ├── wiki_rag.py                                    # BM25 + 1-hop [[wikilink]] retrieval & lint engine
│   ├── link.py                                        # 3-way Dynamic Knowledge Linker (CBM <-> llm-wiki / RAG)
│   ├── render.py                                      # Markdown & frontmatter renderer
│   ├── serve.py                                       # 3-column DeepWiki Web Server (/api/catalog, /api/graph, /api/ask)
│   ├── cli.py                                         # Unified CLI entrypoint (`python3 -m wikigen ...`)
│   └── static/index.html                              # Interactive Web UI (Pan/Zoom/Fullscreen Mermaid + Force Graph)
└── llm-wiki/                                          # Karpathy 3-Layer LLM-Wiki (Arm NN DeepWiki instance)
    ├── llm-wiki.md                                    # Original Karpathy llm-wiki specification
    ├── AGENTS.md                                      # Layer 3: Schema & operational rules
    ├── CLAUDE.md                                      # Pointer to AGENTS.md
    ├── raw/armnn/                                     # Layer 1: Immutable raw official docs + structure.json
    └── wiki/                                          # Layer 2: 26 DeepWiki pages + outline.json + knowledge_links.json + graph.json
```

## Quick Start

### 1. Dynamically Link a `codebase-memory-mcp` Index + `llm-wiki` / `RAG` Collection

```bash
# Link an existing codebase-memory-mcp index with an llm-wiki directory:
python3 -m wikigen link \
  -p home-jason-Project-deepwiki-armnn \
  -o llm-wiki \
  --llm-wiki llm-wiki \
  --source-url https://github.com/ARM-software/armnn/blob/branches/armnn_24_11

# Or link with an HTTP / Qdrant RAG collection:
python3 -m wikigen link \
  -p <cbm-project-name> \
  -o <output-wiki-dir> \
  --rag-url http://127.0.0.1:8005 \
  --rag-collection <collection-name>
```

### 2. Query & Lint the `llm-wiki` Collection

```bash
# BM25 + 1-hop [[wikilink]] retrieval:
python3 -m wikigen wiki-query llm-wiki -q "Optimize Graph SubgraphView WorkloadFactory"

# Health-check broken [[wikilinks]] and orphan pages:
python3 -m wikigen wiki-lint llm-wiki
```

### 3. Start the Interactive DeepWiki Web Viewer

```bash
python3 -m wikigen serve llm-wiki --port 8765
# Open http://127.0.0.1:8765
```
