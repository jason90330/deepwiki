"""Dynamic Knowledge Linker & DeepWiki Builder (`wikigen link` / `wikigen build`).

Connects an already-indexed `codebase-memory-mcp` project graph with an existing
`llm-wiki` collection (and/or HTTP/Qdrant RAG collection), dynamically discovers
entity + lexical + structural links between code symbols/files and documentation,
and synthesizes a complete DeepWiki (`wiki/*.md`, `outline.json`, `knowledge_links.json`,
`graph.json`, `index.md`, `log.md`).
"""
from __future__ import annotations

import datetime as dt
import json
import re
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

from .cbm import CBMClient, find_binary
from .extract import extract
from .llm import LocalLLMClient
from .pages import (
    _file_to_pages,
    _page_files,
    _symbols_for,
    generate_all,
    mermaid_class_diagram,
    mermaid_nl_to_code_diagram,
    mermaid_page,
    mermaid_sequence_diagram,
    page_deps,
    read_source_snippet,
)
from .plan import dumps, plan_outline, write_repo_dossier
from .render import _frontmatter, write_wiki
from .serve import _strip_frontmatter
from .wiki_rag import WikiRAG


class RAGCollectionAdapter:
    """Unified retrieval & document enumeration interface over llm-wiki and/or HTTP/Qdrant RAG."""

    def __init__(
        self,
        llm_wiki_dir: Path | None = None,
        rag_url: str | None = None,
        rag_collection: str | None = None,
    ) -> None:
        self.llm_wiki_dir = llm_wiki_dir.resolve() if llm_wiki_dir else None
        self.rag_url = rag_url.rstrip("/") if rag_url else None
        self.rag_collection = rag_collection or "default"
        self.wiki_rag = WikiRAG(self.llm_wiki_dir, include_raw=True) if self.llm_wiki_dir else None
        self.docs: list[dict[str, Any]] = list(self.wiki_rag.docs) if self.wiki_rag else []
        if self.rag_url:
            self._load_remote_docs()

    def _load_remote_docs(self) -> None:
        """Optionally pull document metadata from a Qdrant or FastAPI RAG collection."""
        if not self.rag_url:
            return
        # Try Qdrant scroll endpoint first: POST /collections/{name}/points/scroll
        scroll_url = f"{self.rag_url}/collections/{self.rag_collection}/points/scroll"
        req = urllib.request.Request(
            scroll_url,
            data=json.dumps({"limit": 250, "with_payload": True, "with_vector": False}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                points = (data.get("result") or {}).get("points") or []
                for pt in points:
                    payload = pt.get("payload") or {}
                    text = str(payload.get("text") or payload.get("content") or payload.get("page_content") or "")
                    if not text:
                        continue
                    doc_id = str(payload.get("doc_id") or payload.get("id") or pt.get("id"))
                    title = str(payload.get("title") or payload.get("source") or doc_id)
                    path = str(payload.get("source") or payload.get("file_path") or f"rag://{self.rag_collection}/{doc_id}")
                    self.docs.append({
                        "id": f"rag:{doc_id}",
                        "title": title,
                        "path": path,
                        "meta": payload,
                        "headings": [title],
                        "links": [],
                        "text": text,
                    })
        except (urllib.error.URLError, TimeoutError, ValueError):
            pass

    def query(self, text: str, top_k: int = 5) -> list[dict[str, Any]]:
        hits: list[dict[str, Any]] = []
        if self.wiki_rag:
            hits.extend(self.wiki_rag.query(text, top_k=top_k, expand_links=True))
        if self.rag_url:
            # Support ~/Project/rag FastAPI `/api/v1/retrieve` endpoint
            for ep in ("/api/v1/retrieve", "/retrieve", "/query"):
                req = urllib.request.Request(
                    f"{self.rag_url}{ep}",
                    data=json.dumps({"query": text, "collection_name": self.rag_collection, "top_k": top_k}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(req, timeout=6) as resp:
                        body = json.loads(resp.read().decode("utf-8"))
                        items = body.get("results") or body.get("chunks") or body.get("hits") or []
                        for i, it in enumerate(items[:top_k]):
                            doc_id = str(it.get("id") or it.get("chunk_id") or f"chunk-{i}")
                            hits.append({
                                "id": f"rag:{doc_id}",
                                "title": str(it.get("title") or it.get("source") or doc_id),
                                "path": str(it.get("source") or it.get("file_path") or f"rag://{self.rag_collection}/{doc_id}"),
                                "headings": [],
                                "links": [],
                                "score": round(float(it.get("score") or 1.0), 4),
                                "via": f"rag-api:{self.rag_collection}",
                                "snippet": str(it.get("text") or it.get("content") or "")[:1200],
                            })
                        break
                except (urllib.error.URLError, TimeoutError, ValueError):
                    continue
        hits.sort(key=lambda h: -h["score"])
        return hits[:top_k + 2]


def infer_repo_from_project(project: str, fallback_repo: Path | None = None) -> Path:
    """Resolve local repo path from a CBM project slug like `home-jason-Project-deepwiki-armnn`."""
    if fallback_repo and fallback_repo.exists():
        return fallback_repo.resolve()
    parts = project.split("-")
    # Greedily reconstruct existing path segments from left to right
    cur = Path("/")
    i = 0
    while i < len(parts):
        matched = None
        for j in range(len(parts), i, -1):
            cand = cur / "-".join(parts[i:j])
            if cand.exists():
                matched = (cand, j)
                break
        if matched:
            cur, i = matched
        else:
            break
    if cur.is_dir() and cur != Path("/"):
        return cur.resolve()
    return (fallback_repo or Path(".")).resolve()


def discover_knowledge_links(
    structure: dict[str, Any],
    outline: dict[str, Any],
    collection: RAGCollectionAdapter,
) -> dict[str, Any]:
    """Dynamically link code symbols, files, and subsystems with llm-wiki / RAG documents.

    Returns a structured link manifest with:
    - `doc_to_symbols`: doc_id -> list of matched CBM symbols (`qname`, `name`, `label`, `file`, `lines`)
    - `doc_to_files`: doc_id -> list of referenced repo file paths
    - `page_to_docs`: page_id -> ranked list of linked documents (`score`, `via`, `shared_symbols`)
    - `page_to_bridges`: page_id -> top bridge symbols connecting to other subsystems
    """
    symbols = structure.get("symbols") or {}
    files = set((structure.get("files") or {}).keys())

    # Index high-signal symbol names (Classes, Structs, Interfaces, Functions >= 4 chars)
    sym_by_name: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for qn, s in symbols.items():
        name = s.get("name", "")
        if len(name) < 4 or name in ("main", "init", "test", "None", "self", "data", "type", "size", "info", "read", "write"):
            continue
        sym_by_name[name].append((qn, s))

    # Keep unambiguous or high-fan-in symbols per name
    canonical_sym: dict[str, tuple[str, dict[str, Any]]] = {}
    for name, candidates in sym_by_name.items():
        candidates.sort(key=lambda qs: (-(qs[1].get("fan_in", 0) * 2 + qs[1].get("fan_out", 0)), qs[0]))
        if len(candidates) <= 6 or candidates[0][1].get("label") in ("Class", "Struct", "Interface"):
            canonical_sym[name] = candidates[0]

    file_by_basename: dict[str, list[str]] = defaultdict(list)
    for f in files:
        bn = Path(f).name
        if len(bn) >= 5:
            file_by_basename[bn].append(f)

    doc_to_symbols: dict[str, list[dict[str, Any]]] = {}
    doc_to_files: dict[str, list[str]] = {}
    symbol_to_docs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    file_to_docs: dict[str, list[dict[str, Any]]] = defaultdict(list)

    ident_re = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]{3,})\b")
    path_re = re.compile(r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.[A-Za-z0-9]+")

    for doc in collection.docs:
        did = doc["id"]
        text = f"{doc['title']}\n{doc['text']}"
        tokens = set(ident_re.findall(text))
        matched_syms: list[dict[str, Any]] = []
        for tok in tokens:
            if tok in canonical_sym:
                qn, s = canonical_sym[tok]
                entry = {
                    "qname": qn,
                    "name": s["name"],
                    "label": s["label"],
                    "file": s["file"],
                    "start": s["start"],
                    "end": s["end"],
                    "fan_in": s.get("fan_in", 0),
                }
                matched_syms.append(entry)
                symbol_to_docs[ s["name"] ].append({"id": did, "title": doc["title"], "path": doc["path"]})
        matched_syms.sort(key=lambda x: (-x["fan_in"], x["name"]))
        doc_to_symbols[did] = matched_syms[:25]

        matched_files: set[str] = set()
        for pm in path_re.findall(text):
            if pm in files:
                matched_files.add(pm)
            else:
                bn = Path(pm).name
                if bn in file_by_basename and len(file_by_basename[bn]) == 1:
                    matched_files.add(file_by_basename[bn][0])
        for s_entry in matched_syms[:12]:
            matched_files.add(s_entry["file"])
        doc_to_files[did] = sorted(matched_files)
        for mf in matched_files:
            file_to_docs[mf].append({"id": did, "title": doc["title"], "path": doc["path"]})

    # Map every outline page to its linked docs (combining BM25/RAG query + entity overlap)
    page_to_docs: dict[str, list[dict[str, Any]]] = {}
    page_to_bridges: dict[str, list[dict[str, Any]]] = {}
    valid_page_ids = {p["id"] for p in outline.get("pages", [])} | {"index"}

    for page in outline.get("pages", []):
        pid = page["id"]
        pfiles = _page_files(page)
        psyms = _symbols_for(pfiles, structure)
        psym_names = {s["name"] for _, s in psyms[:40]}

        # Bridge symbols: highest fan-in + fan-out symbols on this page
        bridges = [
            {
                "name": s["name"],
                "label": s["label"],
                "file": s["file"],
                "start": s["start"],
                "end": s["end"],
                "fan_in": s["fan_in"],
                "fan_out": s["fan_out"],
            }
            for _, s in psyms[:8]
        ]
        page_to_bridges[pid] = bridges

        q_terms = f"{page['title']} {page.get('summary', '')} " + " ".join(s["name"] for _, s in psyms[:12])
        rag_hits = collection.query(q_terms, top_k=6)

        combined: dict[str, dict[str, Any]] = {}
        for h in rag_hits:
            if h["id"] == pid:
                continue
            if not h["path"].startswith("raw/") and not h["id"].startswith("rag:") and h["id"] not in valid_page_ids:
                continue
            shared = sorted(psym_names.intersection({m["name"] for m in doc_to_symbols.get(h["id"], [])}))
            combined[h["id"]] = {
                "id": h["id"],
                "title": h["title"],
                "path": h["path"],
                "score": round(h["score"] + len(shared) * 1.5, 3),
                "via": h["via"] + (f"+entity({len(shared)})" if shared else ""),
                "shared_symbols": shared[:8],
                "snippet": h.get("snippet", "")[:360],
            }

        # Also add docs that directly reference files on this page even if missed by top_k lexical query
        doc_text_by_id = {d["id"]: d.get("text", "") for d in collection.docs}
        for pf in pfiles:
            for dref in file_to_docs.get(pf, []):
                did = dref["id"]
                if did == pid or did in combined:
                    continue
                if not dref["path"].startswith("raw/") and not did.startswith("rag:") and did not in valid_page_ids:
                    continue
                shared = sorted(psym_names.intersection({m["name"] for m in doc_to_symbols.get(did, [])}))
                if shared:
                    combined[did] = {
                        "id": did,
                        "title": dref["title"],
                        "path": dref["path"],
                        "score": round(len(shared) * 2.0, 3),
                        "via": f"entity-link({len(shared)} symbols)",
                        "shared_symbols": shared[:8],
                        "snippet": doc_text_by_id.get(did, "")[:360],
                    }

        ranked_docs = sorted(combined.values(), key=lambda x: -x["score"])[:6]
        page_to_docs[pid] = ranked_docs

    return {
        "project": structure.get("project"),
        "commit": structure.get("commit"),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "stats": {
            "total_code_symbols": len(symbols),
            "total_code_files": len(files),
            "total_collection_docs": len(collection.docs),
            "docs_with_symbol_links": sum(1 for v in doc_to_symbols.values() if v),
            "total_symbol_mentions": sum(len(v) for v in doc_to_symbols.values()),
            "pages_linked": len(page_to_docs),
        },
        "doc_to_symbols": doc_to_symbols,
        "doc_to_files": doc_to_files,
        "page_to_docs": page_to_docs,
        "page_to_bridges": page_to_bridges,
    }


def build_enriched_graph(
    outline: dict[str, Any],
    structure: dict[str, Any],
    links: dict[str, Any],
) -> dict[str, Any]:
    """Build interactive graph.json with page, doc, file, and bridge-symbol nodes + dynamic link edges."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()

    def add_node(nid: str, **attrs: Any) -> None:
        if nid not in seen_nodes:
            seen_nodes.add(nid)
            nodes.append({"id": nid, **attrs})

    for p in outline.get("pages", []):
        pid = p["id"]
        pnode = f"page:{pid}"
        add_node(
            pnode,
            type="page",
            label=p["title"],
            parent=f"page:{p['parent']}" if p.get("parent") else None,
            size=max(1, len(p.get("files", []))),
        )
        if p.get("parent"):
            edges.append({"source": f"page:{p['parent']}", "target": pnode, "type": "child"})
        for r in p.get("related", []):
            if pid < r:
                edges.append({"source": pnode, "target": f"page:{r}", "type": "related"})
        for f in p.get("files", []):
            edges.append({"source": pnode, "target": f"file:{f}", "type": "covers"})

        # Dynamic document links
        for d in links.get("page_to_docs", {}).get(pid, []):
            dnode = f"doc:{d['id']}"
            add_node(dnode, type="doc", label=d["title"], path=d["path"], size=2)
            edges.append({
                "source": dnode,
                "target": pnode,
                "type": "documents",
                "weight": d["score"],
                "via": d["via"],
                "shared_symbols": d.get("shared_symbols", []),
            })

        # Top bridge symbols per page
        for b in links.get("page_to_bridges", {}).get(pid, [])[:4]:
            snode = f"sym:{b['file']}:{b['name']}"
            add_node(snode, type="symbol", label=f"{b['name']} ({b['label']})", file=b["file"], size=2)
            edges.append({"source": pnode, "target": snode, "type": "defines_bridge"})
            edges.append({"source": snode, "target": f"file:{b['file']}", "type": "located_in"})

    for f, meta in (structure.get("files") or {}).items():
        if meta.get("symbols"):
            add_node(
                f"file:{f}",
                type="file",
                label=f,
                community=meta.get("community"),
                is_test=meta.get("is_test", False),
                size=len(meta["symbols"]),
            )
    for a, b, w in structure.get("file_edges") or []:
        edges.append({"source": f"file:{a}", "target": f"file:{b}", "type": "depends", "weight": w})

    return {
        "project": structure.get("project"),
        "commit": structure.get("commit"),
        "link_stats": links.get("stats", {}),
        "nodes": nodes,
        "edges": edges,
    }


def format_knowledge_links_section(
    page: dict[str, Any],
    outline: dict[str, Any],
    structure: dict[str, Any],
    links: dict[str, Any],
) -> str:
    """Render a deterministic `## Knowledge Graph & RAG Links` section for a page."""
    pid = page["id"]
    titles = {p["id"]: p["title"] for p in outline.get("pages", [])}
    linked_docs = links.get("page_to_docs", {}).get(pid, [])
    bridges = links.get("page_to_bridges", {}).get(pid, [])
    deps = page_deps(page, structure, _file_to_pages(outline))

    lines = ["## Dynamic Knowledge Links (Code Graph ↔ LLM-Wiki / RAG)", ""]
    if linked_docs:
        lines.append("### Linked Architecture & Design Documents")
        lines.append("")
        lines.append("| Document | Match Channel | Score | Shared Code Symbols |")
        lines.append("|---|---|---|---|")
        for d in linked_docs:
            syms = ", ".join(f"`{s}`" for s in d.get("shared_symbols", [])[:5]) or "*(lexical/graph match)*"
            doc_link = f"[[{d['id']}|{d['title']}]]" if not d["path"].startswith("raw/") and not d["id"].startswith("rag:") else f"`{d['path']}` ({d['title']})"
            lines.append(f"| {doc_link} | `{d['via']}` | `{d['score']}` | {syms} |")
        lines.append("")

    if bridges:
        lines.append("### High-Centrality Bridge Symbols (CBM Graph)")
        lines.append("")
        lines.append("| Symbol | Kind | Source Location | Fan-In / Fan-Out |")
        lines.append("|---|---|---|---|")
        for b in bridges[:6]:
            lines.append(
                f"| `{b['name']}` | {b['label']} | [{b['file']}:{b['start']}-{b['end']}]() | "
                f"in: `{b['fan_in']}` / out: `{b['fan_out']}` |"
            )
        lines.append("")
        lines.append("Sources: " + ", ".join(f"[{b['file']}:{b['start']}-{b['end']}]()" for b in bridges[:4]))
        lines.append("")

    if deps:
        lines.append("### Cross-Subsystem Coupling")
        lines.append("")
        for other_id, w in deps.most_common(6):
            lines.append(f"- [[{other_id}|{titles.get(other_id, other_id)}]] — call/import coupling weight `{w:.1f}`")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def enrich_existing_wiki_pages(
    wiki_root: Path,
    outline: dict[str, Any],
    structure: dict[str, Any],
    links: dict[str, Any],
    source_url: str | None = None,
) -> list[Path]:
    """Inject or update Dynamic Knowledge Links into an existing `llm-wiki/wiki/` collection."""
    wiki_dir = wiki_root / "wiki" if (wiki_root / "wiki").is_dir() else wiki_root
    updated: list[Path] = []
    marker_re = re.compile(
        r"\n## Dynamic Knowledge Links \(Code Graph ↔ LLM-Wiki / RAG\).*?(?=\n## |\Z)",
        flags=re.S,
    )

    for page in outline.get("pages", []):
        pid = page["id"]
        md_file = wiki_dir / f"{pid}.md"
        if not md_file.exists():
            continue
        raw = md_file.read_text(encoding="utf-8", errors="replace")
        meta, body = _strip_frontmatter(raw)
        meta["commit"] = structure.get("commit", meta.get("commit", ""))
        if source_url:
            meta["source_url"] = source_url
        meta["linked_docs"] = [d["id"] for d in links.get("page_to_docs", {}).get(pid, [])]
        meta["bridge_symbols"] = [b["name"] for b in links.get("page_to_bridges", {}).get(pid, [])[:6]]

        section_md = "\n" + format_knowledge_links_section(page, outline, structure, links)
        if marker_re.search(body):
            body = marker_re.sub("\n" + section_md.strip() + "\n", body)
        else:
            body = body.rstrip() + "\n\n" + section_md

        md_file.write_text(_frontmatter(meta) + "\n" + body.lstrip(), encoding="utf-8")
        updated.append(md_file)
    return updated


def run_dynamic_pipeline(
    project: str,
    out_dir: Path,
    repo: Path | None = None,
    llm_wiki_dir: Path | None = None,
    rag_url: str | None = None,
    rag_collection: str | None = None,
    source_url: str | None = None,
    cbm_bin: str | None = None,
    refresh_structure: bool = False,
    regenerate: bool = False,
    enrich_only: bool = False,
    workers: int = 4,
    llm_base_url: str | None = None,
    llm_model: str | None = None,
) -> dict[str, Any]:
    """End-to-end dynamic pipeline (`git` + `CBM` + `llm-wiki`):
    1. Load or extract `structure.json` from an already-indexed `codebase-memory-mcp` project.
    2. Load the `llm-wiki` and/or HTTP/Qdrant `rag` collection.
    3. Load an existing `outline.json` (if present in `out_dir`) or plan a Canonical DeepWiki outline.
    4. Compute 3-way dynamic knowledge links (`wiki/knowledge_links.json`).
    5. Generate or enrich DeepWiki pages (`wiki/*.md`), `index.md`, `log.md`, and `wiki/graph.json`.
    """
    out_dir = out_dir.resolve()
    wiki_dir = out_dir / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Resolve structure.json from CBM index
    struct_candidates = [
        out_dir / "structure.json",
        out_dir / "raw" / project / "structure.json",
    ]
    if (out_dir / "raw").is_dir():
        struct_candidates.extend(sorted((out_dir / "raw").glob("*/structure.json")))
    struct_path = next((p for p in struct_candidates if p.exists()), out_dir / "raw" / project / "structure.json")

    if refresh_structure or not struct_path.exists():
        resolved_repo = infer_repo_from_project(project, repo)
        client = CBMClient(find_binary(cbm_bin), project=project)
        structure = extract(client, resolved_repo)
        struct_path.parent.mkdir(parents=True, exist_ok=True)
        struct_path.write_text(dumps(structure), encoding="utf-8")
    else:
        structure = json.loads(struct_path.read_text(encoding="utf-8"))

    resolved_repo = Path(structure.get("repo_root") or infer_repo_from_project(project, repo))
    structure["repo_root"] = str(resolved_repo)

    # Step 2: Initialize Knowledge Collection (llm-wiki and/or RAG)
    effective_wiki = llm_wiki_dir.resolve() if llm_wiki_dir else (out_dir if (out_dir / "wiki").is_dir() else None)
    collection = RAGCollectionAdapter(
        llm_wiki_dir=effective_wiki,
        rag_url=rag_url,
        rag_collection=rag_collection,
    )

    # Step 3: Load or Plan Canonical DeepWiki Outline
    outline_path = (wiki_dir / "outline.json") if (wiki_dir / "outline.json").exists() else (out_dir / "outline.json")
    if outline_path.exists() and not refresh_structure and not regenerate:
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
    else:
        outline_path = wiki_dir / "outline.json"
        outline = plan_outline(structure, repo_root=resolved_repo)
        outline_path.write_text(dumps(outline), encoding="utf-8")

    if regenerate:
        for old_md in wiki_dir.glob("*.md"):
            if old_md.stem not in ("log",):
                old_md.unlink()

    # Step 4: Dynamic Knowledge Linking (Code Graph <-> Wiki/RAG)
    links = discover_knowledge_links(structure, outline, collection)
    links_path = wiki_dir / "knowledge_links.json"
    links_path.write_text(dumps(links), encoding="utf-8")

    # Step 5: Generate new pages OR enrich existing curated DeepWiki pages in-place
    llm_client = LocalLLMClient(base_url=llm_base_url, model=llm_model)
    existing_md_count = sum(1 for p in outline.get("pages", []) if (wiki_dir / f"{p['id']}.md").exists())
    if not regenerate and (enrich_only or existing_md_count >= len(outline.get("pages", [])) > 0):
        written = enrich_existing_wiki_pages(out_dir, outline, structure, links, source_url=source_url)
        mode = "enriched-existing-wiki"
    else:
        generated = generate_all(
            outline,
            structure,
            workers=workers,
            doc_rag=collection.wiki_rag,
            llm_client=llm_client if llm_client.enabled else None,
        )
        written = write_wiki(out_dir, outline, structure, generated, source_url=source_url)
        enrich_existing_wiki_pages(out_dir, outline, structure, links, source_url=source_url)
        mode = "generated-and-linked" + (f" ({llm_client.model})" if llm_client.enabled else "")

    # Step 6: Write 3-source repo dossier, per-page context packets & enriched graph.json
    dossier_path = write_repo_dossier(out_dir, structure, outline, links, repo_root=resolved_repo)
    packets_dir = write_page_packets(out_dir, outline, structure, links, repo_root=resolved_repo)
    graph = build_enriched_graph(outline, structure, links)
    graph_path = wiki_dir / "graph.json"
    graph_path.write_text(json.dumps(graph, ensure_ascii=False, indent=1), encoding="utf-8")

    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    stats = links["stats"]
    with (wiki_dir / "log.md").open("a", encoding="utf-8") as log:
        log.write(
            f"## [{stamp}] link ({mode}) | project=`{project}` | "
            f"{stats['pages_linked']} pages, {stats['docs_with_symbol_links']}/{stats['total_collection_docs']} docs linked, "
            f"{stats['total_symbol_mentions']} symbol mentions -> `knowledge_links.json` & `graph.json`\n\n"
        )

    return {
        "status": "ok",
        "mode": mode,
        "project": project,
        "repo_root": str(resolved_repo),
        "out_dir": str(out_dir),
        "pages_updated": len(written),
        "graph_nodes": len(graph["nodes"]),
        "graph_edges": len(graph["edges"]),
        "link_stats": stats,
        "artifacts": {
            "structure": str(struct_path),
            "outline": str(outline_path),
            "knowledge_links": str(links_path),
            "graph": str(graph_path),
            "dossier": str(dossier_path),
            "packets_dir": str(packets_dir),
        },
    }


def write_page_packets(
    out_dir: Path,
    outline: dict[str, Any],
    structure: dict[str, Any],
    links: dict[str, Any],
    repo_root: Path | None = None,
) -> Path:
    """Write 3-Source (`git` + `CBM` + `llm-wiki`) per-page context packets to `wiki/.packets/<page-id>.md`.

    Gives `deepseek v4 flash 0731` (or any agent) grounded source code excerpts from `git`,
    `CBM` symbol/call/inheritance subgraphs, and `llm-wiki` documentation sections in one file.
    """
    wiki_dir = out_dir / "wiki" if (out_dir / "wiki").is_dir() else out_dir
    packets_dir = wiki_dir / ".packets"
    packets_dir.mkdir(parents=True, exist_ok=True)
    valid_pids = {p["id"] for p in outline.get("pages", [])} | {"_repo_dossier"}
    for old_pkt in packets_dir.glob("*.md"):
        if old_pkt.stem not in valid_pids:
            old_pkt.unlink()
    titles = {p["id"]: p["title"] for p in outline.get("pages", [])}
    effective_repo = repo_root or (Path(structure["repo_root"]) if structure.get("repo_root") else None)

    for page in outline.get("pages", []):
        pid = page["id"]
        files = _page_files(page)
        syms = _symbols_for(files, structure)[:22]
        linked_docs = links.get("page_to_docs", {}).get(pid, [])
        children = [p for p in outline.get("pages", []) if p.get("parent") == pid]

        lines = [
            f"# 3-Source Context Packet (`git` + `CBM` + `llm-wiki`) for `{pid}` — {page['title']}",
            "",
            f"- **Target Wiki File**: `wiki/{pid}.md`",
            f"- **Archetype**: `{'Parent Hub Page' if children else ('Glossary Page' if pid.endswith('-glossary') else 'Leaf Technical Spec Page')}`",
            f"- **Parent Page**: `{page.get('parent') or 'None (Top-Level Chapter)'}`",
            f"- **Summary**: {page.get('summary', '')}",
            f"- **Valid `[[wikilink]]` Neighbours**: "
            + (", ".join(f"`[[{r}|{titles.get(r, r)}]]`" for r in page.get("related", [])) or "none"),
            "",
            "## 1. Relevant Source Files (`git` + `CBM`, use verbatim in `<details>`)",
            *[f"- `[{f}]({f})`" for f in files[:30]],
            "",
            "## 2. Grounded Code Symbols (`CBM`, use verbatim for `[file:start-end]()` pill citations)",
        ]
        for _q, s in syms:
            doc = re.sub(r"\s+", " ", s.get("doc") or "").strip()[:160]
            lines.append(
                f"- `{s['name']}` ({s['label']}) @ `[{s['file']}:{s['start']}-{s['end']}]()` "
                f"[fan-in={s['fan_in']}, fan-out={s['fan_out']}] — {doc or s.get('signature', '')[:110]}"
            )

        # Include real source code excerpts from `git` working tree!
        if effective_repo and syms:
            lines += ["", "## 3. Grounded Source Code Excerpts (`git` Working Tree)"]
            added_excerpts = 0
            for _q, s in syms[:8]:
                code_str, l_start, l_end, lang = read_source_snippet(
                    effective_repo, s["file"], s["start"], s["end"], max_lines=16
                )
                if code_str and len(code_str.splitlines()) >= 3:
                    lines += [
                        f"### `{s['name']}` in `[{s['file']}:{l_start}-{l_end}]()`",
                        f"```{lang}",
                        code_str,
                        "```",
                        "",
                    ]
                    added_excerpts += 1
                    if added_excerpts >= 5:
                        break

        lines += ["", "## 4. Linked Official Docs (`llm-wiki` / `RAG`)"]
        for d in linked_docs:
            clean_snip = re.sub(r"\s+", " ", d.get("snippet", ""))[:360]
            lines.append(
                f"- **{d['title']}** (`{d['path']}`, score={d['score']}, shared_symbols={d.get('shared_symbols', [])}): "
                f"{clean_snip}"
            )
        if not linked_docs:
            lines.append("- *(none)*")

        lines += [
            "",
            "## 5. Pre-Verified DeepWiki v1.9.9.5 Mermaid Diagrams",
        ]
        nl_diag = mermaid_nl_to_code_diagram(files, structure, max_items=6)
        if nl_diag:
            lines += ["### Natural Language Space <-> Code Entity Space", nl_diag, ""]
        lines += ["### Subsystem Architecture Flowchart", mermaid_page(page, outline, structure), ""]
        cdiag = mermaid_class_diagram(files, structure)
        if cdiag:
            lines += ["### Class Hierarchy Diagram", cdiag, ""]
        sdiag = mermaid_sequence_diagram(files, structure)
        if sdiag:
            lines += ["### Call Sequence Diagram", sdiag, ""]

        lines += [
            "## 6. DeepWiki v1.9.9.5 Authoring Checklist for `wiki/" + pid + ".md`",
            "1. Keep YAML frontmatter at top (`id`, `title`, `parent`, `sources`, `linked_docs`, `bridge_symbols`).",
            "2. Keep `<details><summary>Relevant source files</summary>` block immediately after `# Title`.",
            "3. Start with `## Purpose and Scope`, then numbered `## 1. ...`, `## 2. ...` sections separated by `---`.",
            "4. Include at least 2 ```mermaid``` diagrams (including a `Natural Language Space` <-> `Code Entity Space` mapping).",
            "5. Cite code entities inline using `[path/to/file.ext:start-end]()` and end every `##` section with `Sources: [file:start-end]()`.",
            "6. Run `deepwiki_cli.py build --enrich-only ...` and `deepwiki_cli.py validate ...` after editing.",
        ]
        (packets_dir / f"{pid}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return packets_dir


def validate_deepwiki(wiki_root: Path) -> dict[str, Any]:
    """Validate all generated DeepWiki pages against strict structural & link-health gates."""
    wiki_root = wiki_root.resolve()
    wiki_dir = wiki_root / "wiki" if (wiki_root / "wiki").is_dir() else wiki_root
    outline_path = wiki_dir / "outline.json"
    if not outline_path.exists():
        return {"passed": False, "error": f"Missing {outline_path}"}

    outline = json.loads(outline_path.read_text(encoding="utf-8"))
    rag = WikiRAG(wiki_root, include_raw=True)
    lint_res = rag.lint()

    page_issues: list[dict[str, Any]] = []
    checked = 0
    total_mermaid = 0
    total_citations = 0

    for p in outline.get("pages", []):
        pid = p["id"]
        md_path = wiki_dir / f"{pid}.md"
        if not md_path.exists():
            page_issues.append({"page": pid, "issue": f"Missing file wiki/{pid}.md"})
            continue
        checked += 1
        raw = md_path.read_text(encoding="utf-8", errors="replace")
        meta, body = _strip_frontmatter(raw)
        issues: list[str] = []
        if not meta.get("id") or not meta.get("title"):
            issues.append("Missing YAML frontmatter `id` or `title`.")
        if "<details>" not in body or "Relevant source files" not in body:
            issues.append("Missing `<details><summary>Relevant source files</summary>` block.")
        mermaids = re.findall(r"```mermaid\s*\n(.*?)```", body, flags=re.S)
        total_mermaid += len(mermaids)
        min_req = 1 if pid in ("overview", "1-overview") else 2
        if len(mermaids) < min_req:
            issues.append(f"Has {len(mermaids)} Mermaid diagrams; expected >= {min_req}.")
        citations = re.findall(r"^Sources:\s*.+$", body, flags=re.M)
        total_citations += len(citations)
        if not citations:
            issues.append("Missing `Sources: [file:start-end]()` citation lines.")
        if "## Dynamic Knowledge Links" not in body:
            issues.append("Missing `## Dynamic Knowledge Links` section (run `build --enrich-only`).")
        if issues:
            page_issues.append({"page": pid, "issues": issues})

    passed = (
        len(page_issues) == 0
        and len(lint_res["broken_links"]) == 0
        and len(lint_res["orphans"]) == 0
        and checked == len(outline.get("pages", []))
    )
    return {
        "passed": passed,
        "pages_checked": checked,
        "total_mermaid_diagrams": total_mermaid,
        "total_source_citation_lines": total_citations,
        "broken_links": lint_res["broken_links"],
        "orphans": lint_res["orphans"],
        "page_issues": page_issues,
    }
