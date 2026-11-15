# DeepWiki Generator (`wikigen`: `git` + `CBM` + `llm-wiki`)

Generate [DeepWiki v1.9.9.5](https://deepwiki.com)-grade multi-page documentation, architecture diagrams, and interactive knowledge graphs by dynamically linking **three complementary knowledge sources**:

1. **`git` Repository Working Tree**: Directory structure, build configurations (`CMakeLists.txt`, `targets.bzl`, `BUCK`, `pyproject.toml`, `.fbs`), and exact source code excerpts (`file:start-end`).
2. **`codebase-memory-mcp` (CBM) Code Graph**: Indexed `Class`, `Struct`, `Interface`, `Function`, and `Method` definitions, `INHERITS` hierarchies, `CALLS`/`IMPORTS` edges, fan-in/fan-out centrality, and Louvain communities.
3. **`llm-wiki` Collection (or HTTP/Qdrant RAG)**: Karpathy's 3-layer knowledge base (`raw/` immutable official docs + `wiki/` synthesized pages + `AGENTS.md` schema) retrieved via BM25 + 1-hop `[[wikilink]]` graph expansion.

Designed for both **deterministic zero-API synthesis** and **local OpenAI-compatible LLMs** such as **`deepseek-v4-flash-0731`** (`--llm-base-url` / `--llm-model`, plus `< 10 KB` context-safe per-page packets).

---

## Reverse-Engineered DeepWiki v1.9.9.5 Features (`rea` Spec)

- **Canonical 10-Section Lifecycle Taxonomy**: Automatically structures repositories into `1. Overview` (`1.1 Getting Started`, `1.2 High-Level API`), `2. Build System & Infrastructure`, Compiler/IR, Quantization/Optimization, Pluggable Hardware Backends (with `Other Backends` consolidation), Model/App Verticals, `Testing & CI/CD`, `Runtime Execution`, `Platform Extensions`, and `Glossary`.
- **4 Distinct Page Archetypes**:
  1. **Top-Level `1-overview`**: System component map, `Natural Language Space ↔ Code Entity Space` bridge diagram, core class hierarchy, subsystem navigation matrix, and entry points.
  2. **Parent Hub Pages (`2`, `3`, `5`, `8`...)**: `## Purpose and Scope` + one section and dedicated Mermaid architecture diagram per child subsystem page.
  3. **Leaf Technical Spec Pages (`1.1`, `3.1`, `8.1`...)**: `## Purpose and Scope`, numbered `## 1..5` sections separated by `---`, **4 Mermaid diagrams** (`Natural Language Space ↔ Code Entity Space`, `flowchart TD`, `classDiagram`, `sequenceDiagram`), real `git` source code blocks, and API reference tables.
  4. **`Glossary` (`10-glossary` / `*-glossary`)**: Domain vocabulary and binary formats mapped directly to `Code Entity Space` classes/structs.
- **Interactive Split GitHub Citation Pills**: Every `[path/to/file.ext:start-end]()` citation renders as DeepWiki's split pill badge (`path/to/file.ext | start-end`) linking directly to `#Lstart-Lend`.

---

## Repository Structure

```text
deepwiki/
├── SKILL.md                                           # Agent Skill specification (deepwiki-generator)
├── .agents/skills/deepwiki-generator/                 # Workspace-discoverable Agent Skill + CLI script
│   ├── SKILL.md
│   └── scripts/deepwiki_cli.py
├── wikigen/                                           # Core Python package
│   ├── cbm.py                                         # codebase-memory-mcp CLI client (cursor pagination)
│   ├── extract.py                                     # Code graph extraction + Louvain community detection
│   ├── plan.py                                        # 3-Source (git + CBM + llm-wiki) DeepWiki v1.9.9.5 outline planner & Repo Dossier
│   ├── pages.py                                       # 4-Archetype DeepWiki page & 4-diagram synthesizer + git code slicer
│   ├── llm.py                                         # Local OpenAI-compatible client (e.g. deepseek-v4-flash-0731) + DeepWiki v1.9.9.5 prompts
│   ├── wiki_rag.py                                    # BM25 + 1-hop [[wikilink]] retrieval & lint engine
│   ├── link.py                                        # 3-way Dynamic Knowledge Linker + 3-Source Page Context Packets
│   ├── render.py                                      # Markdown & frontmatter renderer
│   ├── serve.py                                       # 3-column DeepWiki Web Server (/api/catalog, /api/graph, /api/ask)
│   ├── cli.py                                         # Unified CLI entrypoint (`python3 -m wikigen ...`)
│   └── static/index.html                              # Interactive Web UI (Split GitHub Citation Pills + Pan/Zoom Mermaid + Force Graph)
├── llm-wiki/                                          # Arm NN DeepWiki instance (25 pages, 99 Mermaid diagrams)
└── llm-wiki-executorch/                               # PyTorch ExecuTorch DeepWiki instance (46 pages, 191 Mermaid diagrams)
```

---

## Quick Start

### 1. Build & Validate a DeepWiki (`git` + `CBM` + `llm-wiki`)

```bash
# PyTorch ExecuTorch (46 pages, 191 Mermaid diagrams):
python3 .agents/skills/deepwiki-generator/scripts/deepwiki_cli.py build \
  --project home-jason-Project-deepwiki-executorch \
  --out-dir llm-wiki-executorch \
  --llm-wiki llm-wiki-executorch \
  --repo executorch \
  --source-url https://github.com/pytorch/executorch/blob/main \
  --regenerate \
  --output llm-wiki-executorch/wiki/site_data.json

python3 .agents/skills/deepwiki-generator/scripts/deepwiki_cli.py validate \
  --wiki-dir llm-wiki-executorch \
  --output /tmp/validate_executorch.json

# Or with local DeepSeek V4 Flash 0731:
python3 .agents/skills/deepwiki-generator/scripts/deepwiki_cli.py build \
  --project <cbm-project-name> \
  --out-dir <wiki-dir> \
  --llm-wiki <wiki-dir> \
  --repo <git-repo-path> \
  --llm-base-url http://127.0.0.1:8000/v1 \
  --llm-model deepseek-v4-flash-0731 \
  --regenerate \
  --output <wiki-dir>/wiki/site_data.json
```

### 2. Inspect 3-Source Repo Dossier & Single-Page Context Packets

```bash
# Export the 3-Source Repository Dossier (git tree + CBM classes + llm-wiki docs):
python3 .agents/skills/deepwiki-generator/scripts/deepwiki_cli.py dossier \
  --wiki-dir llm-wiki-executorch \
  --output /tmp/repo_dossier.md

# Export a compact (< 10 KB) 3-Source Context Packet for a single page:
python3 .agents/skills/deepwiki-generator/scripts/deepwiki_cli.py packet \
  --wiki-dir llm-wiki-executorch \
  --page-id 8.1-core-runtime-architecture \
  --output /tmp/packet_8_1.md
```

### 3. Start the Interactive DeepWiki Web Viewer

```bash
python3 -m wikigen serve llm-wiki --port 8765
python3 -m wikigen serve llm-wiki-executorch --port 8766
```
