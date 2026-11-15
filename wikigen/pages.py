"""Step 2b — DeepWiki v1.9.9.5 Page & Multi-Diagram Synthesis (`git` + `CBM` + `llm-wiki`).

Reverse-engineered from `deepwiki.com` (v1.9.9.5):
Supports 4 distinct DeepWiki page archetypes:
  1. Top-Level `1-overview`: System Component Map, Pipeline Stages, Runtime Interaction, Backend/Subsystem Matrix.
  2. Parent Hub Pages (`2`, `3`, `5`, `8`...): `## Purpose and Scope` + one section & Mermaid diagram per child page.
  3. Leaf Technical Spec Pages (`1.1`, `3.1`, `8.1`...): `## Purpose and Scope`, numbered `## 1..5` sections separated by `---`,
     `Natural Language Space ↔ Code Entity Space` diagrams, `flowchart TD`, `classDiagram`, `sequenceDiagram`,
     grounded `git` source code excerpts, inline `[file:start-end]()` pill citations, and `Sources:` footers.
  4. `Glossary` (`10-glossary` / `*-glossary`): Domain vocabulary & file formats mapped to Code Entities with diagrams.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath
from typing import Any

from .llm import PAGE_SYSTEM_PROMPT, LocalLLMClient
from .wiki_rag import WikiRAG

MERMAID_MAX_NODES = 18

NOISE_SYM_PREFIXES = (
    "ET_CHECK", "ET_LOG", "ET_DCHECK", "TORCH_CHECK", "ARMNN_LOG", "BOOST_TEST",
    "bits1", "bits2", "bits4", "bits8", "bits16", "qint", "quint", "uoint",
)


def _page_files(page: dict[str, Any]) -> list[str]:
    return list(dict.fromkeys(page.get("files") or []))


def _file_to_pages(outline: dict[str, Any]) -> dict[str, list[str]]:
    m: dict[str, list[str]] = defaultdict(list)
    for p in outline.get("pages", []):
        for f in p.get("files", []):
            m[f].append(p["id"])
    return m


def _is_noise_symbol(name: str, file_path: str = "") -> bool:
    if name.startswith(NOISE_SYM_PREFIXES) or name in ("main", "init", "test", "setUp", "tearDown", "M", "Foo", "Bar"):
        return True
    fl = file_path.lower()
    if any(k in fl for k in ("/testing_util/", "/test_util/", "/tutorials_source/")):
        return True
    return False


def _symbols_for(files: list[str], structure: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    fs = set(files)
    file_order = {f: idx for idx, f in enumerate(files)}
    fmeta = structure.get("files") or {}
    syms = [(q, s) for q, s in (structure.get("symbols") or {}).items() if s["file"] in fs]
    return sorted(
        syms,
        key=lambda qs: (
            1 if _is_noise_symbol(qs[1]["name"], qs[1]["file"]) else 0,
            1 if (fmeta.get(qs[1]["file"]) or {}).get("is_test") or "/test" in qs[1]["file"].lower() else 0,
            1 if ("/c10/" in qs[1]["file"].lower() or "headeronly/" in qs[1]["file"].lower()) else 0,
            0 if qs[1]["label"] in ("Class", "Struct", "Interface") else 1,
            -(
                qs[1]["fan_in"] * 2
                + qs[1]["fan_out"]
                + (10 if qs[1].get("doc") else 0)
                + min(((qs[1].get("lines") or [0, 0])[1] - (qs[1].get("lines") or [0, 0])[0]) // 20, 18)
                - min(file_order.get(qs[1]["file"], 20) // 2, 12)
            ),
            qs[0],
        ),
    )


def read_source_snippet(
    repo_root: Path | str | None,
    file_path: str,
    start_line: int,
    end_line: int,
    max_lines: int = 20,
) -> tuple[str, int, int, str]:
    """Read a real source code slice from `repo_root / file_path` (`git` working tree)."""
    if not repo_root:
        return ("", start_line, end_line, "")
    full = Path(repo_root) / file_path
    if not full.is_file():
        return ("", start_line, end_line, "")
    try:
        raw_lines = full.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ("", start_line, end_line, "")
    if not raw_lines:
        return ("", start_line, end_line, "")
    s_idx = max(1, start_line or 1)
    e_idx = min(len(raw_lines), max(s_idx, end_line or (s_idx + max_lines - 1)), s_idx + max_lines - 1)
    snippet = "\n".join(raw_lines[s_idx - 1 : e_idx]).strip("\n")
    ext = PurePosixPath(file_path).suffix.lstrip(".").lower()
    lang_map = {
        "py": "python", "pyi": "python", "cpp": "cpp", "cc": "cpp", "c": "c",
        "h": "cpp", "hpp": "cpp", "mm": "objc", "m": "objc", "swift": "swift",
        "java": "java", "kt": "kotlin", "sh": "bash", "cmake": "cmake", "bzl": "python",
        "yaml": "yaml", "yml": "yaml", "toml": "toml", "json": "json", "fbs": "idl",
    }
    lang = lang_map.get(ext, "cpp" if "CMakeLists" not in file_path else "cmake")
    return (snippet, s_idx, e_idx, lang)


def page_deps(page: dict[str, Any], structure: dict[str, Any], f2p: dict[str, list[str]]) -> Counter[str]:
    """Coupling weight from this page to every other page."""
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
    top_k: int = 5,
) -> list[dict[str, Any]]:
    if doc_rag is None:
        return []
    syms = _symbols_for(_page_files(page), structure)
    sym_names = " ".join(s["name"] for _, s in syms[:12])
    q = f"{page['title']} {page.get('summary', '')} {sym_names}".strip()
    return [h for h in doc_rag.query(q, top_k=top_k + 2) if h["id"] != page["id"]][:top_k]


# ---------------------------------------------------------------------------- mermaid

def _mid(text: str) -> str:
    return "n_" + re.sub(r"\W", "_", text)[:48]


def _mlabel(text: str) -> str:
    return re.sub(r'["\[\]{}<>|`]', "'", text).strip()


def _humanize_symbol_concept(name: str, label: str) -> str:
    """Turn a symbol name like `EdgeProgramManager` or `load_method` into a Natural Language Space concept."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name.lstrip("_"))
    s = s.replace("_", " ").strip().title()
    if label in ("Function", "Method") and not s.lower().endswith(("flow", "execution", "handler", "pass")):
        return f"{s} Operation"
    return s or name


def mermaid_nl_to_code_diagram(files: list[str], structure: dict[str, Any], max_items: int = 6) -> str:
    """DeepWiki v1.9.9.5 signature diagram: `Natural Language Space` <-> `Code Entity Space`."""
    syms = _symbols_for(files, structure)
    chosen: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for _q, s in syms:
        if s["name"] in seen_names or len(s["name"]) < 4:
            continue
        seen_names.add(s["name"])
        chosen.append(s)
        if len(chosen) >= max_items:
            break
    if len(chosen) < 2:
        return ""

    out = [
        "```mermaid",
        "graph LR",
        '  subgraph NL_Space["Natural Language Space"]',
    ]
    for i, s in enumerate(chosen):
        concept = _mlabel(_humanize_symbol_concept(s["name"], s["label"]))
        out.append(f'    NL_{i}["{concept}"]')
    out.append("  end")
    out.append('  subgraph Code_Space["Code Entity Space"]')
    for i, s in enumerate(chosen):
        fname = PurePosixPath(s["file"]).name
        lbl = _mlabel(f"{s['name']} ({fname}:{s['start']})")
        out.append(f'    CE_{i}["{lbl}"]')
    out.append("  end")
    for i, s in enumerate(chosen):
        verb = "implemented by" if s["label"] in ("Class", "Struct", "Interface") else "invokes"
        out.append(f'  NL_{i} -->|"{verb}"| CE_{i}')
    for i in range(len(chosen) - 1):
        if chosen[i]["label"] in ("Class", "Struct") and chosen[i + 1]["label"] in ("Function", "Method"):
            out.append(f"  CE_{i} -.-> CE_{i + 1}")
    out.append("```")
    return "\n".join(out)


def mermaid_page(page: dict[str, Any], outline: dict[str, Any], structure: dict[str, Any]) -> str:
    """Subsystem architecture flowchart (`flowchart TD`) with code entities and cross-page links."""
    files = _page_files(page)
    syms = _symbols_for(files, structure)
    f2p = _file_to_pages(outline)
    titles = {p["id"]: p["title"] for p in outline["pages"]}
    group_by_dir = len(files) > MERMAID_MAX_NODES
    node_of = (lambda f: str(PurePosixPath(f).parent) or "root") if group_by_dir else (lambda f: f)

    top_sym_by_file: dict[str, str] = {}
    for _q, s in syms:
        top_sym_by_file.setdefault(s["file"], s["name"])

    nodes_by_group: dict[str, list[tuple[str, str]]] = defaultdict(list)
    seen_nodes: dict[str, str] = {}
    edges: Counter[tuple[str, str]] = Counter()
    own = set(files)

    for f in files:
        if f.startswith("docs/"):
            continue
        n = node_of(f)
        nid = _mid(n)
        if nid not in seen_nodes:
            if group_by_dir:
                label = PurePosixPath(n).name + "/"
            else:
                sym_hint = top_sym_by_file.get(f)
                label = f"{sym_hint} ({PurePosixPath(f).name})" if sym_hint else PurePosixPath(f).name
            seen_nodes[nid] = label
            grp = str(PurePosixPath(n).parent) if group_by_dir else (str(PurePosixPath(f).parent) or "root")
            nodes_by_group[grp].append((nid, label))
            if len(seen_nodes) >= MERMAID_MAX_NODES:
                break

    for a, b, w in structure.get("file_edges") or []:
        if a in own and b in own:
            na, nb = _mid(node_of(a)), _mid(node_of(b))
            if na != nb and na in seen_nodes and nb in seen_nodes:
                edges[tuple(sorted((na, nb)))] += w
        else:
            for x, y in ((a, b), (b, a)):
                if x in own and y not in own:
                    nx_id = _mid(node_of(x))
                    if nx_id not in seen_nodes:
                        continue
                    for other in f2p.get(y, [])[:1]:
                        if other not in (page["id"], "overview", "1-overview"):
                            edges[(nx_id, _mid("page:" + other))] += w

    ext = {e[1] for e in edges if e[1].startswith(_mid("page:"))}
    ext_rank = Counter({n: sum(w for e, w in edges.items() if e[1] == n) for n in ext})
    keep_ext = {n for n, _ in ext_rank.most_common(4)}

    out = ["```mermaid", "flowchart TD", f'  subgraph sub_this["{_mlabel(page["title"])}"]']
    for grp_idx, (grp, items) in enumerate(list(nodes_by_group.items())[:5]):
        gname = _mlabel(grp if grp not in ("", ".") else "Core Code Entities")
        out.append(f'    subgraph sg_{grp_idx}["{gname}"]')
        for nid, label in items[:7]:
            out.append(f'      {nid}["{_mlabel(label)}"]')
        out.append("    end")
    out.append("  end")

    for n in sorted(keep_ext):
        pid = n[len(_mid("page:")):]
        real = next((p["id"] for p in outline["pages"] if _mid("page:" + p["id"]) == n), pid)
        out.append(f'  {n}(["{_mlabel(titles.get(real, real))}"])')
    for (a, b), _w in sorted(edges.items(), key=lambda kv: -kv[1])[:24]:
        if a in seen_nodes and (b in seen_nodes or b in keep_ext):
            arrow = "-.->" if b in keep_ext else "-->"
            out.append(f"  {a} {arrow} {b}")
    out.append("```")
    return "\n".join(out)


def mermaid_overview(outline: dict[str, Any], structure: dict[str, Any]) -> str:
    """Top-level architecture diagram grouping child pages under their top-level parent sections."""
    top_pages = [
        p for p in outline["pages"]
        if p["id"] not in ("overview", "1-overview") and not p["id"].endswith("-glossary") and p.get("parent") is None
    ]
    children_by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in outline["pages"]:
        if p.get("parent"):
            children_by_parent[p["parent"]].append(p)

    comm_page: dict[int, str] = {}
    for p in outline["pages"]:
        if p.get("parent"):
            for c in p.get("communities", []):
                comm_page.setdefault(c, p["id"])
    for p in top_pages:
        for c in p.get("communities", []):
            comm_page.setdefault(c, p["id"])

    edges: Counter[tuple[str, str]] = Counter()
    for a, b, w in structure.get("community_edges") or []:
        pa, pb = comm_page.get(a), comm_page.get(b)
        if pa and pb and pa != pb:
            edges[tuple(sorted((pa, pb)))] += w

    out = ["```mermaid", "flowchart TD"]
    rendered_ids: set[str] = set()
    for tp in top_pages:
        kids = children_by_parent.get(tp["id"], [])
        if kids:
            out.append(f'  subgraph {_mid(tp["id"])}["{_mlabel(tp["title"])}"]')
            for k in kids[:6]:
                out.append(f'    {_mid(k["id"])}["{_mlabel(k["title"])}"]')
                rendered_ids.add(k["id"])
            out.append("  end")
        else:
            out.append(f'  {_mid(tp["id"])}["{_mlabel(tp["title"])}"]')
            rendered_ids.add(tp["id"])

    max_w = max(edges.values(), default=1)
    for (a, b), w in sorted(edges.items(), key=lambda kv: -kv[1])[:22]:
        if a in rendered_ids and b in rendered_ids:
            arrow = "==>" if w >= max_w * 0.45 else "-->"
            out.append(f"  {_mid(a)} {arrow} {_mid(b)}")
    out.append("```")
    return "\n".join(out)


def mermaid_class_diagram(files: list[str], structure: dict[str, Any], max_classes: int = 8) -> str:
    """Build a Mermaid classDiagram with real methods and INHERITS arrows."""
    fs = set(files)
    syms = structure.get("symbols") or {}
    classes = [(q, s) for q, s in syms.items() if s["file"] in fs and s["label"] in ("Class", "Struct", "Interface")]
    classes.sort(key=lambda qs: (-(qs[1]["fan_in"] * 2 + qs[1]["fan_out"]), qs[0]))
    chosen = classes[:max_classes]
    if not chosen:
        return ""

    chosen_qns: dict[str, str] = {}
    used_cnames: set[str] = set()
    dedup_chosen: list[tuple[str, dict[str, Any]]] = []
    for q, c in chosen:
        cname = re.sub(r"\W", "_", c["name"])[:40]
        if not cname or cname in used_cnames:
            continue
        used_cnames.add(cname)
        chosen_qns[q] = cname
        dedup_chosen.append((q, c))

    out = ["```mermaid", "classDiagram"]
    for q, c in dedup_chosen:
        cname = chosen_qns[q]
        out.append(f"  class {cname} {{")
        c_start, c_end = c.get("start", 0), c.get("end", 0)
        methods = [
            s for mq, s in syms.items()
            if s["file"] == c["file"]
            and s["label"] in ("Method", "Function")
            and (
                mq.startswith(q + ".")
                or f".{c['name']}." in mq
                or (c_start > 0 and c_end >= c_start and c_start <= s.get("start", 0) <= c_end)
            )
        ][:6]
        seen_m: set[str] = set()
        for m in methods:
            mname = re.sub(r"\W", "_", m["name"])[:32]
            if mname and mname not in seen_m:
                seen_m.add(mname)
                out.append(f"    +{mname}()")
        out.append("  }")

    added_inh = 0
    for child_qn, parent_qn in structure.get("inherits") or []:
        if child_qn in chosen_qns or parent_qn in chosen_qns:
            c_sym = syms.get(child_qn)
            p_sym = syms.get(parent_qn)
            if c_sym and p_sym:
                c_id = chosen_qns.get(child_qn) or re.sub(r"\W", "_", c_sym["name"])[:40]
                p_id = chosen_qns.get(parent_qn) or re.sub(r"\W", "_", p_sym["name"])[:40]
                if c_id != p_id:
                    out.append(f"  {p_id} <|-- {c_id}")
                    added_inh += 1
                    if added_inh >= 10:
                        break
    out.append("```")
    return "\n".join(out)


def mermaid_sequence_diagram(files: list[str], structure: dict[str, Any], max_steps: int = 8) -> str:
    """Build a Mermaid sequenceDiagram from real CBM call_edges (or top symbol interactions)."""
    fs = set(files)
    syms = structure.get("symbols") or {}
    page_calls: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for sq, dq in structure.get("call_edges") or []:
        sa, sb = syms.get(sq), syms.get(dq)
        if not sa or not sb:
            continue
        if _is_noise_symbol(sa["name"]) or _is_noise_symbol(sb["name"]):
            continue
        if sa["file"] in fs and (sb["file"] in fs or sb.get("fan_in", 0) >= 3):
            if sa["name"] != sb["name"]:
                page_calls.append((sa, sb))

    page_calls.sort(key=lambda ab: -(ab[0]["fan_in"] + ab[0]["fan_out"] + ab[1]["fan_in"] * 2))

    steps: list[tuple[str, str, str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()
    participants: dict[str, str] = {}

    def _actor_of(s: dict[str, Any]) -> tuple[str, str]:
        stem = PurePosixPath(s["file"]).stem
        aid = re.sub(r"\W", "_", stem)[:28] or "Module"
        return aid, stem

    for sa, sb in page_calls:
        a_id, a_lbl = _actor_of(sa)
        b_id, b_lbl = _actor_of(sb)
        if a_id == b_id and len(files) > 1:
            continue
        pair = (a_id, sb["name"])
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        participants.setdefault(a_id, a_lbl)
        participants.setdefault(b_id, b_lbl)
        steps.append((a_id, b_id, sb["name"], sa["name"]))
        if len(steps) >= max_steps or len(participants) >= 6:
            break

    if len(steps) < 2:
        top_syms = _symbols_for(files, structure)[:6]
        if len(top_syms) >= 2:
            for i in range(len(top_syms) - 1):
                sa, sb = top_syms[i][1], top_syms[i + 1][1]
                a_id, a_lbl = _actor_of(sa)
                b_id, b_lbl = _actor_of(sb)
                participants.setdefault(a_id, a_lbl)
                participants.setdefault(b_id, b_lbl)
                steps.append((a_id, b_id, sb["name"], sa["name"]))

    if not steps and files:
        participants["Caller"] = "Caller / Build"
        for idx, f in enumerate(files[:3]):
            fid = f"F{idx}"
            participants[fid] = PurePosixPath(f).name
            prev = "Caller" if idx == 0 else f"F{idx - 1}"
            steps.append((prev, fid, PurePosixPath(f).name, "configure" if idx == 0 else "invoke"))

    if not steps:
        return ""

    out = ["```mermaid", "sequenceDiagram"]
    for pid, plbl in participants.items():
        out.append(f'  participant {pid} as "{_mlabel(plbl)}"')
    for a_id, b_id, callee_name, caller_name in steps:
        msg = _mlabel(f"{caller_name}() -> {callee_name}()")
        out.append(f"  {a_id}->>{b_id}: {msg}")
    out.append("```")
    return "\n".join(out)


# ---------------------------------------------------------------------------- page archetypes

def synthesize_parent_hub(
    page: dict[str, Any],
    children: list[dict[str, Any]],
    outline: dict[str, Any],
    structure: dict[str, Any],
    doc_hits: list[dict[str, Any]] | None = None,
) -> str:
    """DeepWiki v1.9.9.5 Archetype B: Parent Chapter Hub Page (`2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`)."""
    files = _page_files(page)
    syms = _symbols_for(files, structure)

    lines = [
        "<details>",
        "<summary>Relevant source files</summary>",
        "",
        "The following files were used as context for generating this wiki page:",
        "",
        *[f"- [{f}]({f})" for f in files[:35]],
        "",
        "</details>",
        "",
        "## Purpose and Scope",
        "",
        f"This chapter covers **{page['title']}** across the repository, detailing the core abstractions, "
        f"data structures, transformation pipelines, and runtime/build integrations that implement this layer.",
        "",
        "**Scope**: This document provides an architectural hub for the following child subsystems:",
    ]
    for ch in children:
        lines.append(f"- **{ch['title']}**: See [[{ch['id']}|{ch['title']}]].")
    lines.append("")
    if syms:
        lines.append("Sources: " + ", ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for _, s in syms[:4]))
        lines.append("")

    # Overview diagram bridging Natural Language Space to Code Entity Space across the chapter
    nl_diag = mermaid_nl_to_code_diagram(files, structure, max_items=6)
    if nl_diag:
        lines += [
            "---",
            "",
            "## System Mapping: Natural Language Space to Code Entity Space",
            "",
            nl_diag,
            "",
        ]
        if syms:
            lines.append("Sources: " + ", ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for _, s in syms[:5]))
            lines.append("")

    # One dedicated section + Mermaid diagram per child page (matching deepwiki.com `3-exir-core-system`!)
    for idx, ch in enumerate(children, 1):
        ch_files = _page_files(ch)
        ch_syms = _symbols_for(ch_files, structure)
        top_classes = [s for _, s in ch_syms if s["label"] in ("Class", "Struct", "Interface")][:4]
        top_funcs = [s for _, s in ch_syms if s["label"] in ("Function", "Method")][:4]
        cite_str = ", ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for _, s in ch_syms[:3])

        lines += [
            "---",
            "",
            f"## {idx}. {ch['title']}",
            "",
            f"{ch.get('summary', '')} {cite_str}".strip(),
            "",
        ]
        if top_classes or top_funcs:
            lines.append("### Primary Code Entities")
            lines.append("")
            for s in (top_classes + top_funcs)[:6]:
                doc = re.sub(r"\s+", " ", s.get("doc") or s.get("signature") or "").strip()[:180]
                lines.append(
                    f"- **`{s['name']}`** ({s['label']} in [{s['file']}:{s['start']}-{s['end']}]()): "
                    f"{doc or 'Core implementation entity.'}"
                )
            lines.append("")

        lines += [
            f"### {ch['title']} Architecture Flow",
            "",
            mermaid_page(ch, outline, structure),
            "",
            f"For details, see [[{ch['id']}|{ch['title']}]].",
            "",
        ]
        if ch_syms:
            lines.append("Sources: " + ", ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for _, s in ch_syms[:4]))
        elif ch_files:
            lines.append("Sources: " + ", ".join(f"[{f}]()" for f in ch_files[:4]))
        lines.append("")

    if doc_hits:
        lines += [
            "---",
            "",
            "## Official Documentation & Architectural References",
            "",
        ]
        for h in doc_hits[:4]:
            excerpt = re.sub(r"\s+", " ", h.get("snippet", "")).strip()[:360]
            lines.append(f"- **{h['title']}** ([{h['path']}]()): {excerpt}")
        lines += ["", "Sources: " + ", ".join(f"[{h['path']}]()" for h in doc_hits[:4]), ""]

    return "\n".join(lines)


def synthesize_glossary(
    page: dict[str, Any],
    outline: dict[str, Any],
    structure: dict[str, Any],
    doc_rag: WikiRAG | None = None,
) -> str:
    """DeepWiki v1.9.9.5 Archetype D: Domain Glossary (`10-glossary` / `*-glossary`)."""
    files = _page_files(page)
    syms = structure.get("symbols") or {}

    lines = [
        "<details>",
        "<summary>Relevant source files</summary>",
        "",
        "The following files were used as context for generating this wiki page:",
        "",
        *[f"- [{f}]({f})" for f in files[:35]],
        "",
        "</details>",
        "",
        "## Purpose and Scope",
        "",
        "This page provides definitions and technical context for codebase-specific terms, jargon, "
        "abbreviations, file formats, and domain concepts used throughout the repository. Every concept is "
        "mapped directly to its concrete implementation in the **Code Entity Space**.",
        "",
    ]

    # Group high-centrality non-test symbols across the repository into conceptual categories
    fs = set(files)
    fmeta = structure.get("files") or {}
    all_ranked = sorted(
        [
            (q, s)
            for q, s in syms.items()
            if not _is_noise_symbol(s["name"], s["file"])
            and len(s["name"]) >= 4
            and not (fmeta.get(s["file"]) or {}).get("is_test")
            and not any(t in s["file"].lower() for t in ("/test/", "/tests/", "_test.", "/testing_util/", "/c10/", "headeronly/"))
        ],
        key=lambda qs: (
            0 if qs[1]["file"] in fs else 1,
            0 if qs[1]["label"] in ("Class", "Struct", "Interface") else 1,
            -(qs[1]["fan_in"] * 2 + qs[1]["fan_out"] + (15 if qs[1].get("doc") else 0)),
        ),
    )

    categories: list[tuple[str, str, list[tuple[str, dict[str, Any]]]]] = [
        (
            "Core Compilation, IR & Graph Concepts",
            "Intermediate representations, graph lowering managers, dialect verifiers, and serialization formats.",
            [(q, s) for q, s in all_ranked if any(k in s["file"].lower() for k in ("exir", "export", "compiler", "ir", "graph", "pass", "schema", "emit"))][:10],
        ),
        (
            "Backend Delegation, Partitioning & Hardware Formats",
            "Graph partitioning interfaces, capability specifications, and hardware accelerator delegates.",
            [(q, s) for q, s in all_ranked if any(k in s["file"].lower() for k in ("backend", "partition", "delegate", "tosa", "vulkan", "qnn", "xnnpack", "coreml"))][:10],
        ),
        (
            "Runtime Execution, Memory & Serialization Entities",
            "On-device execution engines, tagged value unions, memory allocators, data loaders, and profiling tools.",
            [(q, s) for q, s in all_ranked if any(k in s["file"].lower() for k in ("runtime", "executor", "memory", "evalue", "kernel", "etdump", "devtools", "module"))][:10],
        ),
    ]

    for sec_idx, (cat_title, cat_desc, cat_syms) in enumerate(categories, 1):
        if not cat_syms:
            continue
        lines += [
            "---",
            "",
            f"## {sec_idx}. {cat_title}",
            "",
            cat_desc,
            "",
        ]
        for _q, s in cat_syms[:6]:
            doc = re.sub(r"\s+", " ", s.get("doc") or "").strip()[:260]
            sig = s.get("signature") or f"{s['label']} {s['name']}"
            fallback_doc = f"Core {s['label'].lower()} defined in `{s['file']}`."
            lines += [
                f"### `{s['name']}` ({_humanize_symbol_concept(s['name'], s['label'])})",
                "",
                doc or fallback_doc,
                "",
                "**Code Entities:**",
                f"- `{s['name']}` (`{sig[:110]}`): [{s['file']}:{s['start']}-{s['end']}]() (fan-in `{s['fan_in']}`, fan-out `{s['fan_out']}`).",
                "",
            ]
        cat_files = list(dict.fromkeys(s["file"] for _, s in cat_syms))
        nl_diag = mermaid_nl_to_code_diagram(cat_files, structure, max_items=5)
        if nl_diag:
            lines += [
                f"### Diagram: Natural Language Space to Code Entity Space ({cat_title.split(',')[0]})",
                "",
                nl_diag,
                "",
            ]
        lines.append("Sources: " + ", ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for _, s in cat_syms[:5]))
        lines.append("")

    return "\n".join(lines)


def synthesize_body(
    page: dict[str, Any],
    outline: dict[str, Any],
    structure: dict[str, Any],
    doc_hits: list[dict[str, Any]] | None = None,
) -> str:
    """Synthesize a DeepWiki v1.9.9.5 page (dispatching Parent Hubs, Glossary, and Leaf Technical Specs)."""
    pid = page["id"]
    if pid.endswith("-glossary") or page.get("title", "").lower().endswith("glossary"):
        return synthesize_glossary(page, outline, structure)

    children = [p for p in outline.get("pages", []) if p.get("parent") == pid]
    if children and pid not in ("overview", "1-overview"):
        return synthesize_parent_hub(page, children, outline, structure, doc_hits=doc_hits)

    # Archetype C: Leaf Technical Specification Page
    files = _page_files(page)
    syms = _symbols_for(files, structure)
    titles = {p["id"]: p["title"] for p in outline["pages"]}
    f2p = _file_to_pages(outline)
    deps = page_deps(page, structure, f2p)
    repo_root = structure.get("repo_root")

    top_classes = [(q, s) for q, s in syms if s["label"] in ("Class", "Struct", "Interface")]
    top_funcs = [(q, s) for q, s in syms if s["label"] in ("Function", "Method")]
    key_entities = ", ".join(f"`{s['name']}` ([{s['file']}:{s['start']}-{s['end']}]())" for _, s in syms[:5])

    lines = [
        "<details>",
        "<summary>Relevant source files</summary>",
        "",
        "The following files were used as context for generating this wiki page:",
        "",
        *[f"- [{f}]({f})" for f in files[:35]],
        "",
        "</details>",
        "",
        "## Purpose and Scope",
        "",
        page.get("summary") or f"This document details the architecture and implementation of {page['title']}.",
        "",
    ]
    if key_entities:
        lines.append(f"Primary code entities analyzed on this page include {key_entities}.")
        lines.append("")
    if page.get("parent") and page["parent"] in titles:
        p_id = page["parent"]
        siblings = [p for p in outline["pages"] if p.get("parent") == p_id and p["id"] != pid][:4]
        sib_str = ", ".join(f"[[{s['id']}|{s['title']}]]" for s in siblings)
        lines.append(
            f"For the parent architectural layer, see [[{p_id}|{titles[p_id]}]]."
            + (f" Related sibling subsystems: {sib_str}." if sib_str else "")
        )
        lines.append("")
    if syms:
        lines += ["Sources: " + ", ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for _, s in syms[:4]), ""]
    elif files:
        lines += ["Sources: " + ", ".join(f"[{f}]()" for f in files[:4]), ""]

    # Section 1: High-Level Architecture & Natural Language <-> Code Entity Mapping
    lines += [
        "---",
        "",
        "## 1. High-Level Architecture and Data Flow",
        "",
    ]
    nl_diag = mermaid_nl_to_code_diagram(files, structure, max_items=6)
    if nl_diag:
        lines += [
            "### Natural Language Space to Code Entity Space Mapping",
            "",
            "The following diagram maps domain concepts in this subsystem to their concrete code entities:",
            "",
            nl_diag,
            "",
        ]

    lines += [
        "### Subsystem Component & Dependency Flow",
        "",
        mermaid_page(page, outline, structure),
        "",
    ]
    if deps:
        top_dep_str = ", ".join(f"[[{other_id}|{titles.get(other_id, other_id)}]] (coupling `{w:.1f}`)" for other_id, w in deps.most_common(5))
        lines.append(f"Cross-subsystem call and import edges connect **{page['title']}** with {top_dep_str}.")
        lines.append("")

    # Summarize module directories with inline citations
    by_dir: dict[str, list[str]] = defaultdict(list)
    for f in files:
        if not f.startswith("docs/"):
            by_dir[str(PurePosixPath(f).parent) or "."].append(f)
    if by_dir:
        lines += [
            "| Module Directory | Files | Primary Code Entities | Source Citations |",
            "|---|---|---|---|",
        ]
        for d, dfiles in sorted(by_dir.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:8]:
            dset = set(dfiles)
            dsyms = [s for _, s in syms if s["file"] in dset]
            top_names = ", ".join(f"`{s['name']}`" for s in dsyms[:4]) or "*(build / config)*"
            cites = " ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for s in dsyms[:2]) or f"[{dfiles[0]}]()"
            lines.append(f"| `{d}` | {len(dfiles)} | {top_names} | {cites} |")
        lines.append("")

    if syms:
        lines += ["Sources: " + ", ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for _, s in syms[:5]), ""]
    elif files:
        lines += ["Sources: " + ", ".join(f"[{f}]()" for f in files[:5]), ""]

    # Section 2: Core Data Structures, Classes & Grounded Source Excerpts
    cdiag = mermaid_class_diagram(files, structure)
    featured_syms = (top_classes[:5] + top_funcs[:4])[:6]
    if cdiag or featured_syms:
        lines += [
            "---",
            "",
            "## 2. Core Data Structures and Implementation Details",
            "",
        ]
        if cdiag:
            lines += [
                "### Class and Entity Relationship Diagram",
                "",
                cdiag,
                "",
            ]

        snippets_added = 0
        for _q, s in featured_syms:
            doc = re.sub(r"\s+", " ", s.get("doc") or "").strip()[:320]
            sig = s.get("signature") or f"{s['label']} {s['name']}"
            lines += [
                f"### `{s['name']}` ({s['label']})",
                "",
                f"- **Source Location**: [{s['file']}:{s['start']}-{s['end']}]()",
                f"- **Declaration**: `{sig[:140]}`",
                f"- **Graph Centrality**: fan-in `{s['fan_in']}` callers, fan-out `{s['fan_out']}` callees",
            ]
            if doc:
                lines.append(f"- **Responsibility**: {doc}")
            lines.append("")
            if snippets_added < 3 and repo_root:
                code_str, l_start, l_end, lang = read_source_snippet(repo_root, s["file"], s["start"], s["end"], max_lines=16)
                if code_str and len(code_str.splitlines()) >= 3:
                    lines += [
                        f"```{lang}",
                        f"// {s['file']}:{l_start}-{l_end}",
                        code_str,
                        "```",
                        "",
                    ]
                    snippets_added += 1

        lines += ["Sources: " + ", ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for _, s in featured_syms[:5]), ""]

    # Section 3: Execution & Control Flow (Sequence Diagram)
    sdiag = mermaid_sequence_diagram(files, structure)
    if sdiag:
        lines += [
            "---",
            "",
            "## 3. Execution and Call Flow",
            "",
            "The sequence diagram below traces the runtime/compile-time call chain across components in this module:",
            "",
            sdiag,
            "",
        ]
        if syms:
            lines += ["Sources: " + ", ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for _, s in syms[:5]), ""]

    # Section 4: Key API & Symbol Reference Table
    if syms:
        lines += [
            "---",
            "",
            "## 4. Key API and Symbol Reference",
            "",
            "| Code Entity | Kind | Location | Fan-In / Out | Role & Signature |",
            "|---|---|---|---|---|",
        ]
        for _, s in syms[:22]:
            raw_desc = s["doc"].split("\n")[0][:110] if s.get("doc") else (s.get("signature") or "")[:110]
            desc = re.sub(r"\s+", " ", raw_desc).replace("|", "\\|").strip() or "—"
            lines.append(
                f"| `{s['name']}` | {s['label']} | [{s['file']}:{s['start']}-{s['end']}]() | "
                f"`{s['fan_in']}` / `{s['fan_out']}` | {desc} |"
            )
        lines += ["", "Sources: " + ", ".join(f"[{s['file']}:{s['start']}-{s['end']}]()" for _, s in syms[:6]), ""]

    # Section 5: Official Documentation & Design Context (`llm-wiki` / `raw/`)
    if doc_hits:
        lines += [
            "---",
            "",
            "## 5. Official Documentation and Design Context",
            "",
            "The following linked documentation sections from `llm-wiki` (`raw/`) provide additional "
            "architectural context, tutorials, and design invariants for this subsystem:",
            "",
        ]
        for h in doc_hits[:4]:
            excerpt = re.sub(r"\s+", " ", h.get("snippet", "")).strip()[:420]
            headings = ", ".join(f"`{hd}`" for hd in (h.get("headings") or [])[:4])
            h_note = f" (sections: {headings})" if headings else ""
            cite_path = h["path"][len("raw/executorch/"):] if h["path"].startswith("raw/executorch/") else h["path"]
            lines.append(f"- **{h['title']}** ([{cite_path}](), score `{h['score']}`){h_note}: {excerpt}")
        lines += [
            "",
            "Sources: " + ", ".join(
                f"[{h['path'][len('raw/executorch/'):] if h['path'].startswith('raw/executorch/') else h['path']}]()"
                for h in doc_hits[:4]
            ),
            "",
        ]

    return "\n".join(lines)


def synthesize_overview(
    outline: dict[str, Any],
    structure: dict[str, Any],
    doc_rag: WikiRAG | None = None,
) -> str:
    """DeepWiki v1.9.9.5 Archetype A: Top-Level `1-overview` Page."""
    pages = outline.get("pages", [])
    ov_page = pages[0] if pages else {"files": []}
    top_chapters = [p for p in pages if p["id"] not in ("overview", "1-overview") and p.get("parent") is None]
    top_files = list(dict.fromkeys((ov_page.get("files") or []) + [f for p in top_chapters for f in (p.get("files") or [])[:2]]))[:24]
    doc_hits = doc_rag.query(f"{outline.get('title', '')} overview architecture concepts getting started", top_k=5) if doc_rag else []

    lines = [
        "<details>",
        "<summary>Relevant source files</summary>",
        "",
        "The following files were used as context for generating this wiki page:",
        "",
        *[f"- [{f}]({f})" for f in top_files],
        "",
        "</details>",
        "",
        f"**{outline.get('title', 'DeepWiki').replace(' DeepWiki', '')}** comprises **{len(structure.get('files', {}))} "
        f"indexed code files**, **{len(structure.get('symbols', {}))} symbols**, and **{len(structure.get('file_edges', []))} "
        f"inter-file dependency edges** [README.md:1-30]().",
        "",
        "**Scope**: This page provides a high-level architecture overview, compilation/execution lifecycle, and "
        "subsystem navigation map. For detailed technical specifications on each layer:",
    ]
    for ch in top_chapters:
        lines.append(f"- **{ch['title']}**: See [[{ch['id']}|{ch['title']}]].")
    lines += [
        "",
        "Sources: " + ", ".join(f"[{f}]()" for f in top_files[:4]),
        "",
        "---",
        "",
        "## 1. Architecture Overview & System Component Map",
        "",
        "This diagram maps the repository's high-level architectural chapters and subsystems to their primary modules:",
        "",
        mermaid_overview(outline, structure),
        "",
    ]

    nl_diag = mermaid_nl_to_code_diagram(ov_page.get("files") or top_files, structure, max_items=6)
    if nl_diag:
        lines += [
            "### Core Concept to Code Entity Mapping",
            "",
            nl_diag,
            "",
        ]

    ov_cls_diag = mermaid_class_diagram(ov_page.get("files") or top_files, structure, max_classes=6)
    if ov_cls_diag:
        lines += [
            "### Core Compilation & Runtime Class Hierarchy",
            "",
            ov_cls_diag,
            "",
        ]

    if doc_hits:
        lines += ["### Architectural Principles (from Official Documentation)", ""]
        for h in doc_hits[:4]:
            excerpt = re.sub(r"\s+", " ", h.get("snippet", "")).strip()[:380]
            cite_path = h["path"][len("raw/executorch/"):] if h["path"].startswith("raw/executorch/") else h["path"]
            lines.append(f"- **{h['title']}** ([{cite_path}]()): {excerpt}")
        lines += [
            "",
            "Sources: " + ", ".join(
                f"[{h['path'][len('raw/executorch/'):] if h['path'].startswith('raw/executorch/') else h['path']}]()"
                for h in doc_hits[:4]
            ),
            "",
        ]

    lines += [
        "---",
        "",
        "## 2. Subsystem Catalog & Navigation Matrix",
        "",
        "| Section | Page | Files | Parent Chapter | Primary Focus & Code Entities |",
        "|---|---|---|---|---|",
    ]
    titles = {p["id"]: p["title"] for p in pages}
    for p in pages:
        if p["id"] in ("overview", "1-overview"):
            continue
        sec = p.get("section_id") or "—"
        parent_link = f"[[{p['parent']}|{titles.get(p['parent'], p['parent'])}]]" if p.get("parent") else "**Top-Level Chapter**"
        summary = re.sub(r"\s+", " ", p.get("summary", "")).replace("|", "\\|")[:150]
        lines.append(f"| `{sec}` | [[{p['id']}|{p['title']}]] | {len(p.get('files', []))} | {parent_link} | {summary} |")
    lines.append("")

    if structure.get("languages"):
        lines += [
            "---",
            "",
            "## 3. Language Breakdown & Repository Statistics",
            "",
            "| Language | Indexed File Count |",
            "|---|---|",
        ]
        for r in structure["languages"][:10]:
            lines.append(f"| `{r.get('language')}` | {r.get('files')} |")
        lines.append("")

    if structure.get("entry_points"):
        lines += ["---", "", "## 4. Primary Entry Points", ""]
        for r in structure["entry_points"][:20]:
            lines.append(f"- `{r.get('qn', '').split('.', 1)[-1]}` in [{r.get('file')}]()")
        lines += ["", "Sources: " + ", ".join(f"[{r.get('file')}]()" for r in structure["entry_points"][:5] if r.get("file")), ""]

    return "\n".join(lines)


# ---------------------------------------------------------------------------- post-processing

def fix_wikilinks(body: str, outline: dict[str, Any]) -> str:
    titles = {p["id"]: p["title"] for p in outline["pages"]}
    fences: list[str] = []
    protected = re.sub(r"```[\s\S]*?```", lambda m: (fences.append(m.group(0)), f"@@FENCE_{len(fences)-1}@@")[1], body)

    def repl(m: re.Match[str]) -> str:
        target, _, alias = m.group(1).partition("|")
        target = target.strip()
        if target in titles:
            return f"[[{target}|{alias or titles[target]}]]"
        return alias or target

    fixed = re.sub(r"\[\[([^\]]+)\]\]", repl, protected)
    return re.sub(r"@@FENCE_(\d+)@@", lambda m: fences[int(m.group(1))], fixed)


def link_citations(body: str, source_url: str | None) -> str:
    """Turn `path:12-34` citations into links when a browsable source URL is configured."""
    if not source_url:
        return body
    base = source_url.rstrip("/")

    def repl(m: re.Match[str]) -> str:
        path, a, b = m.group(1), m.group(2), m.group(3) or m.group(2)
        return f"[{path}:{a}-{b}]({base}/{path}#L{a}-L{b})"

    return re.sub(r"`([\w./-]+\.\w+):(\d+)(?:-(\d+))?`", repl, body)


# ---------------------------------------------------------------------------- generation

def generate_page(
    page: dict[str, Any],
    outline: dict[str, Any],
    structure: dict[str, Any],
    doc_rag: WikiRAG | None = None,
    llm_client: LocalLLMClient | None = None,
) -> dict[str, Any]:
    doc_hits = query_docs_for_page(page, structure, doc_rag)
    det_body = synthesize_body(page, outline, structure, doc_hits=doc_hits)
    generator = "deterministic-deepwiki-v1.9"

    if llm_client and llm_client.enabled:
        prompt = (
            f"# Target Page: `{page['id']}` — {page['title']}\n\n"
            f"Below is the grounded 3-Source Context & Draft for `{page['title']}`. "
            f"Expand and refine it into an authoritative DeepWiki v1.9.9.5 specification page while preserving all "
            f"exact `[file:start-end]()` citations, `<details><summary>Relevant source files</summary>`, and valid Mermaid diagrams:\n\n"
            f"{det_body}"
        )
        llm_out = llm_client.complete(PAGE_SYSTEM_PROMPT, prompt)
        if llm_out and "```mermaid" in llm_out and "Sources:" in llm_out:
            # Strip leading H1 if the LLM included one (`write_wiki` adds `# Title`)
            llm_out = re.sub(r"^#\s+[^\n]+\n+", "", llm_out.strip())
            det_body = fix_wikilinks(llm_out, outline)
            generator = f"llm:{llm_client.model}"

    doc_refs = [
        {"id": h["id"], "title": h["title"], "path": h["path"], "score": h["score"], "via": h["via"]}
        for h in doc_hits
    ]
    return {
        "id": page["id"],
        "body": det_body,
        "diagram": "",
        "doc_refs": doc_refs,
        "generator": generator,
    }


def generate_overview(
    outline: dict[str, Any],
    structure: dict[str, Any],
    doc_rag: WikiRAG | None = None,
    llm_client: LocalLLMClient | None = None,
) -> dict[str, Any]:
    ov_id = outline["pages"][0]["id"] if outline.get("pages") else "1-overview"
    body = synthesize_overview(outline, structure, doc_rag=doc_rag)
    generator = "deterministic-deepwiki-v1.9"
    if llm_client and llm_client.enabled:
        prompt = (
            f"# Target Overview Page: `{ov_id}` — {outline.get('title', 'Overview')}\n\n"
            f"Refine and expand this grounded Overview draft into an authoritative DeepWiki v1.9.9.5 Overview page:\n\n{body}"
        )
        llm_out = llm_client.complete(PAGE_SYSTEM_PROMPT, prompt)
        if llm_out and "```mermaid" in llm_out:
            llm_out = re.sub(r"^#\s+[^\n]+\n+", "", llm_out.strip())
            body = fix_wikilinks(llm_out, outline)
            generator = f"llm:{llm_client.model}"
    return {
        "id": ov_id,
        "body": body,
        "diagram": "",
        "generator": generator,
    }


def generate_all(
    outline: dict[str, Any],
    structure: dict[str, Any],
    workers: int = 4,
    only: set[str] | None = None,
    existing: dict[str, dict[str, Any]] | None = None,
    doc_rag: WikiRAG | None = None,
    llm_client: LocalLLMClient | None = None,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = dict(existing or {})
    ov_ids = {"overview", "1-overview"}
    todo = [p for p in outline["pages"] if p["id"] not in ov_ids and (only is None or p["id"] in only)]
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for res in pool.map(lambda p: generate_page(p, outline, structure, doc_rag, llm_client), todo):
            results[res["id"]] = res
            print(f"[pages] {res['id']} ({res['generator']})")
    ov_id = next((p["id"] for p in outline["pages"] if p["id"] in ov_ids), "1-overview")
    if only is None or ov_id in only or todo:
        results[ov_id] = generate_overview(outline, structure, doc_rag=doc_rag, llm_client=llm_client)
        print(f"[pages] {ov_id} ({results[ov_id]['generator']})")
    return results
