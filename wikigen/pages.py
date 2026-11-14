"""Step 2b — deterministic DeepWiki page & Mermaid diagram synthesis.

For every page in `outline.json`, assembles grounded structure from the code graph
(`symbols`, signatures, docstrings, call/import edges, cross-page dependencies) plus
linked `llm-wiki` / RAG documents, and generates DeepWiki-formatted Markdown with
`<details><summary>Relevant source files</summary>`, Mermaid diagrams (`flowchart`,
`classDiagram`), and `Sources: [file:start-end]()` citations.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import PurePosixPath
from typing import Any

from .wiki_rag import WikiRAG

MERMAID_MAX_NODES = 24


def _page_files(page: dict[str, Any]) -> list[str]:
    return list(dict.fromkeys(page.get("files") or []))


def _file_to_pages(outline: dict[str, Any]) -> dict[str, list[str]]:
    m: dict[str, list[str]] = defaultdict(list)
    for p in outline.get("pages", []):
        for f in p.get("files", []):
            m[f].append(p["id"])
    return m


def _symbols_for(files: list[str], structure: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    fs = set(files)
    syms = [(q, s) for q, s in (structure.get("symbols") or {}).items() if s["file"] in fs]
    return sorted(syms, key=lambda qs: (-(qs[1]["fan_in"] * 2 + qs[1]["fan_out"]), qs[0]))


def page_deps(page: dict[str, Any], structure: dict[str, Any], f2p: dict[str, list[str]]) -> Counter[str]:
    """Coupling weight from this page to every other page (file edges are undirected)."""
    own = set(page.get("files") or [])
    out: Counter[str] = Counter()
    for a, b, w in structure.get("file_edges") or []:
        for x, y in ((a, b), (b, a)):
            if x in own and y not in own:
                for other in f2p.get(y, []):
                    if other not in (page["id"], "overview", "1-overview"):
                        out[other] += w
    return out


def query_docs_for_page(
    page: dict[str, Any],
    structure: dict[str, Any],
    doc_rag: WikiRAG | None,
    top_k: int = 4,
) -> list[dict[str, Any]]:
    if doc_rag is None:
        return []
    syms = _symbols_for(_page_files(page), structure)
    sym_names = " ".join(s["name"] for _, s in syms[:10])
    q = f"{page['title']} {page.get('summary', '')} {sym_names}".strip()
    return doc_rag.query(q, top_k=top_k)


# ---------------------------------------------------------------------------- mermaid

def _mid(text: str) -> str:
    return "n_" + re.sub(r"\W", "_", text)


def _mlabel(text: str) -> str:
    return text.replace('"', "'")


def mermaid_page(page: dict[str, Any], outline: dict[str, Any], structure: dict[str, Any]) -> str:
    """File-level dependency graph inside the page, plus neighbouring pages as external nodes."""
    files = _page_files(page)
    f2p = _file_to_pages(outline)
    titles = {p["id"]: p["title"] for p in outline["pages"]}
    group_by_dir = len(files) > MERMAID_MAX_NODES
    node_of = (lambda f: str(PurePosixPath(f).parent) + "/") if group_by_dir else (lambda f: f)

    nodes: dict[str, str] = {}
    edges: Counter[tuple[str, str]] = Counter()
    own = set(files)
    for f in files:
        n = node_of(f)
        nodes[_mid(n)] = PurePosixPath(n).name + ("/" if group_by_dir else "")
    for a, b, w in structure["file_edges"]:
        if a in own and b in own:
            na, nb = _mid(node_of(a)), _mid(node_of(b))
            if na != nb:
                edges[tuple(sorted((na, nb)))] += w
        else:
            for x, y in ((a, b), (b, a)):
                if x in own and y not in own:
                    for other in f2p.get(y, [])[:1]:
                        if other not in (page["id"], "overview", "1-overview"):
                            edges[(_mid(node_of(x)), _mid("page:" + other))] += w
    ext = {e[1] for e in edges if e[1].startswith(_mid("page:"))}
    ext_rank = Counter({n: sum(w for e, w in edges.items() if e[1] == n) for n in ext})
    keep_ext = {n for n, _ in ext_rank.most_common(6)}

    out = ["```mermaid", "flowchart LR", f'  subgraph this["{_mlabel(page["title"])}"]']
    for nid, label in list(nodes.items())[:MERMAID_MAX_NODES]:
        out.append(f'    {nid}["{_mlabel(label)}"]')
    out.append("  end")
    for n in sorted(keep_ext):
        pid = n[len(_mid("page:")):]
        real = next((p["id"] for p in outline["pages"] if _mid("page:" + p["id"]) == n), pid)
        out.append(f'  {n}(["{_mlabel(titles.get(real, real))}"])')
    for (a, b), _w in sorted(edges.items(), key=lambda kv: -kv[1])[:40]:
        if a in nodes and (b in nodes or b in keep_ext):
            arrow = "-.->" if b in keep_ext else "---"
            out.append(f"  {a} {arrow} {b}")
    out.append("```")
    return "\n".join(out)


def mermaid_overview(outline: dict[str, Any], structure: dict[str, Any]) -> str:
    pages = [p for p in outline["pages"] if p["id"] not in ("overview", "1-overview") and p.get("parent") is None]
    comm_page: dict[int, str] = {}
    for p in pages:
        for c in p.get("communities", []):
            comm_page.setdefault(c, p["id"])
    edges: Counter[tuple[str, str]] = Counter()
    for a, b, w in structure["community_edges"]:
        pa, pb = comm_page.get(a), comm_page.get(b)
        if pa and pb and pa != pb:
            edges[tuple(sorted((pa, pb)))] += w
    out = ["```mermaid", "flowchart TD"]
    for p in pages:
        out.append(f'  {_mid(p["id"])}["{_mlabel(p["title"])}"]')
    max_w = max(edges.values(), default=1)
    for (a, b), w in sorted(edges.items(), key=lambda kv: -kv[1]):
        arrow = "===" if w >= max_w * 0.5 else "---"
        out.append(f"  {_mid(a)} {arrow} {_mid(b)}")
    out.append("```")
    return "\n".join(out)


def mermaid_class_diagram(files: list[str], structure: dict[str, Any], max_classes: int = 10) -> str:
    """Build a Mermaid classDiagram from Class/Struct symbols and their methods in `files`."""
    fs = set(files)
    syms = structure["symbols"]
    classes = [(q, s) for q, s in syms.items() if s["file"] in fs and s["label"] in ("Class", "Struct", "Interface")]
    classes.sort(key=lambda qs: (-(qs[1]["fan_in"] * 2 + qs[1]["fan_out"]), qs[0]))
    chosen = classes[:max_classes]
    if not chosen:
        return ""
    out = ["```mermaid", "classDiagram"]
    for q, c in chosen:
        cname = re.sub(r"\W", "_", c["name"])
        out.append(f"  class {cname} {{")
        methods = [
            s for mq, s in syms.items()
            if s["file"] == c["file"] and s["label"] == "Method" and mq.startswith(q + ".")
        ][:6]
        for m in methods:
            out.append(f"    +{m['name']}()")
        out.append("  }")
    out.append("```")
    return "\n".join(out)


# ---------------------------------------------------------------------------- page body

def synthesize_body(
    page: dict[str, Any],
    outline: dict[str, Any],
    structure: dict[str, Any],
    doc_hits: list[dict[str, Any]] | None = None,
) -> str:
    files = _page_files(page)
    syms = _symbols_for(files, structure)
    titles = {p["id"]: p["title"] for p in outline["pages"]}
    lines = [
        "<details>",
        "<summary>Relevant source files</summary>",
        "",
        "The following files were used as context for generating this wiki page:",
        "",
        *[f"- [{f}]({f})" for f in files[:30]],
        "",
        "</details>",
        "",
        page.get("summary") or f"Technical reference for `{page['title']}`.",
        "",
    ]
    if doc_hits:
        lines += ["## Architectural Context", ""]
        for h in doc_hits[:3]:
            excerpt = re.sub(r"\s+", " ", h["snippet"]).strip()[:360]
            lines.append(f"- **{h['title']}**: {excerpt}")
        lines += ["", "Sources: " + ", ".join(f"[{h['path']}]()" for h in doc_hits[:3]), ""]

    cdiag = mermaid_class_diagram(files, structure)
    if cdiag:
        lines += ["## Class Hierarchy & Structure", "", cdiag, ""]
        top_c = [s for _, s in syms if s["label"] in ("Class", "Struct")][:4]
        if top_c:
            lines += ["Sources: " + ", ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for s in top_c), ""]

    lines += ["## Key Components & APIs", "", "| Symbol | Kind | Location | Summary |", "|---|---|---|---|"]
    for _, s in syms[:20]:
        doc = (
            s["doc"].split("\n")[0][:110]
            if s["doc"]
            else f"fan-in {s['fan_in']}, fan-out {s['fan_out']}"
        ).replace("|", "\\|")
        lines.append(f"| `{s['name']}` | {s['label']} | [{s['file']}:{s['start']}-{s['end']}]() | {doc} |")
    if syms:
        lines += ["", "Sources: " + ", ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for _, s in syms[:5]), ""]

    deps = page_deps(page, structure, _file_to_pages(outline))
    if deps:
        lines += ["## Subsystem Interactions", ""]
        lines += [f"- [[{pid}|{titles.get(pid, pid)}]] (coupling weight {w:.1f})" for pid, w in deps.most_common(8)]
    return "\n".join(lines)


def synthesize_overview(outline: dict[str, Any], structure: dict[str, Any]) -> str:
    lines = ["## Subsystems", ""]
    for p in outline["pages"]:
        if p["id"] not in ("overview", "1-overview"):
            lines.append(f"- [[{p['id']}|{p['title']}]] — {p['summary']}")
    if structure["entry_points"]:
        lines += ["", "## Entry points", ""]
        lines += [f"- `{r.get('qn', '').split('.', 1)[-1]}` in `{r.get('file')}`" for r in structure["entry_points"]]
    if structure["routes"]:
        lines += ["", "## HTTP routes", ""]
        lines += [f"- `{r['method']} {r['path']}`" for r in structure["routes"][:40]]
    return "\n".join(lines)


# ---------------------------------------------------------------------------- post-processing

def fix_wikilinks(body: str, outline: dict[str, Any]) -> str:
    titles = {p["id"]: p["title"] for p in outline["pages"]}

    def repl(m: re.Match[str]) -> str:
        target, _, alias = m.group(1).partition("|")
        target = target.strip()
        if target in titles:
            return f"[[{target}|{alias or titles[target]}]]"
        return alias or target

    return re.sub(r"\[\[([^\]]+)\]\]", repl, body)


def link_citations(body: str, source_url: str | None) -> str:
    """Turn `path:12-34` citations into links when a browsable source URL is configured."""
    if not source_url:
        return body
    base = source_url.rstrip("/")

    def repl(m: re.Match[str]) -> str:
        path, a, b = m.group(1), m.group(2), m.group(3) or m.group(2)
        return f"[`{path}:{a}-{b}`]({base}/{path}#L{a}-L{b})"

    return re.sub(r"`([\w./-]+\.\w+):(\d+)(?:-(\d+))?`", repl, body)


# ---------------------------------------------------------------------------- generation

def generate_page(
    page: dict[str, Any],
    outline: dict[str, Any],
    structure: dict[str, Any],
    doc_rag: WikiRAG | None = None,
) -> dict[str, Any]:
    doc_hits = query_docs_for_page(page, structure, doc_rag)
    body = synthesize_body(page, outline, structure, doc_hits=doc_hits)
    doc_refs = [
        {"id": h["id"], "title": h["title"], "path": h["path"], "score": h["score"], "via": h["via"]}
        for h in doc_hits
    ]
    return {
        "id": page["id"],
        "body": body,
        "diagram": mermaid_page(page, outline, structure),
        "doc_refs": doc_refs,
        "generator": "deterministic",
    }


def generate_overview(outline: dict[str, Any], structure: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": outline["pages"][0]["id"] if outline.get("pages") else "1-overview",
        "body": synthesize_overview(outline, structure),
        "diagram": mermaid_overview(outline, structure),
        "generator": "deterministic",
    }


def generate_all(
    outline: dict[str, Any],
    structure: dict[str, Any],
    workers: int = 4,
    only: set[str] | None = None,
    existing: dict[str, dict[str, Any]] | None = None,
    doc_rag: WikiRAG | None = None,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = dict(existing or {})
    ov_ids = {"overview", "1-overview"}
    todo = [p for p in outline["pages"] if p["id"] not in ov_ids and (only is None or p["id"] in only)]
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for res in pool.map(lambda p: generate_page(p, outline, structure, doc_rag), todo):
            results[res["id"]] = res
            print(f"[pages] {res['id']} ({res['generator']})")
    ov_id = next((p["id"] for p in outline["pages"] if p["id"] in ov_ids), "1-overview")
    if only is None or ov_id in only or todo:
        results[ov_id] = generate_overview(outline, structure)
        print(f"[pages] {ov_id} ({results[ov_id]['generator']})")
    return results
