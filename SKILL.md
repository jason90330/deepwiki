---
name: deepwiki-generator
description: >-
  Generate DeepWiki-grade (v1.9.9.5) multi-page documentation, architecture diagrams,
  and interactive knowledge graphs by dynamically linking a git repository, an already-indexed
  codebase-memory-mcp (CBM) code graph, and an existing llm-wiki collection or HTTP/Qdrant RAG
  collection. Optimized for local LLMs such as DeepSeek V4 Flash 0731 as well as deterministic
  zero-API execution.
---

# DeepWiki Generator & 3-Source Knowledge Linker (`git` + `CBM` + `llm-wiki`)

## Overview

`deepwiki-generator` reproduces the architecture of **DeepWiki v1.9.9.5** (reverse-engineered via `rea` from `https://deepwiki.com/pytorch/executorch` and `https://deepwiki.com/ARM-software/armnn`) by dynamically fusing **three complementary knowledge sources**:

1. **`git` Repository Working Tree**: Directory hierarchy, build files (`CMakeLists.txt`, `targets.bzl`, `BUCK`, `pyproject.toml`, `.fbs`), commit history, and exact source code slices (`read_source_snippet` at `file:start-end`).
2. **`codebase-memory-mcp` (CBM) Code Graph**: Indexed `Class`, `Struct`, `Interface`, `Function`, and `Method` symbols with exact line spans (`start_line`–`end_line`), `INHERITS` hierarchies, `CALLS`/`IMPORTS` edges, fan-in/fan-out centrality, and Louvain communities.
3. **`llm-wiki` Collection (or HTTP/Qdrant RAG)**: Karpathy's 3-layer knowledge base (`raw/` immutable official docs + `wiki/` synthesized pages + `AGENTS.md` schema) retrieved via BM25 + 1-hop `[[wikilink]]` graph expansion.

It supports **two execution modes**:
- **Deterministic + Agentic Packet Mode (Default)**: Generates a complete, lint-clean DeepWiki deterministically, and exports a compact Repo Dossier (`wiki/.packets/_repo_dossier.md`) plus per-page 3-Source Context Packets (`wiki/.packets/<page-id>.md`, `< 10 KB` each) so an agent (such as **`deepseek-v4-flash-0731`**) can author or refine pages without ever overflowing its context window.
- **Direct Local LLM Mode (`--llm-base-url` / `--llm-model`)**: Connects directly to a local OpenAI-compatible endpoint (e.g., `deepseek-v4-flash-0731` via vLLM / SGLang / Ollama / llama.cpp) using DeepWiki v1.9.9.5's reverse-engineered `OUTLINE_SYSTEM_PROMPT` and `PAGE_SYSTEM_PROMPT`.

---

## Reverse-Engineered DeepWiki v1.9.9.5 Architecture (`rea` Spec)

Every generated DeepWiki adheres to the 5 structural invariants of `deepwiki.com` (v1.9.9.5):

1. **Canonical Lifecycle Outline Taxonomy (`wiki/outline.json`)**:
   - Always begins with **`1. Overview`** (`1.1 Getting Started`, `1.2 High-Level / Export API`) and **`2. Build System and Infrastructure`**, followed by core compiler/IR/graph subsystems, quantization/optimization, pluggable hardware backends (with an `Other Backends` consolidation page so no chapter exceeds 8 children), model/application verticals, **`Testing and CI/CD Infrastructure`**, **`Runtime Execution`**, **`Platform Extensions`**, and concludes with **`Glossary`**.
2. **Four Distinct Page Archetypes**:
   - **Archetype A — `1-overview`**: Repository statistics, full-system component map (`flowchart TD`), `Natural Language Space ↔ Code Entity Space` bridge diagram, core class hierarchy (`classDiagram`), subsystem navigation matrix, and entry points.
   - **Archetype B — Parent Hub Pages (`2`, `3`, `5`, `8`...)**: `## Purpose and Scope` followed by one numbered section and dedicated Mermaid architecture diagram per child subsystem page (`For detailed technical specifications, see [[child-id|Child Title]]`).
   - **Archetype C — Leaf Technical Spec Pages (`1.1`, `3.1`, `8.1`...)**: `## Purpose and Scope`, numbered `## 1..5` sections separated by horizontal rules (`---`), **4 Mermaid diagrams** (`Natural Language Space ↔ Code Entity Space` `graph LR`, subsystem `flowchart TD`, `classDiagram` with real methods & inheritance, and `sequenceDiagram` from real `CALLS` edges), grounded `git` source code blocks, API signature tables, and `## Dynamic Knowledge Links`.
   - **Archetype D — `Glossary` (`10-glossary` / `*-glossary`)**: Domain vocabulary, abbreviations, and binary formats mapped directly to `Code Entity Space` classes/structs with `graph LR` mapping diagrams.
3. **Inline Split GitHub Citation Pills (`[path/to/file.ext:start-end]()`)**:
   - Every technical claim in prose, tables, and section `Sources:` footers uses `[file:start-end]()` citations, which the Web UI renders as DeepWiki's iconic split GitHub pill badge (`path/to/file.ext | start-end`) linking to `#Lstart-Lend`.

---

## ⚠️ Critical Rules for `deepseek-v4-flash-0731` & Other LLM Agents

1. **NEVER read `structure.json`, `graph.json`, or `knowledge_links.json` directly into your context window.**
   - On large repositories (e.g., `pytorch/executorch` with 521k nodes or `ARM-software/armnn` with 23k nodes), `structure.json` is **15–45 MB**. Reading it directly will overflow your context window.
   - Instead, ALWAYS read the compact **Repo Dossier** (`wiki/.packets/_repo_dossier.md`) or **Single-Page Context Packet** (`wiki/.packets/<page-id>.md`) via `deepwiki_cli.py dossier` and `deepwiki_cli.py packet`.
2. **ALWAYS run `build` first, and ALWAYS run `validate` before finishing.**
   - Do NOT finish until `validate` outputs `"passed": true`.
3. **Ground every claim in `git` + `CBM` + `llm-wiki` facts from the Page Packet.**
   - Never invent file paths, line numbers, class names, or `[[wikilinks]]`. Use the pre-verified `[file:start-end]()` ranges, `git` code snippets, and Mermaid diagrams in `wiki/.packets/<page-id>.md`.

---

## Standard 4-Step Workflow for Any Repository / Knowledge Collection

### Step 1: Verify or Prepare the `llm-wiki` 3-Layer Directory
Ensure `<wiki-dir>` contains:
- `<wiki-dir>/raw/<project>/`: Official markdown/rst/doxygen documentation (`README.md`, `docs/**/*.md`, `*.rst`, `*.dox`).
- `<wiki-dir>/wiki/`: Output directory for synthesized DeepWiki pages.
- `<wiki-dir>/AGENTS.md`: Layer 3 schema file (copied from `llm-wiki/AGENTS.md` if creating a new workspace).

### Step 2: Run `build` (3-Source Extraction, Dynamic Linking & Page Synthesis)

```bash
# Mode A: Deterministic 3-Source Build (Zero External API Required)
python3 /home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py build \
  --project <cbm-project-name> \
  --out-dir <path-to-wiki-dir> \
  --llm-wiki <path-to-wiki-dir> \
  --repo <path-to-git-repo> \
  --source-url <github-or-gitlab-blob-base-url> \
  --regenerate \
  --output <path-to-wiki-dir>/wiki/site_data.json

# Mode B: With Local DeepSeek V4 Flash 0731 (OpenAI-Compatible Endpoint)
python3 /home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py build \
  --project <cbm-project-name> \
  --out-dir <path-to-wiki-dir> \
  --llm-wiki <path-to-wiki-dir> \
  --repo <path-to-git-repo> \
  --source-url <github-or-gitlab-blob-base-url> \
  --llm-base-url http://127.0.0.1:8000/v1 \
  --llm-model deepseek-v4-flash-0731 \
  --regenerate \
  --output <path-to-wiki-dir>/wiki/site_data.json
```

What `build` does automatically:
1. Extracts `structure.json` from `codebase-memory-mcp` (`LIMIT 95000` + non-null file filters so 500k+ node repos succeed).
2. Builds the **Repo Dossier** (`wiki/.packets/_repo_dossier.md`) and plans the **Canonical DeepWiki v1.9.9.5 Outline** (`wiki/outline.json`) using `git` directory/build structure + `CBM` symbol centrality + `llm-wiki` doc mentions.
3. Performs **3-Way Dynamic Knowledge Linking** (`wiki/knowledge_links.json`):
   - **Entity Linking**: Matches code symbols and file paths in `raw/` or RAG docs to CBM definitions.
   - **BM25 + 1-Hop `[[wikilink]]` Retrieval**: Links top architectural docs to each subsystem page.
   - **Bridge Symbol Discovery**: Identifies high fan-in/fan-out symbols and cross-page call/import coupling weights.
4. Synthesizes all 4 DeepWiki Page Archetypes (`wiki/*.md`) with 3–4 Mermaid diagrams per page, real `git` source code excerpts, and inline `[file:start-end]()` citations.
5. Exports per-page 3-Source Context Packets (`wiki/.packets/<page-id>.md`) and writes `wiki/graph.json`.

### Step 3: (Optional) Inspect `dossier` / `packet` & Refine Specific Pages
If you (`deepseek-v4-flash-0731` or another agent) want to inspect the repository dossier or write bespoke prose for specific pages:

```bash
# 1. Inspect the 3-Source Repo Dossier (git + CBM + llm-wiki summary):
python3 /home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py dossier \
  --wiki-dir <path-to-wiki-dir> \
  --output /tmp/repo_dossier.md

# 2. Export a single page's 3-Source Context Packet (< 10 KB, includes git code slices + CBM symbols + llm-wiki docs):
python3 /home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py packet \
  --wiki-dir <path-to-wiki-dir> \
  --page-id <page-id> \
  --output /tmp/page_packet.md

# 3. After editing <wiki-dir>/wiki/<page-id>.md, re-attach dynamic links & rebuild graph.json:
python3 /home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py build \
  --project <cbm-project-name> \
  --out-dir <path-to-wiki-dir> \
  --llm-wiki <path-to-wiki-dir> \
  --repo <path-to-git-repo> \
  --enrich-only \
  --output /tmp/enrich_summary.json
```

### Step 4: Run `validate` (Mandatory Quality Gate)
Always validate the generated DeepWiki before reporting completion:

```bash
python3 /home/jason/Project/deepwiki/.agents/skills/deepwiki-generator/scripts/deepwiki_cli.py validate \
  --wiki-dir <path-to-wiki-dir> \
  --output /tmp/deepwiki_validate.json
cat /tmp/deepwiki_validate.json
```

`validate` verifies:
- Every page in `outline.json` exists and has valid YAML frontmatter (`id`, `title`).
- Every page has `<details><summary>Relevant source files</summary>`.
- Every subsystem page has `>= 2` ```mermaid``` blocks (`>= 1` for overview).
- Every page has `Sources: [...]()` citation lines and `## Dynamic Knowledge Links`.
- `broken_links == []` and `orphans == []`.

---

## CLI Subcommands Reference (`deepwiki_cli.py`)

| Subcommand | Purpose | Example |
|---|---|---|
| `build` | Extract CBM graph, link `git` + `CBM` + `llm-wiki`/`RAG`, and synthesize all pages | `deepwiki_cli.py build --project ... --out-dir ... --repo ... --output ...` |
| `dossier` | Export the 3-Source Repository Dossier (`git` tree + `CBM` classes + `llm-wiki` docs) | `deepwiki_cli.py dossier --wiki-dir llm-wiki-executorch --output /tmp/dossier.md` |
| `packet` | Export a single page's 3-Source Context Packet (`git` code snippets + `CBM` symbols + `llm-wiki` docs + Mermaid diagrams) | `deepwiki_cli.py packet --wiki-dir llm-wiki-executorch --page-id 8.1-core-runtime-architecture --output /tmp/p.md` |
| `validate` | Run all structural, Mermaid, citation, and link-health quality gates | `deepwiki_cli.py validate --wiki-dir llm-wiki-executorch --output /tmp/val.json` |
| `query` | Query the `llm-wiki` collection via BM25 + 1-hop `[[wikilink]]` expansion | `deepwiki_cli.py query --wiki-dir llm-wiki-executorch --query "Program Method EValue" --output /tmp/q.json` |
| `lint` | Check `broken_links` and `orphans` across `wiki/*.md` | `deepwiki_cli.py lint --wiki-dir llm-wiki-executorch --output /tmp/lint.json` |
| `serve` | Launch the interactive 3-column DeepWiki Web UI | `deepwiki_cli.py serve --wiki-dir llm-wiki-executorch --port 8766` |
