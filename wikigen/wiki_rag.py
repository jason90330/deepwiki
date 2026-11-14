"""Lightweight RAG adapter over an `llm-wiki` directory (Karpathy's llm-wiki pattern).

Provides a temporary, zero-infrastructure document retrieval interface (no Qdrant/vLLM
needed) by indexing `wiki/*.md` (and optionally `raw/*.md|txt`) with BM25 scoring plus
1-hop `[[wikilink]]` expansion.

Returns hits in the same dict shape we expect from a Qdrant/hybrid RAG backend so the
rest of `wikigen` can swap between `WikiRAG` and a real RAG server seamlessly.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def tokenize(text: str) -> list[str]:
    """Split identifiers (camelCase/snake_case), words, and CJK bigrams."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    ascii_tokens = re.findall(r"[a-z0-9_]+", s.lower())
    out: list[str] = []
    for tok in ascii_tokens:
        parts = [p for p in tok.split("_") if p]
        out.extend(parts)
        if len(parts) > 1:
            out.append(tok)
    for seq in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(seq) == 1:
            out.append(seq)
        else:
            out.extend(seq[i:i + 2] for i in range(len(seq) - 1))
    return out


def parse_markdown_doc(path: Path, root: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    meta: dict[str, Any] = {}
    body = raw
    m = FRONTMATTER_RE.match(raw)
    if m:
        try:
            loaded = yaml.safe_load(m.group(1))
            if isinstance(loaded, dict):
                meta = loaded
        except yaml.YAMLError:
            pass
        body = raw[m.end():]
    headings = [h.strip() for h in re.findall(r"^#{1,3}\s+(.+)$", body, flags=re.M)]
    title = str(meta.get("title") or (headings[0] if headings else path.stem))
    body_no_code = re.sub(r"```.*?```", "", body, flags=re.S)
    links = list(dict.fromkeys(
        l.strip() for l in WIKILINK_RE.findall(body_no_code)
        if l.strip() and not l.strip().startswith('"')
    ))
    rel = str(path.relative_to(root))
    doc_id = str(meta.get("id") or path.stem)
    return {
        "id": doc_id,
        "title": title,
        "path": rel,
        "meta": meta,
        "headings": headings,
        "links": links,
        "text": body.strip(),
    }


@dataclass
class _BM25Index:
    docs: list[dict[str, Any]]
    tf: list[Counter[str]]
    df: Counter[str]
    avgdl: float

    @classmethod
    def build(cls, docs: list[dict[str, Any]]) -> "_BM25Index":
        tf: list[Counter[str]] = []
        df: Counter[str] = Counter()
        total_len = 0
        for d in docs:
            # Weight title and headings higher than body text.
            weighted = f"{d['title']} {d['title']} {' '.join(d['headings'])} {d['text']}"
            toks = tokenize(weighted)
            c = Counter(toks)
            tf.append(c)
            total_len += sum(c.values())
            for term in c:
                df[term] += 1
        avgdl = total_len / max(len(docs), 1)
        return cls(docs=docs, tf=tf, df=df, avgdl=avgdl)

    def score(self, query: str, k1: float = 1.5, b: float = 0.75) -> list[tuple[int, float]]:
        q_toks = tokenize(query)
        n = len(self.docs)
        if not q_toks or n == 0:
            return []
        scores: list[tuple[int, float]] = []
        for idx, c in enumerate(self.tf):
            dl = sum(c.values()) or 1
            s = 0.0
            for t in q_toks:
                f = c.get(t, 0)
                if not f:
                    continue
                df = self.df[t]
                idf = math.log(1.0 + (n - df + 0.5) / (df + 0.5))
                s += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / self.avgdl))
            if s > 0:
                scores.append((idx, s))
        scores.sort(key=lambda x: -x[1])
        return scores


class WikiRAG:
    """Query interface over an llm-wiki directory (`wiki/` and optional `raw/`)."""

    def __init__(self, wiki_dir: Path, include_raw: bool = True) -> None:
        self.root = Path(wiki_dir).resolve()
        self.docs: list[dict[str, Any]] = []
        self.by_id: dict[str, int] = {}

        search_dirs = [self.root / "wiki"] if (self.root / "wiki").is_dir() else [self.root]
        if include_raw and (self.root / "raw").is_dir():
            search_dirs.append(self.root / "raw")

        for d in search_dirs:
            for p in sorted(list(d.rglob("*.md")) + list(d.rglob("*.dox"))):
                if p.name in ("log.md", "AGENTS.md", "CLAUDE.md"):
                    continue
                doc = parse_markdown_doc(p, self.root)
                self.by_id[doc["id"]] = len(self.docs)
                self.docs.append(doc)
        self._index = _BM25Index.build(self.docs)

    def query(self, text: str, top_k: int = 5, expand_links: bool = True,
              snippet_chars: int = 1200) -> list[dict[str, Any]]:
        ranked = self._index.score(text)
        hits: list[dict[str, Any]] = []
        seen: set[int] = set()
        for idx, sc in ranked[:top_k]:
            seen.add(idx)
            d = self.docs[idx]
            hits.append({
                "id": d["id"],
                "title": d["title"],
                "path": d["path"],
                "headings": d["headings"],
                "links": d["links"],
                "score": round(sc, 4),
                "via": "bm25",
                "snippet": d["text"][:snippet_chars],
            })
        if expand_links and hits:
            # Pull 1-hop [[wikilink]] neighbours of the top 2 hits as supporting context.
            for h in hits[:2]:
                for target in h["links"]:
                    nidx = self.by_id.get(target)
                    if nidx is not None and nidx not in seen and len(hits) < top_k + 3:
                        seen.add(nidx)
                        nd = self.docs[nidx]
                        hits.append({
                            "id": nd["id"],
                            "title": nd["title"],
                            "path": nd["path"],
                            "headings": nd["headings"],
                            "links": nd["links"],
                            "score": round(h["score"] * 0.5, 4),
                            "via": f"wikilink:{h['id']}",
                            "snippet": nd["text"][:snippet_chars],
                        })
        return hits

    def lint(self) -> dict[str, Any]:
        """Basic llm-wiki health check: broken [[wikilinks]] and orphan pages."""
        known = set(self.by_id)
        inbound: Counter[str] = Counter()
        broken: list[dict[str, str]] = []
        for d in self.docs:
            for target in d["links"]:
                if target in known:
                    inbound[target] += 1
                else:
                    broken.append({"from": d["id"], "missing_target": target})
        orphans = [d["id"] for d in self.docs
                   if d["id"] not in ("index", "overview") and not d["path"].startswith("raw/")
                   and inbound[d["id"]] == 0]
        return {"doc_count": len(self.docs), "broken_links": broken, "orphans": orphans}
