# LLM Wiki Schema (DeepWiki Edition)

This repository implements Karpathy's **LLM Wiki** three-layer architecture ([llm-wiki.md](llm-wiki.md)),
specialized for generating and maintaining **DeepWiki-grade codebase & document wikis**.

## Directory Architecture (Three Layers)

```text
llm-wiki/
├── llm-wiki.md          # Original LLM Wiki pattern specification
├── AGENTS.md            # Layer 3 — Schema: conventions, page spec & agent workflows
├── CLAUDE.md            # Layer 3 — Schema pointer for Claude Code
├── raw/                 # Layer 1 — Immutable Raw Sources (never modified by the LLM)
│   └── <project>/       # Repo docs (.md, .dox, PDFs, CMake) + CBM code graph (structure.json)
└── wiki/                # Layer 2 — LLM-owned Persistent Wiki
    ├── index.md         # Content-oriented catalog organized by 2-level hierarchy
    ├── log.md           # Chronological append-only log (## [YYYY-MM-DD] <op> | <detail>)
    ├── outline.json     # 2-level numbered page plan (1, 1.1, 2, 2.1...)
    ├── graph.json       # Unified knowledge & code dependency graph (pages + docs + files)
    └── <slug>.md        # DeepWiki-format Markdown pages
```

## DeepWiki Page Format (`wiki/<slug>.md`)

Every page in `wiki/<slug>.md` MUST include:
1. **YAML Frontmatter**:
   ```yaml
   ---
   id: 1-armnn-overview
   section_id: "1"
   title: ArmNN Overview
   parent: null          # or parent slug e.g. "2-core-architecture"
   order: 10
   type: overview        # overview | architecture | component | backend | tool | guide
   source_url: https://github.com/ARM-software/armnn/blob/main
   sources:
     - README.md
     - include/armnn/INetwork.hpp
   updated: '2026-11-14'
   ---
   ```
2. **Collapsible Relevant Source Files block** right under the `# Title`:
   ```markdown
   <details>
   <summary>Relevant source files</summary>

   The following files were used as context for generating this wiki page:

   - [README.md](README.md)
   - [include/armnn/INetwork.hpp](include/armnn/INetwork.hpp)
   </details>
   ```
3. **Multi-diagram Architecture & Flow Visuals**:
   - Subgraph `mermaid` diagrams (`graph TD`, `flowchart LR`, `sequenceDiagram`, `classDiagram`) using real C++ class/function names from `raw/<project>/structure.json`.
4. **Per-Section Grounded Citations**:
   - Every `##` / `###` section ends with `Sources: [path:start-end](), [path2:start-end]()` citing exact files and line numbers.
5. **Cross-Page Links**:
   - Link between wiki pages using `[Title](#section_id)` (e.g. `[Getting Started](#1.1)`) or `[[slug|Title]]`.

## Operations

1. **Ingest (`ingest-raw` + Agent / `wikigen` Synthesis)**:
   - Extract raw code graph (`codebase-memory-mcp`) and copy repo docs into `raw/<project>/`:
     `python3 -m wikigen extract <repo_path> -o llm-wiki/raw/<project>`
   - Synthesize/update 2-level DeepWiki pages in `wiki/`, update `wiki/index.md` and `wiki/graph.json`, and append `## [YYYY-MM-DD] ingest | ...` to `wiki/log.md`.
2. **Query (`wiki-query`)**:
   - Search `wiki/` + `raw/` via BM25 + wikilink expansion:
     `python3 -m wikigen wiki-query llm-wiki -q "<question>"`
   - File valuable synthesis/answers back into `wiki/` as new pages and log `## [YYYY-MM-DD] query | ...`.
3. **Lint (`wiki-lint`)**:
   - Verify zero broken links and zero orphan pages:
     `python3 -m wikigen wiki-lint llm-wiki`
4. **Serve (`serve`)**:
   - Launch the 3-column DeepWiki web UI on `llm-wiki/`:
     `python3 -m wikigen serve llm-wiki --port 8765`
