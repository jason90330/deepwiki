"""Step 4 — DeepWiki-style web server for generated wiki + graph.json + llm-wiki."""
from __future__ import annotations

import json
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .wiki_rag import FRONTMATTER_RE, WikiRAG

STATIC_INDEX = Path(__file__).parent / "static" / "index.html"


def _strip_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    import yaml
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1))
        return (meta if isinstance(meta, dict) else {}), text[m.end():]
    except yaml.YAMLError:
        return {}, text[m.end():]


def build_catalog(out_dir: Path, doc_wiki: Path | None) -> dict[str, Any]:
    wiki_dir = out_dir / "wiki" if (out_dir / "wiki").is_dir() else out_dir
    outline_path = (out_dir / "outline.json") if (out_dir / "outline.json").exists() else (wiki_dir / "outline.json")
    struct_path = out_dir / "structure.json"
    if not struct_path.exists():
        raw_structs = list((out_dir / "raw").glob("*/structure.json")) if (out_dir / "raw").is_dir() else []
        if raw_structs:
            struct_path = raw_structs[0]
    outline = json.loads(outline_path.read_text(encoding="utf-8")) if outline_path.exists() else {"title": out_dir.name, "pages": []}
    struct = json.loads(struct_path.read_text(encoding="utf-8")) if struct_path.exists() else {}
    llm_pages: list[dict[str, Any]] = []
    if doc_wiki and (doc_wiki / "wiki").is_dir() and doc_wiki.resolve() != out_dir.resolve():
        for p in sorted((doc_wiki / "wiki").glob("*.md")):
            if p.name in ("index.md", "log.md"):
                continue
            meta, body = _strip_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            heading = re.search(r"^#\s+(.+)$", body, flags=re.M)
            llm_pages.append({
                "id": f"llm:{p.stem}",
                "slug": p.stem,
                "title": str(meta.get("title") or (heading.group(1) if heading else p.stem)),
                "parent": f"llm:{meta['parent']}" if meta.get("parent") else None,
                "order": int(meta.get("order", 999)),
                "type": meta.get("type", "wiki"),
                "source_url": meta.get("source_url"),
            })
        llm_pages.sort(key=lambda x: (x["order"], x["title"]))
    return {
        "title": outline.get("title", out_dir.name),
        "project": struct.get("project", out_dir.name),
        "commit": struct.get("commit", ""),
        "generated_at": struct.get("generated_at", ""),
        "pages": outline.get("pages", []),
        "llm_pages": llm_pages,
    }


def serve_wiki(out_dir: Path, doc_wiki: Path | None = None, host: str = "127.0.0.1", port: int = 8765) -> None:
    out_dir = out_dir.resolve()
    doc_wiki = doc_wiki.resolve() if doc_wiki else None
    code_rag = WikiRAG(out_dir, include_raw=False)
    doc_rag = WikiRAG(doc_wiki, include_raw=True) if doc_wiki else None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            pass

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj: Any, code: int = 200) -> None:
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)

            if path == "/" or path == "/index.html":
                self._send(200, STATIC_INDEX.read_bytes(), "text/html; charset=utf-8")
                return
            if path == "/api/catalog":
                self._json(build_catalog(out_dir, doc_wiki))
                return
            if path == "/api/graph":
                gp = (out_dir / "graph.json") if (out_dir / "graph.json").exists() else (out_dir / "wiki" / "graph.json")
                self._send(200, gp.read_bytes() if gp.exists() else b'{"nodes":[],"edges":[]}',
                           "application/json; charset=utf-8")
                return
            if path.startswith("/api/page/"):
                pid = path[len("/api/page/"):]
                md_path = None
                if pid.startswith("llm:") and doc_wiki:
                    cand = (doc_wiki / "wiki" / f"{pid[4:]}.md").resolve()
                    if cand.is_file() and str(cand).startswith(str(doc_wiki)):
                        md_path = cand
                else:
                    cand = (out_dir / "wiki" / f"{pid}.md").resolve()
                    if cand.is_file() and str(cand).startswith(str(out_dir)):
                        md_path = cand
                    elif doc_wiki:
                        cand2 = (doc_wiki / "wiki" / f"{pid}.md").resolve()
                        if cand2.is_file() and str(cand2).startswith(str(doc_wiki)):
                            md_path = cand2
                if md_path is None:
                    self._json({"error": "not found"}, 404)
                    return
                meta, body = _strip_frontmatter(md_path.read_text(encoding="utf-8", errors="replace"))
                self._json({"id": pid, "meta": meta, "markdown": body})
                return
            if path in ("/api/search", "/api/ask"):
                q = (qs.get("q") or [""])[0].strip()
                if not q:
                    self._json({"hits": []})
                    return
                hits: list[dict[str, Any]] = []
                if doc_rag:
                    hits += [{"scope": "llm-wiki", **h} for h in doc_rag.query(q, top_k=5, expand_links=True)]
                hits += [{"scope": "code-wiki", **h} for h in code_rag.query(q, top_k=4, expand_links=False)]
                hits.sort(key=lambda x: -x["score"])
                self._json({"query": q, "hits": hits[:10]})
                return
            self._send(HTTPStatus.NOT_FOUND, b"Not found", "text/plain")

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"[serve] DeepWiki viewer running at http://{host}:{port} (out={out_dir})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
