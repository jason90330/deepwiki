---
name: deepwiki-generator
description: >-
  Generate DeepWiki-grade multi-page documentation, architecture diagrams, and interactive
  knowledge graphs by dynamically linking an already-indexed codebase-memory-mcp project
  with an existing llm-wiki collection or HTTP/Qdrant RAG collection. Use when the user
  provides a codebase-memory-mcp index name and an llm-wiki or RAG collection and wants to
  link code symbols/subsystems with documents to generate or update a DeepWiki.
---

# DeepWiki Generator & Dynamic Knowledge Linker

## Overview

`deepwiki-generator` turns an already-indexed **`codebase-memory-mcp` code graph** plus an existing **`llm-wiki` collection** (Karpathy's 3-layer `raw/` + `wiki/` + `AGENTS.md` architecture) or **HTTP/Qdrant RAG collection** into a complete, interactive **DeepWiki**:

1. **Code Graph Extraction (`structure.json`)**: Pulls `Class`, `Struct`, `Interface`, `Function`, and `Method` nodes plus `CALLS` / `IMPORTS` / `INHERITS` edges from `codebase-memory-mcp`, and clusters files into Louvain architectural communities.
2. **2-Level DeepWiki Outline (`outline.json`)**: Plans a hierarchical numbered page tree (`1`, `1.1`, `1.2`, `2`, `2.1`...) matching DeepWiki's navigation structure.
3. **3-Way Dynamic Knowledge Linking (`knowledge_links.json` + `graph.json`)**:
   - **Entity Linking (`doc_to_symbols`, `doc_to_files`)**: Matches exact code symbols (`INetwork`, `IOptimizedNetwork`, `LoadedNetwork`, `WorkloadFactory`, etc.) and file paths mentioned inside `llm-wiki` or RAG chunks to their `codebase-memory-mcp` definitions (`[file:start-end]()`).
   - **Lexical + 1-Hop Graph Expansion (`page_to_docs`)**: Queries `WikiRAG` (BM25 + 1-hop `[[wikilink]]` traversal) and/or an HTTP/Qdrant RAG endpoint per subsystem page, boosting documents that share code symbols with the subsystem.
   - **Bridge Symbol & Coupling Discovery (`page_to_bridges`)**: Identifies high fan-in/fan-out bridge classes/functions and cross-subsystem call/import weights.
4. **DeepWiki Synthesis & Interactive Viewer (`wiki/*.md`, `index.md`, `log.md`, `serve`)**:
   - Produces or enriches every `wiki/<id>.md` page with YAML frontmatter, `<details><summary>Relevant source files</summary>`, multi-diagram Mermaid blocks (`graph TD`, `classDiagram`, `sequenceDiagram`), `Sources: [file:start-end]()` citations, and a `## Dynamic Knowledge Links (Code Graph ↔ LLM-Wiki / RAG)` table.
   - Serves a 3-column DeepWiki web UI with natural-size 16px Mermaid diagrams (Pan, Ctrl+Wheel Zoom, Fit, Fullscreen) and an interactive force-directed graph modal (`Page`, `Doc`, `Symbol`, `File`).

## Dependencies

- **`codebase-memory-mcp`**: Binary installed at `/home/jason/.local/opt/cbm/codebase-memory-mcp` (auto-discovered by `wikigen.cbm.find_binary()`).
- **`wikigen` package**: Located at `/home/jason/Project/deepwiki/wikigen`.

## Quick Start

Given an existing `codebase-memory-mcp` project (e.g., `home-jason-Project-deepwiki-armnn`) and an `llm-wiki` directory (e.g., `/home/jason/Project/deepwiki/llm-wiki`):

```bash
python3 /home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py build \
  --project home-jason-Project-deepwiki-armnn \
  --out-dir /home/jason/Project/deepwiki/llm-wiki \
  --llm-wiki /home/jason/Project/deepwiki/llm-wiki \
  --source-url https://github.com/ARM-software/armnn/blob/branches/armnn_24_11 \
  --output /home/jason/Project/deepwiki/llm-wiki/wiki/link_summary.json
```

Or directly via the `wikigen` module:

```bash
cd /home/jason/Project/deepwiki
python3 -m wikigen link \
  -p home-jason-Project-deepwiki-armnn \
  -o llm-wiki \
  --llm-wiki llm-wiki \
  --source-url https://github.com/ARM-software/armnn/blob/branches/armnn_24_11
```

## Utility Scripts

All commands use `/home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py` and write structured JSON results to `--output`.

### 1. `build` — Dynamically Link Code Graph + LLM-Wiki / RAG & Generate DeepWiki

Links a `codebase-memory-mcp` project index with an `llm-wiki` workspace and/or an HTTP/Qdrant RAG server:

```bash
# With llm-wiki collection:
python3 /home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py build \
  --project <cbm-project-name> \
  --out-dir <path-to-llm-wiki> \
  --llm-wiki <path-to-llm-wiki> \
  --source-url <github-or-gitlab-blob-base-url> \
  --output <path-to-summary.json>

# With HTTP / Qdrant RAG collection (e.g. ~/Project/rag on :8005 or Qdrant on :6333):
python3 /home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py build \
  --project <cbm-project-name> \
  --out-dir <path-to-output-wiki> \
  --rag-url http://127.0.0.1:8005 \
  --rag-collection <collection-name> \
  --output <path-to-summary.json>
```

Key flags:
- `--refresh-structure`: Re-extract `structure.json` from `codebase-memory-mcp` even if cached.
- `--enrich-only`: Preserve existing hand-crafted/agent-authored prose in `wiki/*.md` and only inject/update the `## Dynamic Knowledge Links` section, frontmatter metadata, `knowledge_links.json`, and `graph.json`.

### 2. `query` — Query the Linked `llm-wiki` Collection

Retrieves relevant wiki pages and raw documents using BM25 + 1-hop `[[wikilink]]` graph expansion:

```bash
python3 /home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py query \
  --wiki-dir /home/jason/Project/deepwiki/llm-wiki \
  --query "Optimize Graph SubgraphView WorkloadFactory" \
  --limit 5 \
  --output /tmp/deepwiki_query.json
```

### 3. `lint` — Verify `[[wikilinks]]` and Orphan Pages

```bash
python3 /home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py lint \
  --wiki-dir /home/jason/Project/deepwiki/llm-wiki \
  --output /tmp/deepwiki_lint.json
```

### 4. `serve` — Launch the DeepWiki Web UI

```bash
python3 /home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py serve \
  --wiki-dir /home/jason/Project/deepwiki/llm-wiki \
  --port 8765
```

## Workflow for Agent-Authored DeepWiki Synthesis

When asked to build a brand-new DeepWiki for a repository `<repo>` whose `codebase-memory-mcp` index is `<project>`:

1. **Prepare `llm-wiki` 3-Layer Layout**:
   - Ensure `<wiki-dir>/raw/` contains official repository docs (`README.md`, `docs/`, `*.dox`), `<wiki-dir>/wiki/` exists, and `<wiki-dir>/AGENTS.md` defines the schema.
2. **Run `build` to Extract Code Graph & Discover Dynamic Links**:
   - Run `deepwiki_cli.py build --project <project> --out-dir <wiki-dir> --llm-wiki <wiki-dir> --output <wiki-dir>/wiki/link_summary.json`.
   - Inspect `<wiki-dir>/wiki/outline.json` and `<wiki-dir>/wiki/knowledge_links.json`.
3. **Author / Refine DeepWiki Pages (Optional Agent Pass)**:
   - Using `structure.json` and `knowledge_links.json`, write or refine `wiki/<id>.md` with rich architectural prose, 2–4 Mermaid diagrams (`graph TD`, `classDiagram`, `sequenceDiagram`), `<details><summary>Relevant source files</summary>`, and `Sources: [file:start-end]()` citations.
   - Re-run `deepwiki_cli.py build --enrich-only ...` to attach the `## Dynamic Knowledge Links` tables and rebuild `graph.json`.
4. **Lint & Serve**:
   - Run `deepwiki_cli.py lint` to verify `broken_links == []` and `orphans == []`.
   - Serve via `deepwiki_cli.py serve --wiki-dir <wiki-dir> --port 8765`.

## Common Mistakes

- **Mermaid `[["..."]]` subroutine nodes parsed as wikilinks**: Always strip fenced code blocks (` ```...``` `) before extracting or replacing `[[wikilinks]]` (handled automatically by `wikigen`).
- **Slow one-shot CLI queries on 20k+ node repos**: Start `codebase-memory-mcp daemon start` before running `--refresh-structure` on large C++ repositories.
