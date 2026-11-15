"""Write the generated wiki in llm-wiki layout (`wiki/*.md`, `index.md`, `log.md`)."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import yaml

from .pages import fix_wikilinks, link_citations


def _frontmatter(meta: dict[str, Any]) -> str:
    return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip() + "\n---\n"


def render_page(
    page: dict[str, Any],
    gen: dict[str, Any],
    outline: dict[str, Any],
    structure: dict[str, Any],
    source_url: str | None,
) -> str:
    titles = {p["id"]: p["title"] for p in outline["pages"]}
    children = [p for p in outline["pages"] if p.get("parent") == page["id"]]
    meta = {
        "id": page["id"],
        "title": page["title"],
        "parent": page.get("parent"),
        "type": "overview" if page["id"] in ("overview", "1-overview") else "code-subsystem",
        "sources": page["files"],
        "communities": page["communities"],
        "commit": structure.get("commit", ""),
        "generator": gen.get("generator", "deterministic"),
        "generated_at": structure.get("generated_at"),
    }
    body = link_citations(fix_wikilinks(gen["body"], outline), source_url)
    parts = [_frontmatter(meta), f"# {page['title']}\n"]
    if page.get("parent"):
        parts.append(f"↑ [[{page['parent']}|{titles.get(page['parent'], page['parent'])}]]\n")
    if page.get("summary"):
        parts.append(f"> {page['summary']}\n")
    parts.append(body.strip() + "\n")
    if gen.get("diagram"):
        parts.append("## Dependency diagram\n\n" + gen["diagram"] + "\n")
    if children:
        parts.append("## Sub-pages\n\n" + "\n".join(f"- [[{c['id']}|{c['title']}]]" for c in children) + "\n")
    if page.get("related"):
        parts.append(
            "## Related pages\n\n"
            + "\n".join(f"- [[{r}|{titles.get(r, r)}]]" for r in page["related"])
            + "\n"
        )
    if gen.get("doc_refs"):
        parts.append(
            "## Related documents\n\n"
            + "\n".join(
                f"- `{d['path']}` — {d['title']} (score {d['score']}, via {d['via']})"
                for d in gen["doc_refs"]
            )
            + "\n"
        )
    if page["files"]:
        def src(f: str) -> str:
            return f"- [`{f}`]({source_url.rstrip('/')}/{f})" if source_url else f"- `{f}`"
        parts.append("## Sources\n\n" + "\n".join(src(f) for f in page["files"]) + "\n")
    return "\n".join(parts)


def render_index(outline: dict[str, Any], structure: dict[str, Any]) -> str:
    children: dict[str | None, list[dict[str, Any]]] = {}
    for p in outline["pages"]:
        children.setdefault(p.get("parent"), []).append(p)
    lines = [
        f"# {outline['title']}",
        "",
        f"Generated from `{structure['project']}` at commit `{structure.get('commit', '')[:12]}` "
        f"({structure.get('generated_at')}).",
        "",
        "## Pages",
        "",
    ]

    def walk(parent: str | None, depth: int) -> None:
        for p in children.get(parent, []):
            lines.append(f"{'  ' * depth}- [[{p['id']}|{p['title']}]] — {p['summary']}")
            walk(p["id"], depth + 1)

    walk(None, 0)
    return "\n".join(lines) + "\n"


def write_wiki(
    out: Path,
    outline: dict[str, Any],
    structure: dict[str, Any],
    generated: dict[str, dict[str, Any]],
    source_url: str | None = None,
) -> list[Path]:
    wiki = out / "wiki"
    wiki.mkdir(parents=True, exist_ok=True)
    written = []
    for page in outline["pages"]:
        gen = generated.get(page["id"])
        if not gen:
            continue
        path = wiki / f"{page['id']}.md"
        path.write_text(render_page(page, gen, outline, structure, source_url), encoding="utf-8")
        written.append(path)
    (wiki / "index.md").write_text(render_index(outline, structure), encoding="utf-8")
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    gens = sorted({g.get("generator", "?") for g in generated.values()})
    with (wiki / "log.md").open("a", encoding="utf-8") as log:
        log.write(
            f"## [{stamp}] generate | {len(written)} pages from {structure['project']}"
            f"@{structure.get('commit', '')[:12]} via {', '.join(gens)}\n\n"
        )
    return written
