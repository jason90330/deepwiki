"""Step 2a — plan the 2-level DeepWiki outline from `structure.json`.

Input: `structure.json`
Output: `outline.json`
  {"title": str, "pages": [{"id", "section_id", "title", "parent", "summary", "communities", "files", "related"}]}
The outline is validated against the structure: unknown files are dropped, every
non-test code file is covered by at least one page, and ids are unique slugs.
"""
from __future__ import annotations

import json
import re
from typing import Any


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.U)
    s = re.sub(r"[\s_/]+", "-", s).strip("-")
    return s or "page"


def _classify_group(label: str, is_test: bool) -> tuple[str, str]:
    l = label.lower()
    if is_test or "test" in l:
        return ("dev", "Development & Testing")
    if any(k in l for k in ("backend", "neon", "cl", "reference", "tosa", "ethos")):
        return ("backends", "Compute Backends")
    if any(k in l for k in ("delegate", "parser", "serializer", "deserializer", "ingest")):
        return ("frontends", "Model Support & Parsers")
    if any(k in l for k in ("profiling", "sample", "cli", "tool", "serve")):
        return ("tools", "Tools, Serving & Profiling")
    if any(k in l for k in ("cmake", "script", "build")):
        return ("dev", "Development & Testing")
    return ("core", "Core Architecture")


def fallback_outline(structure: dict[str, Any]) -> dict[str, Any]:
    pages: list[dict[str, Any]] = [{
        "id": "1-overview", "section_id": "1", "title": "1. Overview", "parent": None,
        "summary": "Architecture overview: subsystems, entry points and how they depend on each other.",
        "communities": [c["id"] for c in structure["communities"]], "files": [], "related": [],
    }]
    groups: dict[str, tuple[str, list[dict[str, Any]]]] = {}
    for c in structure["communities"]:
        gkey, gtitle = _classify_group(c["label"], bool(c.get("is_test")))
        groups.setdefault(gkey, (gtitle, []))[1].append(c)

    used: set[str] = {"1-overview"}
    sec_num = 2
    for _gkey, (gtitle, comms) in groups.items():
        if len(comms) == 1:
            c = comms[0]
            pid = f"{sec_num}-{slugify(c['label'].replace('/', ' '))}"
            used.add(pid)
            pages.append({
                "id": pid, "section_id": str(sec_num), "title": f"{sec_num}. {c['label']}",
                "parent": None, "summary": f"Subsystem `{c['label']}` ({len(c['files'])} files).",
                "communities": [c["id"]], "files": list(c["files"]), "related": [],
            })
        else:
            parent_id = f"{sec_num}-{slugify(gtitle)}"
            used.add(parent_id)
            pages.append({
                "id": parent_id, "section_id": str(sec_num), "title": f"{sec_num}. {gtitle}",
                "parent": None,
                "summary": f"{gtitle} across {sum(len(c['files']) for c in comms)} files.",
                "communities": [c["id"] for c in comms],
                "files": [f for c in comms for f in c["files"][:5]], "related": [],
            })
            for sub_idx, c in enumerate(comms, 1):
                sub_sec = f"{sec_num}.{sub_idx}"
                base = f"{sub_sec}-{slugify(c['label'].replace('/', ' '))}"
                pid, n = base, 2
                while pid in used:
                    pid, n = f"{base}-{n}", n + 1
                used.add(pid)
                pages.append({
                    "id": pid, "section_id": sub_sec, "title": f"{sub_sec} {c['label']}",
                    "parent": parent_id, "summary": f"Subsystem `{c['label']}` ({len(c['files'])} files).",
                    "communities": [c["id"]], "files": list(c["files"]), "related": [parent_id],
                })
        sec_num += 1
    _link_related_by_deps(structure, pages)
    return {"title": f"{structure['project']} wiki", "pages": pages}


def _link_related_by_deps(structure: dict[str, Any], pages: list[dict[str, Any]]) -> None:
    by_comm: dict[int, list[str]] = {}
    for p in pages:
        if p["id"] in ("overview", "1-overview"):
            continue
        for cid in p["communities"]:
            by_comm.setdefault(cid, []).append(p["id"])
    for a, b, _w in structure["community_edges"]:
        for pa in by_comm.get(a, []):
            for pb in by_comm.get(b, []):
                for src, dst in ((pa, pb), (pb, pa)):
                    page = next(p for p in pages if p["id"] == src)
                    if dst not in page["related"] and dst != src:
                        page["related"].append(dst)


def validate_outline(outline: dict[str, Any], structure: dict[str, Any]) -> dict[str, Any]:
    known_files = set(structure["files"])
    comm_ids = {c["id"] for c in structure["communities"]}
    pages_in = outline.get("pages") or []
    pages: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in pages_in:
        if not isinstance(raw, dict) or not raw.get("title"):
            continue
        pid = slugify(str(raw.get("id") or raw["title"]))
        base, n = pid, 2
        while pid in seen:
            pid, n = f"{base}-{n}", n + 1
        seen.add(pid)
        comms = [c for c in raw.get("communities") or [] if isinstance(c, int) and c in comm_ids]
        files = [f for f in raw.get("files") or [] if f in known_files]
        pages.append({
            "id": pid,
            "section_id": raw.get("section_id"),
            "title": str(raw["title"]),
            "parent": raw.get("parent"),
            "summary": str(raw.get("summary", "")),
            "communities": comms,
            "files": files,
            "related": [slugify(str(r)) for r in raw.get("related") or []],
        })
    if not pages or pages[0]["id"] not in ("overview", "1-overview"):
        pages.insert(0, fallback_outline(structure)["pages"][0])
        seen.add(pages[0]["id"])
    ids = {p["id"] for p in pages}
    for p in pages:
        if p["parent"] is not None:
            p["parent"] = slugify(str(p["parent"]))
            if p["parent"] not in ids or p["parent"] == p["id"]:
                p["parent"] = None
        p["related"] = [r for r in dict.fromkeys(p["related"]) if r in ids and r != p["id"]]
        if not p["files"] and p["communities"] and p["id"] not in ("overview", "1-overview"):
            p["files"] = sorted({f for c in structure["communities"] if c["id"] in p["communities"]
                                 for f in c["files"]})
    covered = {f for p in pages for f in p["files"]}
    for f, meta in structure["files"].items():
        if f in covered or meta["community"] is None or meta["is_test"] or not meta["symbols"]:
            continue
        owner = next((p for p in pages[1:] if meta["community"] in p["communities"]), None)
        if owner is None:
            owner = {
                "id": f"misc-{meta['community']}",
                "title": f"Other: {f.split('/')[0]}",
                "parent": None,
                "summary": "Files not assigned by the planner.",
                "communities": [meta["community"]],
                "files": [],
                "related": [],
            }
            pages.append(owner)
        owner["files"].append(f)
    return {"title": str(outline.get("title") or f"{structure['project']} wiki"), "pages": pages}


def plan_outline(structure: dict[str, Any]) -> dict[str, Any]:
    outline = fallback_outline(structure)
    result = validate_outline(outline, structure)
    result["planner"] = "deterministic-2level"
    return result


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)
