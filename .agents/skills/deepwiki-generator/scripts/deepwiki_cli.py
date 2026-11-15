#!/usr/bin/env python3
"""DeepWiki Generator Skill CLI wrapper.

Provides subcommands (`build`, `packet`, `validate`, `query`, `lint`, `serve`) to
dynamically link an indexed `codebase-memory-mcp` project with an existing `llm-wiki`
or HTTP/Qdrant `rag` collection and generate/validate a complete DeepWiki.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Resolve repository root dynamically whether invoked from `.agents/skills/...` or global skills
_CANDIDATES = [
    Path(__file__).resolve().parents[4],
    Path(__file__).resolve().parents[1],
    Path("/home/jason/Project/deepwiki"),
]
for _cand in _CANDIDATES:
    if (_cand / "wikigen").is_dir() and str(_cand) not in sys.path:
        sys.path.insert(0, str(_cand))
        break

from wikigen.link import run_dynamic_pipeline, validate_deepwiki  # noqa: E402
from wikigen.serve import serve_wiki  # noqa: E402
from wikigen.wiki_rag import WikiRAG  # noqa: E402


def _write_output(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Success! Data written to: {path}")


def cmd_build(args: argparse.Namespace) -> None:
    res = run_dynamic_pipeline(
        project=args.project,
        out_dir=args.out_dir,
        repo=args.repo,
        llm_wiki_dir=args.llm_wiki,
        rag_url=args.rag_url,
        rag_collection=args.rag_collection,
        source_url=args.source_url,
        cbm_bin=args.cbm_bin,
        refresh_structure=args.refresh_structure,
        regenerate=args.regenerate,
        enrich_only=args.enrich_only,
        workers=args.workers,
        llm_base_url=args.llm_base_url,
        llm_model=args.llm_model,
    )
    _write_output(args.output, res)


def cmd_dossier(args: argparse.Namespace) -> None:
    wiki_dir = args.wiki_dir.resolve()
    dos = wiki_dir / "wiki" / ".packets" / "_repo_dossier.md"
    if not dos.exists():
        dos = wiki_dir / ".packets" / "_repo_dossier.md"
    if not dos.exists():
        raise FileNotFoundError("Repository dossier not found. Run `build` first.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(dos.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Success! 3-Source Repository Dossier written to: {args.output}")


def cmd_packet(args: argparse.Namespace) -> None:
    wiki_dir = args.wiki_dir.resolve()
    pkt = (wiki_dir / "wiki" / ".packets" / f"{args.page_id}.md")
    if not pkt.exists():
        pkt = wiki_dir / ".packets" / f"{args.page_id}.md"
    if not pkt.exists():
        raise FileNotFoundError(f"Packet not found for page_id={args.page_id}. Run `build` first.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(pkt.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Success! Page packet written to: {args.output}")


def cmd_validate(args: argparse.Namespace) -> None:
    res = validate_deepwiki(args.wiki_dir)
    _write_output(args.output, res)
    if not res.get("passed"):
        sys.exit(1)


def cmd_query(args: argparse.Namespace) -> None:
    rag = WikiRAG(args.wiki_dir)
    hits = rag.query(args.query, top_k=args.limit)
    _write_output(
        args.output,
        {"wiki_dir": str(args.wiki_dir), "query": args.query, "docs_indexed": len(rag.docs), "hits": hits},
    )


def cmd_lint(args: argparse.Namespace) -> None:
    rag = WikiRAG(args.wiki_dir)
    _write_output(args.output, rag.lint())


def cmd_serve(args: argparse.Namespace) -> None:
    serve_wiki(args.wiki_dir, doc_wiki=args.doc_wiki, host=args.host, port=args.port)


def main() -> None:
    ap = argparse.ArgumentParser(prog="deepwiki_cli", description="Dynamic DeepWiki Knowledge Linker & Generator")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="Link CBM index + llm-wiki/RAG collection and generate DeepWiki")
    b.add_argument("--project", required=True, help="Indexed codebase-memory-mcp project name")
    b.add_argument("--out-dir", type=Path, required=True, help="Target llm-wiki / DeepWiki directory")
    b.add_argument("--repo", type=Path, help="Optional repository path (auto-inferred from --project if omitted)")
    b.add_argument("--llm-wiki", type=Path, help="Existing llm-wiki collection path")
    b.add_argument("--rag-url", help="Optional HTTP/Qdrant RAG base URL (e.g. http://127.0.0.1:8005)")
    b.add_argument("--rag-collection", default="default", help="RAG collection name")
    b.add_argument("--source-url", help="Browsable repository source URL for citations")
    b.add_argument("--cbm-bin", help="Path to codebase-memory-mcp binary")
    b.add_argument("--refresh-structure", action="store_true", help="Re-extract structure.json from CBM")
    b.add_argument("--regenerate", action="store_true", help="Re-plan outline.json and regenerate all wiki/*.md pages")
    b.add_argument("--enrich-only", action="store_true", help="Only update dynamic links in existing wiki/*.md")
    b.add_argument("--workers", type=int, default=4, help="Parallel worker count")
    b.add_argument("--llm-base-url", help="Optional OpenAI-compatible local LLM URL (e.g. http://127.0.0.1:8000/v1)")
    b.add_argument("--llm-model", help="Optional local LLM model name (default: deepseek-v4-flash-0731)")
    b.add_argument("--output", type=Path, required=True, help="Output JSON summary file path")
    b.set_defaults(func=cmd_build)

    ds = sub.add_parser("dossier", help="Export the 3-source (git + CBM + llm-wiki) repository architecture dossier")
    ds.add_argument("--wiki-dir", type=Path, required=True, help="Path to llm-wiki directory")
    ds.add_argument("--output", type=Path, required=True, help="Output markdown file path")
    ds.set_defaults(func=cmd_dossier)

    pk = sub.add_parser("packet", help="Export a compact (<8 KB) context packet for one page (for LLM authoring)")
    pk.add_argument("--wiki-dir", type=Path, required=True, help="Path to llm-wiki directory")
    pk.add_argument("--page-id", required=True, help="Page ID from outline.json (e.g. 2.1-exir-edge-dialect)")
    pk.add_argument("--output", type=Path, required=True, help="Output markdown file path")
    pk.set_defaults(func=cmd_packet)

    vl = sub.add_parser("validate", help="Run full DeepWiki quality & link-health validation gates")
    vl.add_argument("--wiki-dir", type=Path, required=True, help="Path to llm-wiki directory")
    vl.add_argument("--output", type=Path, required=True, help="Output JSON validation report path")
    vl.set_defaults(func=cmd_validate)

    q = sub.add_parser("query", help="Query the linked llm-wiki collection (BM25 + 1-hop [[wikilink]])")
    q.add_argument("--wiki-dir", type=Path, required=True, help="Path to llm-wiki directory")
    q.add_argument("--query", required=True, help="Search query")
    q.add_argument("--limit", type=int, required=True, help="Maximum hits to return")
    q.add_argument("--output", type=Path, required=True, help="Output JSON file path")
    q.set_defaults(func=cmd_query)

    lt = sub.add_parser("lint", help="Check broken [[wikilinks]] and orphan pages")
    lt.add_argument("--wiki-dir", type=Path, required=True, help="Path to llm-wiki directory")
    lt.add_argument("--output", type=Path, required=True, help="Output JSON report path")
    lt.set_defaults(func=cmd_lint)

    sv = sub.add_parser("serve", help="Start the DeepWiki 3-column interactive web viewer")
    sv.add_argument("--wiki-dir", type=Path, required=True, help="Path to llm-wiki directory")
    sv.add_argument("--doc-wiki", type=Path, help="Optional secondary llm-wiki directory")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8765)
    sv.set_defaults(func=cmd_serve)

    args = ap.parse_args()
    try:
        args.func(args)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
