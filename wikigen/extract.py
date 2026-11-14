"""Step 1 — structure extraction (deterministic, no LLM).

Pulls the code graph from codebase-memory-mcp, folds symbol-level edges into a weighted
file-level graph, and runs Louvain community detection to find subsystems. The result,
`structure.json`, is the skeleton the wiki outline is planned from.
"""
from __future__ import annotations

import datetime as dt
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

import networkx as nx

from .cbm import CBMClient

SYMBOL_LABELS = ("Class", "Function", "Method")
# Edge type -> weight when folded to the file level.
EDGE_WEIGHTS = {"CALLS": 1.0, "IMPORTS": 2.0, "INHERITS": 3.0}
SIBLING_WEIGHT = 0.3          # weak affinity between files in the same directory
SIBLING_DIR_MAX = 30          # skip sibling edges in very wide directories
MIN_COMMUNITY_FILES = 2


def clean_doc(raw: str | None) -> str:
    """CBM stores docstrings with escaped quotes/newlines; return plain text."""
    if not raw:
        return ""
    s = raw.replace("\\\\n", "\n").replace("\\n", "\n")
    s = re.sub(r"\\+\"", '"', s).replace("\\'", "'")
    s = s.strip().strip("\"'").strip()
    return re.sub(r"\n\s+", "\n", s)


def clean_sig(raw: str | None) -> str:
    if not raw:
        return ""
    s = raw.replace("\\\\n", " ").replace("\\n", " ")
    return re.sub(r"\s+", " ", s).strip()


def is_test_path(path: str) -> bool:
    p = PurePosixPath(path)
    return any(part in ("tests", "test", "__tests__") for part in p.parts[:-1]) or \
        p.name.startswith("test_") or p.stem.endswith("_test")


def _int(v: Any) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def git_commit(repo: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def fetch_graph(client: CBMClient) -> dict[str, Any]:
    symbols: dict[str, dict[str, Any]] = {}
    for label in SYMBOL_LABELS:
        rows = client.query(
            f"MATCH (s:{label}) RETURN s.qualified_name, s.name, s.file_path, s.start_line, "
            f"s.end_line, s.signature, s.docstring")
        for r in rows:
            qn, fp = r["s.qualified_name"], r["s.file_path"]
            if not qn or not fp:
                continue
            symbols[qn] = {
                "name": r["s.name"], "label": label, "file": fp,
                "start": _int(r["s.start_line"]), "end": _int(r["s.end_line"]),
                "signature": clean_sig(r["s.signature"]), "doc": clean_doc(r["s.docstring"]),
            }
    edges: list[tuple[str, str, str, str, str]] = []  # (type, src_qn, src_file, dst_qn, dst_file)
    for etype in EDGE_WEIGHTS:
        rows = client.query(
            f"MATCH (a)-[:{etype}]->(b) RETURN a.qualified_name, a.file_path, "
            f"b.qualified_name, b.file_path")
        for r in rows:
            if r["a.file_path"] and r["b.file_path"]:
                edges.append((etype, r["a.qualified_name"], r["a.file_path"],
                              r["b.qualified_name"], r["b.file_path"]))
    files = sorted({r["f.file_path"] for r in client.query("MATCH (f:File) RETURN f.file_path")
                    if r["f.file_path"] and not r["f.file_path"].startswith("<")})
    file_set = set(files)
    symbols = {qn: s for qn, s in symbols.items() if s["file"] in file_set}
    arch = client.call("get_architecture", aspects=["languages", "entry_points", "routes"])
    return {"symbols": symbols, "edges": edges, "files": files, "arch": arch}


def _rows(table: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not table:
        return []
    return [dict(zip(table.get("cols", []), r)) for r in table.get("rows", [])]


def build_structure(raw: dict[str, Any], *, project: str, repo_root: Path) -> dict[str, Any]:
    symbols: dict[str, dict[str, Any]] = raw["symbols"]
    code_files = sorted({s["file"] for s in symbols.values()})
    all_files = sorted(set(raw["files"]) | set(code_files))

    # Symbol fan-in/out over project-internal CALLS.
    fan_in: Counter[str] = Counter()
    fan_out: Counter[str] = Counter()
    file_w: dict[tuple[str, str], float] = defaultdict(float)
    for etype, sq, sf, dq, df in raw["edges"]:
        if etype == "CALLS" and dq in symbols and sq in symbols and sq != dq:
            fan_in[dq] += 1
            fan_out[sq] += 1
        if sf != df and sf in code_files and df in code_files:
            key = tuple(sorted((sf, df)))
            file_w[key] += EDGE_WEIGHTS[etype]  # type: ignore[index]
    for qn, s in symbols.items():
        s["fan_in"], s["fan_out"] = fan_in[qn], fan_out[qn]

    prod_files = [f for f in code_files if not is_test_path(f)]
    test_files = [f for f in code_files if is_test_path(f)]

    g = nx.Graph()
    g.add_nodes_from(prod_files)
    for (a, b), w in file_w.items():
        if a in g and b in g:
            g.add_edge(a, b, weight=w)
    by_dir: dict[str, list[str]] = defaultdict(list)
    for f in prod_files:
        by_dir[str(PurePosixPath(f).parent)].append(f)
    for sib in by_dir.values():
        if 1 < len(sib) <= SIBLING_DIR_MAX:
            for i, a in enumerate(sib):
                for b in sib[i + 1:]:
                    prev = g.get_edge_data(a, b, {}).get("weight", 0.0)
                    g.add_edge(a, b, weight=prev + SIBLING_WEIGHT)

    comms = [set(c) for c in nx.community.louvain_communities(g, weight="weight", seed=42)] \
        if g.number_of_nodes() else []
    comms = _merge_small(g, comms)
    comms.sort(key=lambda c: (-len(c), sorted(c)[0]))

    file_comm: dict[str, int] = {f: i for i, c in enumerate(comms) for f in c}
    communities: list[dict[str, Any]] = []
    for i, members in enumerate(comms):
        communities.append(_summarize(i, sorted(members), symbols, g))
    if test_files:
        tid = len(communities)
        for f in test_files:
            file_comm[f] = tid
        communities.append({**_summarize(tid, test_files, symbols, g), "label": "tests", "is_test": True})

    comm_w: dict[tuple[int, int], float] = defaultdict(float)
    for (a, b), w in file_w.items():
        ca, cb = file_comm.get(a), file_comm.get(b)
        if ca is not None and cb is not None and ca != cb:
            comm_w[tuple(sorted((ca, cb)))] += w  # type: ignore[index]

    arch = raw.get("arch", {})
    return {
        "project": project,
        "repo_root": str(repo_root),
        "commit": git_commit(repo_root),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "languages": _rows(arch.get("languages")),
        "entry_points": _rows(arch.get("entry_points")),
        "routes": [r for r in _rows(arch.get("routes")) if r.get("method")],
        "files": {f: {"community": file_comm.get(f), "is_test": is_test_path(f),
                      "symbols": sorted(q for q, s in symbols.items() if s["file"] == f)}
                  for f in all_files},
        "symbols": symbols,
        "file_edges": [[a, b, round(w, 2)] for (a, b), w in sorted(file_w.items())],
        "communities": communities,
        "community_edges": [[a, b, round(w, 2)] for (a, b), w in sorted(comm_w.items())],
    }


def _merge_small(g: nx.Graph, comms: list[set[str]]) -> list[set[str]]:
    """Fold communities below MIN_COMMUNITY_FILES into their most strongly connected neighbour."""
    changed = True
    while changed and len(comms) > 1:
        changed = False
        for i, c in enumerate(comms):
            if len(c) >= MIN_COMMUNITY_FILES:
                continue
            best, best_w = None, 0.0
            for j, other in enumerate(comms):
                if j == i:
                    continue
                w = sum(g[a][b]["weight"] for a in c for b in g.neighbors(a) if b in other)
                if w > best_w:
                    best, best_w = j, w
            if best is not None:
                comms[best] |= c
                del comms[i]
                changed = True
                break
    return comms


def _common_prefix(files: list[str]) -> str:
    parts = [PurePosixPath(f).parent.parts for f in files]
    prefix: list[str] = []
    for level in zip(*parts):
        if len(set(level)) != 1:
            break
        prefix.append(level[0])
    return "/".join(prefix)


def _summarize(cid: int, files: list[str], symbols: dict[str, dict[str, Any]], g: nx.Graph) -> dict[str, Any]:
    members = [(q, s) for q, s in symbols.items() if s["file"] in set(files)]
    top = sorted(members, key=lambda qs: (-(qs[1]["fan_in"] + qs[1]["fan_out"]), qs[0]))[:12]
    dirs = Counter(str(PurePosixPath(f).parent) for f in files)
    top_dir, top_count = dirs.most_common(1)[0]
    prefix = _common_prefix(files)
    # Prefer the dominant directory when a shallow common prefix hides the real package (e.g. "rag" vs "rag/serve").
    label = top_dir if (top_count >= len(files) * 0.5 and top_dir not in ("", ".")) else (prefix or top_dir)
    if label in ("", "."):
        label = PurePosixPath(files[0]).stem if len(files) == 1 else "root"
    internal = sum(d["weight"] for a, b, d in g.subgraph(files).edges(data=True)) if g else 0.0
    return {
        "id": cid,
        "label": label,
        "files": files,
        "dirs": dict(dirs),
        "symbol_count": len(members),
        "top_symbols": [q for q, _ in top],
        "internal_weight": round(internal, 2),
        "is_test": False,
    }


def extract(client: CBMClient, repo_root: Path) -> dict[str, Any]:
    raw = fetch_graph(client)
    return build_structure(raw, project=client.project or "", repo_root=repo_root)
