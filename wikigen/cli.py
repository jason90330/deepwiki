"""wikigen CLI.

  python -m wikigen link -p <cbm-project> -o <llm-wiki-dir>   # dynamic knowledge linker + DeepWiki builder
  python -m wikigen wiki-query <llm-wiki-dir> -q "<query>"    # BM25 + 1-hop [[wikilink]] RAG query
  python -m wikigen wiki-lint  <llm-wiki-dir>                 # verify broken links & orphans
  python -m wikigen serve      <llm-wiki-dir> --port 8765     # start 3-column DeepWiki web viewer
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .cbm import CBMClient, find_binary
from .extract import extract
from .link import RAGCollectionAdapter, build_enriched_graph, discover_knowledge_links, run_dynamic_pipeline
from .pages import generate_all
from .plan import dumps, plan_outline
from .render import write_wiki
from .serve import serve_wiki
from .wiki_rag import WikiRAG


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(obj), encoding="utf-8")


def cmd_extract(args: argparse.Namespace) -> None:
    repo = Path(args.repo).resolve()
    client = CBMClient(find_binary(args.cbm_bin), project=args.project)
    if not args.no_index:
        res = client.index(repo)
        print(f"[extract] indexed {res.get('project')}: {res.get('nodes')} nodes, {res.get('edges')} edges")
    if not client.project:
        client.project = str(repo).strip("/").replace("/", "-")
    structure = extract(client, repo)
    _save(args.out / "structure.json", structure)
    comms = structure["communities"]
    print(f"[extract] {len(structure['symbols'])} symbols, {len(structure['file_edges'])} file edges, "
          f"{len(comms)} communities -> {args.out / 'structure.json'}")


def cmd_plan(args: argparse.Namespace) -> None:
    structure = _load(args.out / "structure.json")
    outline = plan_outline(structure)
    _save(args.out / "outline.json", outline)
    print(f"[plan] {len(outline['pages'])} pages via {outline['planner']} -> {args.out / 'outline.json'}")


def cmd_generate(args: argparse.Namespace) -> None:
    structure = _load(args.out / "structure.json")
    outline = _load(args.out / "outline.json")
    pages_path = args.out / "pages.json"
    existing = _load(pages_path) if (args.only and pages_path.exists()) else None
    only = set(args.only.split(",")) if args.only else None
    doc_rag = WikiRAG(args.doc_wiki) if args.doc_wiki else None
    generated = generate_all(outline, structure, workers=args.workers, only=only, existing=existing, doc_rag=doc_rag)
    _save(pages_path, generated)
    written = write_wiki(args.out, outline, structure, generated, source_url=args.source_url)
    collection = RAGCollectionAdapter(llm_wiki_dir=args.doc_wiki or args.out)
    links = discover_knowledge_links(structure, outline, collection)
    graph = build_enriched_graph(outline, structure, links)
    _save(args.out / "wiki" / "graph.json", graph)
    print(f"[generate] wrote {len(written)} pages -> {args.out / 'wiki'}; graph -> {args.out / 'wiki' / 'graph.json'}")


def cmd_all(args: argparse.Namespace) -> None:
    cmd_extract(args)
    cmd_plan(args)
    cmd_generate(args)


def cmd_wiki_query(args: argparse.Namespace) -> None:
    rag = WikiRAG(args.wiki_dir)
    hits = rag.query(args.query, top_k=args.top_k)
    if args.json:
        print(dumps({"query": args.query, "docs_indexed": len(rag.docs), "hits": hits}))
        return
    print(f"[wiki-query] {len(hits)} hits (from {len(rag.docs)} docs in {args.wiki_dir}):")
    for h in hits:
        print(f"  - [{h['score']}] {h['title']} ({h['path']}, via {h['via']})")
        print(f"    {h['snippet'][:180].replace(chr(10), ' ')}")


def cmd_wiki_lint(args: argparse.Namespace) -> None:
    rag = WikiRAG(args.wiki_dir)
    print(dumps(rag.lint()))


def cmd_serve(args: argparse.Namespace) -> None:
    serve_wiki(args.out_dir, doc_wiki=args.doc_wiki, host=args.host, port=args.port)


def cmd_link(args: argparse.Namespace) -> None:
    res = run_dynamic_pipeline(
        project=args.project,
        out_dir=args.out,
        repo=args.repo,
        llm_wiki_dir=args.llm_wiki,
        rag_url=args.rag_url,
        rag_collection=args.rag_collection,
        source_url=args.source_url,
        cbm_bin=args.cbm_bin,
        refresh_structure=args.refresh_structure,
        enrich_only=args.enrich_only,
        workers=args.workers,
    )
    if args.output_file:
        _save(args.output_file, res)
    print(f"[link] Success! Mode={res['mode']}, pages={res['pages_updated']}, "
          f"symbol_mentions={res['link_stats']['total_symbol_mentions']}, "
          f"graph=({res['graph_nodes']} nodes, {res['graph_edges']} edges) -> {res['out_dir']}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="wikigen", description="DeepWiki generator & dynamic knowledge linker")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p: argparse.ArgumentParser, repo: bool = False) -> None:
        if repo:
            p.add_argument("repo", help="path to the repository")
            p.add_argument("--project", help="existing CBM project name (default: derived on index)")
            p.add_argument("--no-index", action="store_true", help="reuse the existing CBM index")
            p.add_argument("--cbm-bin", help="path to codebase-memory-mcp")
        p.add_argument("-o", "--out", type=Path, required=True, help="output directory")
        p.add_argument("--workers", type=int, default=4, help="parallel page generations")
        p.add_argument("--only", help="comma-separated page ids to (re)generate")
        p.add_argument("--source-url", help="browsable source base URL for citation links")
        p.add_argument("--doc-wiki", type=Path, help="path to an llm-wiki workspace")

    common(e := sub.add_parser("extract", help="step 1: structure extraction"), repo=True)
    e.set_defaults(func=cmd_extract)
    common(p := sub.add_parser("plan", help="step 2a: outline planning"))
    p.set_defaults(func=cmd_plan)
    common(g := sub.add_parser("generate", help="step 2b: page generation + render"))
    g.set_defaults(func=cmd_generate)
    common(a := sub.add_parser("all", help="extract + plan + generate"), repo=True)
    a.set_defaults(func=cmd_all)

    wq = sub.add_parser("wiki-query", help="query an llm-wiki directory via BM25 + 1-hop [[wikilink]]")
    wq.add_argument("wiki_dir", type=Path, help="path to llm-wiki workspace (contains wiki/ and raw/)")
    wq.add_argument("-q", "--query", required=True, help="search query")
    wq.add_argument("-k", "--top-k", type=int, default=5, help="number of hits")
    wq.add_argument("--json", action="store_true", help="output JSON")
    wq.set_defaults(func=cmd_wiki_query)

    wl = sub.add_parser("wiki-lint", help="health-check [[wikilinks]] and orphans in an llm-wiki")
    wl.add_argument("wiki_dir", type=Path, help="path to llm-wiki workspace")
    wl.set_defaults(func=cmd_wiki_lint)

    sv = sub.add_parser("serve", help="start DeepWiki-style web viewer for llm-wiki")
    sv.add_argument("out_dir", type=Path, help="llm-wiki directory")
    sv.add_argument("--doc-wiki", type=Path, help="optional secondary llm-wiki workspace")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8765)
    sv.set_defaults(func=cmd_serve)

    for sub_name in ("link", "build"):
        lk = sub.add_parser(sub_name, help="dynamically link an indexed CBM project + llm-wiki/RAG collection -> DeepWiki")
        lk.add_argument("-p", "--project", required=True, help="existing codebase-memory-mcp project name")
        lk.add_argument("-o", "--out", type=Path, required=True, help="target DeepWiki / llm-wiki output directory")
        lk.add_argument("--repo", type=Path, help="local repo path (auto-inferred from --project if omitted)")
        lk.add_argument("--llm-wiki", type=Path, help="path to existing llm-wiki collection (defaults to --out)")
        lk.add_argument("--rag-url", help="optional HTTP/Qdrant RAG server URL (e.g. http://127.0.0.1:8005 or :6333)")
        lk.add_argument("--rag-collection", default="default", help="RAG collection name when --rag-url is used")
        lk.add_argument("--source-url", help="browsable source base URL for citation links")
        lk.add_argument("--cbm-bin", help="path to codebase-memory-mcp binary")
        lk.add_argument("--refresh-structure", action="store_true", help="re-extract structure.json from CBM index")
        lk.add_argument("--enrich-only", action="store_true", help="only inject dynamic knowledge links into existing wiki/*.md")
        lk.add_argument("--workers", type=int, default=4, help="parallel page workers")
        lk.add_argument("--output-file", type=Path, help="optional JSON summary file path")
        lk.set_defaults(func=cmd_link)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
