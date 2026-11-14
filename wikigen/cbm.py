"""Thin client over the codebase-memory-mcp CLI (`codebase-memory-mcp cli <tool> ...`).

Every MCP tool is also exposed as a one-shot CLI command; we pass arguments as one JSON
object on stdin and request machine-readable JSON output.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_BINARIES = (
    "codebase-memory-mcp",
    str(Path.home() / ".local/opt/cbm/codebase-memory-mcp"),
    str(Path.home() / ".local/bin/codebase-memory-mcp"),
)


class CBMError(RuntimeError):
    pass


def find_binary(explicit: str | None = None) -> str:
    candidates = [explicit] if explicit else [os.environ.get("CBM_BIN")] + list(DEFAULT_BINARIES)
    for cand in candidates:
        if not cand:
            continue
        path = shutil.which(cand) or (cand if Path(cand).is_file() else None)
        if path:
            return path
    raise CBMError("codebase-memory-mcp binary not found; set CBM_BIN or pass --cbm-bin")


@dataclass
class CBMClient:
    binary: str
    project: str | None = None
    timeout: int = 900

    def call(self, tool: str, **args: Any) -> dict[str, Any]:
        if self.project and "project" not in args and tool not in ("index_repository", "list_projects"):
            args["project"] = self.project
        args.setdefault("format", "json")
        proc = subprocess.run(
            [self.binary, "cli", "--quiet", tool],
            input=json.dumps(args), capture_output=True, text=True, timeout=self.timeout,
        )
        out = proc.stdout.strip()
        if proc.returncode != 0 or not out:
            raise CBMError(f"{tool} failed (rc={proc.returncode}): {proc.stderr.strip()[-800:]}")
        try:
            return json.loads(out)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise CBMError(f"{tool} returned non-JSON output: {out[:300]}") from exc

    def index(self, repo_path: str | Path) -> dict[str, Any]:
        res = self.call("index_repository", repo_path=str(Path(repo_path).resolve()))
        self.project = res.get("project", self.project)
        return res

    def query(self, cypher: str, max_rows: int = 99998, max_output_tokens: int = 500000) -> list[dict[str, Any]]:
        """Run a read-only Cypher query and return rows as dicts keyed by column name.

        Follows snapshot cursors so results above max_rows are not silently dropped.
        """
        rows: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            args: dict[str, Any] = {"query": cypher, "max_rows": max_rows,
                                    "max_output_tokens": max_output_tokens}
            if cursor:
                args["cursor"] = cursor
            res = self.call("query_graph", **args)
            cols = res.get("columns", [])
            rows.extend(dict(zip(cols, r)) for r in res.get("rows", []))
            cursor = res.get("next_cursor") or res.get("cursor")
            if not res.get("has_more") or not cursor:
                return rows
