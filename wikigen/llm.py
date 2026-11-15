"""Optional OpenAI-Compatible Local LLM Client (`deepseek-v4-flash-0731` / vLLM / SGLang / Ollama).

Contains the reverse-engineered `deepwiki.com` (v1.9.9.5) system prompts for:
  1. Repository Outline Planning (`OUTLINE_SYSTEM_PROMPT`)
  2. Technical Page Synthesis (`PAGE_SYSTEM_PROMPT`)

Can be used either:
  - Automatically via `deepwiki_cli.py build --llm-base-url http://127.0.0.1:8000/v1 --llm-model deepseek-v4-flash-0731`
  - Directly by an Agent (`deepseek v4 flash 0731`) following `.agents/skills/deepwiki-generator/SKILL.md`
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

OUTLINE_SYSTEM_PROMPT = """You are the DeepWiki Architecture Planner (v1.9.9.5).
Given a 3-Source Repository Dossier combining:
  1. `git` repository tree, build files, and entry points
  2. `codebase-memory-mcp` (CBM) symbol centrality, classes, and call-graph hubs
  3. `llm-wiki` (`raw/`) official documentation titles and domain vocabulary

Design a comprehensive 2-level (or 3-level) DeepWiki `outline.json` following the Canonical DeepWiki Taxonomy:
  - `1`: Overview (`1.1` Getting Started, `1.2` High-Level API / Workflow)
  - `2`: Build System and Infrastructure (`2.1` CMake/Build Targets, `2.2` Codegen/Selective Build, `2.3` Schema/Serialization, `2.4` Language Bindings)
  - `3..N-1`: Core Compiler/IR, Optimization/Quantization, Pluggable Backends (consolidating minor ones into `Other Backends`), Model/Application Extensions, Testing/CI, Runtime Execution, and Mobile/Platform Extensions
  - `N`: Glossary (always the final chapter, mapping domain acronyms and formats to Code Entities)

Never use generic folder-dump titles like `Additional Modules` or `Vendor Demos`.
Return valid JSON matching `{"title": "<Repo> DeepWiki", "pages": [{"id", "section_id", "title", "parent", "summary", "files", "related"}]}`."""

PAGE_SYSTEM_PROMPT = """You are the DeepWiki Technical Author (v1.9.9.5).
Write an authoritative, code-grounded DeepWiki page in GitHub-Flavored Markdown from the provided 3-Source Context Packet (`git` source excerpts + `CBM` symbol/call graph + `llm-wiki` official docs).

Strict DeepWiki v1.9.9.5 Formatting Rules:
1. Begin immediately after `# <Title>` with `<details><summary>Relevant source files</summary>` listing the context files as `- [path/to/file](path/to/file)`.
2. Include `## Purpose and Scope` defining what the page covers, its primary classes/functions, and cross-page links (`[[page-id|Page Title]]`).
3. Structure the body into numbered `## 1. ...`, `## 2. ...` sections separated by `---`.
4. Every technical claim MUST include an inline file and line-range citation in the exact format `[path/to/file.ext:start-end]()`.
5. End every `##` section with a `Sources: [path/to/file.ext:start-end](), ...` line.
6. Include 2 to 4 Mermaid diagrams per page using ```mermaid fences:
   - A `Natural Language Space` to `Code Entity Space` mapping diagram (`graph TD` or `graph LR` with `subgraph "Natural Language Space"` and `subgraph "Code Entity Space"`).
   - A Pipeline / Execution Data Flow diagram (`graph TD`, `flowchart TD`, or `sequenceDiagram`) using real function/method names.
   - A `classDiagram` showing real class fields, methods, and inheritance/composition relationships.
   - Always quote node labels containing parentheses, colons, or paths: `NodeId["ClassName<br/>path/to/file.py"]`.
7. Include structured Markdown comparison tables (`Component | Code Entity | Purpose / Location`) and concise grounded code blocks where appropriate."""


class LocalLLMClient:
    """Zero-dependency OpenAI-compatible `/v1/chat/completions` client for local LLMs (e.g. `deepseek-v4-flash-0731`)."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: int = 180,
    ) -> None:
        self.base_url = (base_url or os.environ.get("WIKIGEN_LLM_BASE_URL") or "").rstrip("/")
        self.model = model or os.environ.get("WIKIGEN_LLM_MODEL") or "deepseek-v4-flash-0731"
        self.api_key = api_key or os.environ.get("WIKIGEN_LLM_API_KEY") or "EMPTY"
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, max_tokens: int = 4096) -> str | None:
        if not self.enabled:
            return None
        url = self.base_url if self.base_url.endswith("/chat/completions") else f"{self.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices") or []
                if choices:
                    content = (choices[0].get("message") or {}).get("content") or ""
                    # Strip optional <think>...</think> blocks from reasoning models
                    import re
                    content = re.sub(r"<think>[\s\S]*?</think>\s*", "", content).strip()
                    return content
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
            return None
        return None
