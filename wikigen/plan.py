"""Step 2a — 3-Source (`git` + `CBM` + `llm-wiki`) Canonical DeepWiki Outline Planner & Dossier Generator.

Reverse-engineered from `deepwiki.com` (v1.9.9.5):
Instead of naive folder dumping, combines:
  1. `git` repository tree, build files (`CMakeLists.txt`, `BUCK`, `targets.bzl`, `pyproject.toml`), and entry points
  2. `CBM` (`codebase-memory-mcp`) symbol centrality (`fan_in`/`fan_out`), classes, and call-graph hubs
  3. `llm-wiki` (`raw/`) official documentation titles, headings, and domain vocabulary

Produces:
  - `outline.json`: DeepWiki Canonical Lifecycle Outline (Overview -> Build/Infra -> Compiler/IR ->
    Quantization/Optimization -> Backends/Providers -> Models/Extensions -> Testing/CI ->
    Runtime Execution -> Platform Extensions -> Glossary)
  - `wiki/.packets/_repo_dossier.md`: Compact 3-source architectural dossier for LLM outline steering
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

ACRONYMS = {
    "ir": "IR", "exir": "EXIR", "api": "API", "apis": "APIs", "cli": "CLI", "sdk": "SDK",
    "nn": "NN", "armnn": "ArmNN", "cpu": "CPU", "gpu": "GPU", "npu": "NPU", "dsp": "DSP",
    "cl": "OpenCL", "opencl": "OpenCL", "tosa": "TOSA", "vgf": "VGF", "xnnpack": "XNNPACK",
    "mps": "MPS", "coreml": "CoreML", "qnn": "Qualcomm QNN", "qualcomm": "Qualcomm QNN",
    "vulkan": "Vulkan", "openvino": "OpenVINO", "tensorrt": "TensorRT", "cuda": "CUDA",
    "aten": "ATen", "ao": "TorchAO", "llm": "LLM", "rag": "RAG", "etdump": "ETDump",
    "etrecord": "ETRecord", "pte": "PTE", "onnx": "ONNX", "tflite": "TFLite",
    "tf": "TensorFlow", "hal": "HAL", "jni": "JNI", "objc": "Objective-C",
    "wasm": "WebAssembly", "zephyr": "Zephyr", "nxp": "NXP", "mlx": "Apple MLX",
    "aoti": "AOTI", "webgpu": "WebGPU", "cmsis": "CMSIS-NN", "ethos": "Ethos-U",
    "cadence": "Cadence DSP", "mediatek": "MediaTek", "samsung": "Samsung Exynos",
}


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s.-]", "", text.lower(), flags=re.U)
    s = re.sub(r"[\s_/]+", "-", s).strip("-")
    return s or "page"


def humanize_label(raw_label: str) -> str:
    """Convert a module path or identifier into a clean DeepWiki title."""
    cleaned = raw_label.strip("/").lstrip(".")
    parts = [
        p.lstrip("_") for p in re.split(r"[/\\-]+", cleaned)
        if p.lstrip("_") and p.lower() not in ("src", "include", "lib", "internal", "detail")
    ]
    if not parts:
        parts = [cleaned or "Core"]
    dedup: list[str] = []
    for p in parts:
        if not dedup or dedup[-1].lower() != p.lower():
            dedup.append(p)
    words: list[str] = []
    for w in dedup[:3]:
        low = w.lower()
        if low in ACRONYMS:
            words.append(ACRONYMS[low])
        else:
            words.append(w.replace("_", " ").title())
    return " ".join(words)


def scan_git_files(repo_root: Path | None, structure: dict[str, Any]) -> list[str]:
    """Combine CBM-indexed files with `git ls-files` (capturing CMake, Buck, YAML, scripts, docs)."""
    cbm_files = set((structure.get("files") or {}).keys())
    if repo_root and (repo_root / ".git").exists():
        try:
            out = subprocess.check_output(
                ["git", "-C", str(repo_root), "ls-files"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
            git_files = [
                line.strip() for line in out.splitlines()
                if line.strip() and not line.startswith("third-party/") and not line.startswith("third_party/")
            ]
            return sorted(cbm_files.union(git_files))
        except Exception:
            pass
    return sorted(cbm_files)


def _is_test_or_demo_path(fl: str) -> bool:
    return any(
        tok in fl
        for tok in (
            "/test/", "/tests/", "/testing_util/", "/test_util/", "/test_suite/",
            "/tutorials_source/", "/test_", "_test.cpp", "_test.py", "_test.h",
            "androidtest", "/mock", "/fake",
        )
    )


def _match_files(all_files: list[str], prefixes: tuple[str, ...], keywords: tuple[str, ...] = (), exclude_tests: bool = False) -> list[str]:
    matched: list[str] = []
    seen: set[str] = set()
    for p in prefixes:
        pl = p.lower()
        for f in all_files:
            if f in seen:
                continue
            fl = f.lower()
            if exclude_tests and _is_test_or_demo_path(fl):
                continue
            if fl == pl or fl.startswith(pl):
                matched.append(f)
                seen.add(f)
    if keywords:
        for f in all_files:
            if f in seen:
                continue
            fl = f.lower()
            if exclude_tests and _is_test_or_demo_path(fl):
                continue
            if any(k in fl for k in keywords):
                matched.append(f)
                seen.add(f)
    return matched


def _score_files(files: list[str], structure: dict[str, Any], doc_files_mentioned: set[str]) -> int:
    """Compute architectural importance score from CBM non-test symbol centrality + doc mentions."""
    fmeta = structure.get("files") or {}
    syms = structure.get("symbols") or {}
    score = 0
    for f in files:
        meta = fmeta.get(f)
        if not meta:
            if f in doc_files_mentioned or f.endswith((".md", ".rst", "CMakeLists.txt", "targets.bzl")):
                score += 5
            continue
        if meta.get("is_test"):
            score += 1
            continue
        score += 4 + len(meta.get("symbols", []))
        for q in meta.get("symbols", [])[:15]:
            s = syms.get(q)
            if s:
                score += min(30, s.get("fan_in", 0) * 2 + s.get("fan_out", 0))
        if f in doc_files_mentioned:
            score += 25
    return score


def _communities_for_files(files: list[str], structure: dict[str, Any]) -> list[int]:
    fmeta = structure.get("files") or {}
    cids = {
        fmeta[f]["community"]
        for f in files
        if f in fmeta and fmeta[f].get("community") is not None
    }
    return sorted(cids)


def _prioritize_files(files: list[str], structure: dict[str, Any], limit: int = 45) -> list[str]:
    """Rank non-test implementation files, build files, docs, and key test files for a page."""
    fmeta = structure.get("files") or {}
    syms = structure.get("symbols") or {}
    dedup_files = list(dict.fromkeys(files))
    order_idx = {f: i for i, f in enumerate(dedup_files)}

    def _rank(f: str) -> tuple[int, int, int, str]:
        fl = f.lower()
        depth = len(PurePosixPath(f).parts)
        is_doc = fl.startswith("docs/") or fl.endswith(".md") or fl.endswith(".rst")
        is_test = bool((fmeta.get(f) or {}).get("is_test")) or _is_test_or_demo_path(fl)
        is_compat_shim = "headeronly/" in fl or "/c10/" in fl or "/generated/" in fl
        is_build = fl.endswith(("cmakelists.txt", "targets.bzl", "buck", "pyproject.toml", "setup.py", ".cmake", ".fbs"))
        sym_list = (fmeta.get(f) or {}).get("symbols") or []
        centrality = sum(syms.get(q, {}).get("fan_in", 0) * 2 + syms.get(q, {}).get("fan_out", 0) for q in sym_list[:15])
        has_class = any(syms.get(q, {}).get("label") in ("Class", "Struct", "Interface") for q in sym_list)
        class_bonus = 60 if has_class else 0
        util_penalty = 35 if ("/util/" in fl or "_util." in fl or "types.h" in fl) else 0
        order_penalty = min(order_idx.get(f, 0) * 3, 180)
        if not is_test and not is_doc and not is_compat_shim and (sym_list or f.endswith((".h", ".hpp", ".cpp", ".py"))):
            tier = 0
        elif is_doc:
            tier = 1
        elif is_build:
            tier = 2
        elif is_compat_shim and not is_test:
            tier = 3
        elif is_test:
            tier = 4
        else:
            tier = 5
        depth_penalty = max(0, depth - 3) * 25
        return (tier, -(centrality + class_bonus + min(len(sym_list), 20) * 2 - depth_penalty - util_penalty - order_penalty), depth, f)

    ranked = sorted(dedup_files, key=_rank)
    impl = [f for f in ranked if _rank(f)[0] == 0][: max(16, limit - 12)]
    docs = [f for f in ranked if _rank(f)[0] == 1][:6]
    build_files = [f for f in ranked if _rank(f)[0] == 2 and not _is_test_or_demo_path(f.lower())][:6]
    non_test = list(dict.fromkeys(impl + docs + build_files))
    if len(impl) >= 4:
        return non_test[:limit]
    combined = list(dict.fromkeys(non_test + ranked))
    return combined[:limit]


def _build_executorch_canonical_outline(
    all_files: list[str],
    structure: dict[str, Any],
) -> dict[str, Any]:
    """Canonical DeepWiki v1.9.9.5 outline when repository matches PyTorch ExecuTorch."""
    spec: list[tuple[str, str, str | None, str, list[str]]] = [
        (
            "1-overview", "1", None, "Overview",
            _match_files(all_files, ("README.md", "CONTRIBUTING.md", "docs/source/overview.md", "docs/source/intro-", "docs/source/getting-started", "exir/program/_program.py", "runtime/executor/program.h", "runtime/executor/method.h", "extension/module/module.h")),
        ),
        (
            "1.1-getting-started", "1.1", "1-overview", "Getting Started",
            _match_files(all_files, ("install_executorch.py", "install_requirements.py", "docs/source/getting-started", "docs/source/using-executorch", "examples/portable/")),
        ),
        (
            "1.2-export-api-and-recipe-system", "1.2", "1-overview", "Export API and Recipe System",
            _match_files(all_files, ("export/", "docs/source/export-", "exir/program/_program.py", "devtools/bundled_program/")),
        ),
        (
            "2-build-system-and-infrastructure", "2", None, "Build System and Infrastructure",
            _match_files(all_files, ("CMakeLists.txt", "tools/cmake/", "codegen/", "schema/", "extension/pybindings/", "shim_et/", "pyproject.toml", "setup.py")),
        ),
        (
            "2.1-cmake-configuration-and-targets", "2.1", "2-build-system-and-infrastructure", "CMake Configuration and Targets",
            _match_files(all_files, ("CMakeLists.txt", "tools/cmake/", "docs/source/building-from-source.md", "docs/source/using-executorch-building-from-source.md")),
        ),
        (
            "2.2-kernel-libraries-and-selective-build", "2.2", "2-build-system-and-infrastructure", "Kernel Libraries and Selective Build",
            _match_files(all_files, ("codegen/tools/", "codegen/templates/", "codegen/gen.py", "codegen/parse.py", "codegen/model.py", "examples/selective_build/", "docs/source/kernel-library-selective-build.md")),
        ),
        (
            "2.3-schema-generation-and-flatbuffers", "2.3", "2-build-system-and-infrastructure", "Schema Generation and FlatBuffers",
            _match_files(all_files, ("schema/", "exir/_serialize/", "exir/schema.py", "extension/flat_tensor/", "devtools/etdump/")),
        ),
        (
            "2.4-python-bindings-and-dependencies", "2.4", "2-build-system-and-infrastructure", "Python Bindings and Dependencies",
            _match_files(all_files, ("extension/pybindings/", "pyproject.toml", "setup.py", "install_requirements.py", "install_executorch.py", ".lintrunner.toml", "docs/source/runtime-python-api-reference.rst")),
        ),
        (
            "2.5-buck2-and-shim-build-layer", "2.5", "2-build-system-and-infrastructure", "Buck2 and Shim Build Layer",
            _match_files(all_files, ("shim_et/", ".ci/scripts/unittest-buck2.sh", "runtime/core/portable_type/c10/", "codegen/targets.bzl")),
        ),
        (
            "3-exir-core-system", "3", None, "EXIR Core System",
            _match_files(all_files, ("exir/program/", "exir/passes/", "exir/emit/", "exir/verification/", "exir/dialects/", "exir/capture/", "exir/memory_planning.py", "docs/source/ir-exir.md", "docs/source/compiler-")),
        ),
        (
            "3.1-program-structure-and-compilation-flow", "3.1", "3-exir-core-system", "Program Structure and Compilation Flow",
            _match_files(all_files, ("exir/program/", "exir/capture/", "exir/lowered_backend_module.py", "exir/tracer.py", "docs/source/ir-exir.md")),
        ),
        (
            "3.2-graph-transformation-pass-system", "3.2", "3-exir-core-system", "Graph Transformation Pass System",
            _match_files(all_files, ("exir/passes/", "exir/pass_base.py", "exir/pass_manager.py", "docs/source/compiler-custom-compiler-passes.md")),
        ),
        (
            "3.3-memory-planning-and-allocation", "3.3", "3-exir-core-system", "Memory Planning and Allocation",
            _match_files(all_files, ("exir/memory_planning.py", "exir/passes/memory_planning_pass.py", "exir/passes/sym_shape_eval_pass.py", "exir/tensor.py", "docs/source/compiler-memory-planning.md")),
        ),
        (
            "3.4-program-emission-and-serialization", "3.4", "3-exir-core-system", "Program Emission and Serialization",
            _match_files(all_files, ("exir/emit/", "exir/_serialize/", "exir/schema.py", "extension/flat_tensor/")),
        ),
        (
            "3.5-verification-and-dialect-system", "3.5", "3-exir-core-system", "Verification and Dialect System",
            _match_files(all_files, ("exir/verification/", "exir/dialects/", "exir/operator/", "docs/source/ir-exir.md")),
        ),
        (
            "4-quantization-systems", "4", None, "Quantization Systems",
            _match_files(all_files, ("kernels/quantized/", "exir/passes/quant", "backends/xnnpack/quantizer/", "backends/arm/quantizer/", "backends/qualcomm/quantizer/", "backends/apple/coreml/quantizer/", "docs/source/quantization-")),
        ),
        (
            "4.1-quantization-framework-and-patterns", "4.1", "4-quantization-systems", "Quantization Framework and Patterns",
            _match_files(all_files, ("kernels/quantized/", "exir/passes/quant", "docs/source/quantization-overview.md", "backends/transforms/")),
        ),
        (
            "4.2-backend-specific-quantization", "4.2", "4-quantization-systems", "Backend-Specific Quantization",
            _match_files(all_files, ("backends/xnnpack/quantizer/", "backends/arm/quantizer/", "backends/qualcomm/quantizer/", "backends/apple/coreml/quantizer/", "backends/vulkan/quantizer/", "backends/cadence/aot/quantizer/")),
        ),
        (
            "5-backend-delegation-architecture", "5", None, "Backend Delegation Architecture",
            _match_files(all_files, ("exir/backend/", "runtime/backend/", "docs/source/backends-overview.md", "docs/source/compiler-delegate-and-partitioner.md", "backends/xnnpack/", "backends/vulkan/", "backends/qualcomm/", "backends/arm/", "backends/apple/")),
        ),
        (
            "5.1-partitioning-and-operator-support", "5.1", "5-backend-delegation-architecture", "Partitioning and Operator Support",
            _match_files(all_files, ("exir/backend/", "docs/source/compiler-delegate-and-partitioner.md", "docs/source/backends-overview.md")),
        ),
        (
            "5.2-vulkan-gpu-backend", "5.2", "5-backend-delegation-architecture", "Vulkan GPU Backend",
            _match_files(all_files, ("backends/vulkan/", "docs/source/backends/vulkan/"), exclude_tests=True),
        ),
        (
            "5.3-qualcomm-qnn-backend", "5.3", "5-backend-delegation-architecture", "Qualcomm QNN Backend",
            _match_files(all_files, ("backends/qualcomm/", "docs/source/backends-qualcomm.md", "examples/qualcomm/"), exclude_tests=True),
        ),
        (
            "5.4-arm-tosa-and-ethos-u-backend", "5.4", "5-backend-delegation-architecture", "ARM TOSA and Ethos-U Backend",
            _match_files(all_files, ("backends/arm/", "docs/source/backends-arm-", "docs/source/backends/arm-", "examples/arm/"), exclude_tests=True),
        ),
        (
            "5.5-cadence-dsp-backend", "5.5", "5-backend-delegation-architecture", "Cadence DSP Backend",
            _match_files(all_files, ("backends/cadence/", "docs/source/backends-cadence.md", "examples/cadence/"), exclude_tests=True),
        ),
        (
            "5.6-xnnpack-cpu-backend", "5.6", "5-backend-delegation-architecture", "XNNPACK CPU Backend",
            _match_files(all_files, ("backends/xnnpack/", "docs/source/backends-xnnpack.md", "examples/xnnpack/"), exclude_tests=True),
        ),
        (
            "5.7-cuda-aoti-and-apple-metal-backends", "5.7", "5-backend-delegation-architecture", "CUDA / AOTI and Apple Metal Backends",
            _match_files(all_files, ("backends/cuda/", "backends/aoti/", "backends/apple/coreml/", "backends/apple/mps/", "backends/apple/metal/", "docs/source/backends/cuda/", "docs/source/backends-coreml.md", "docs/source/backends-mps.md"), exclude_tests=True),
        ),
        (
            "5.8-other-backends", "5.8", "5-backend-delegation-architecture", "Other Hardware Backends (OpenVINO, MediaTek, Samsung, NXP, MLX, TensorRT)",
            _match_files(all_files, ("backends/openvino/", "backends/mediatek/", "backends/samsung/", "backends/nxp/", "backends/mlx/", "backends/tensorrt/", "docs/source/backends/"), exclude_tests=True),
        ),
        (
            "6-model-export-and-llm-support", "6", None, "Model Export and LLM Support",
            _match_files(all_files, ("examples/models/", "extension/llm/", "docs/source/llm/")),
        ),
        (
            "6.1-llama-model-export", "6.1", "6-model-export-and-llm-support", "LLaMA and Generative Model Export",
            _match_files(all_files, ("examples/models/llama/", "examples/models/qwen", "examples/models/phi", "examples/models/gemma", "docs/source/llm/"), exclude_tests=True),
        ),
        (
            "6.2-llm-runner-framework", "6.2", "6-model-export-and-llm-support", "LLM Runner Framework",
            _match_files(all_files, ("extension/llm/runner/", "extension/llm/sampler/", "extension/llm/tokenizer", "extension/llm/modules/"), exclude_tests=True),
        ),
        (
            "6.3-custom-operators-and-extensions", "6.3", "6-model-export-and-llm-support", "Custom Operators and Extensions",
            _match_files(all_files, ("extension/llm/custom_ops/", "extension/custom_ops/", "kernels/aten/", "examples/portable/custom_ops/", "docs/source/kernel-library-custom-aten-kernel.md"), exclude_tests=True),
        ),
        (
            "6.4-multimodal-and-audio-models", "6.4", "6-model-export-and-llm-support", "Multimodal and Audio Models",
            _match_files(all_files, ("examples/models/llava/", "examples/models/whisper/", "examples/models/moshi/", "examples/models/voxtral/", "examples/models/parakeet/", "extension/audio/"), exclude_tests=True),
        ),
        (
            "7-testing-and-cicd-infrastructure", "7", None, "Testing and CI/CD Infrastructure",
            _match_files(all_files, (".github/workflows/", ".ci/", "examples/models/test", "backends/test_suite/", "devtools/etdump/", "profiler/")),
        ),
        (
            "7.1-cicd-workflows-and-validation", "7.1", "7-testing-and-cicd-infrastructure", "CI/CD Workflows and Validation",
            _match_files(all_files, (".github/workflows/", ".ci/scripts/", ".ci/docker/")),
        ),
        (
            "7.2-model-and-backend-testing-framework", "7.2", "7-testing-and-cicd-infrastructure", "Model and Backend Testing Framework",
            _match_files(all_files, ("backends/test_suite/", "examples/models/", "exir/tests/", "runtime/executor/test/")),
        ),
        (
            "7.3-performance-benchmarking-and-profiling", "7.3", "7-testing-and-cicd-infrastructure", "Performance Benchmarking and Profiling",
            _match_files(all_files, ("profiler/", "devtools/etdump/", "devtools/inspector/", "docs/source/devtools-", "docs/source/profiling")),
        ),
        (
            "8-runtime-execution", "8", None, "Runtime Execution",
            _match_files(all_files, ("runtime/executor/", "runtime/core/", "runtime/kernel/", "runtime/backend/", "runtime/platform/", "kernels/portable/", "kernels/optimized/", "devtools/")),
        ),
        (
            "8.1-core-runtime-architecture", "8.1", "8-runtime-execution", "Core Runtime Architecture",
            _match_files(all_files, ("runtime/executor/", "runtime/core/", "runtime/platform/", "extension/data_loader/", "extension/flat_tensor/", "docs/source/runtime-overview.md"), exclude_tests=True),
        ),
        (
            "8.2-kernel-registration-and-dispatch", "8.2", "8-runtime-execution", "Kernel Registration and Dispatch",
            _match_files(all_files, ("runtime/kernel/", "kernels/portable/", "kernels/optimized/", "kernels/prim_ops/", "docs/source/kernel-library-overview.md"), exclude_tests=True),
        ),
        (
            "8.3-developer-tools-devtools", "8.3", "8-runtime-execution", "Developer Tools (DevTools: ETDump, ETRecord, Inspector)",
            _match_files(all_files, ("devtools/etdump/", "devtools/etrecord/", "devtools/inspector/", "devtools/bundled_program/", "docs/source/devtools-", "docs/source/etdump.md", "docs/source/etrecord.md"), exclude_tests=True),
        ),
        (
            "9-mobile-and-platform-extensions", "9", None, "Mobile and Platform Extensions",
            _match_files(all_files, ("extension/android/", "extension/apple/", "extension/module/", "extension/tensor/", "extension/training/", "extension/wasm/", "backends/webgpu/", "examples/demo-apps/", "examples/arm/", "examples/espressif/", "examples/raspberry_pi/")),
        ),
        (
            "9.1-android-extension", "9.1", "9-mobile-and-platform-extensions", "Android Extension (Java/Kotlin & JNI)",
            _match_files(all_files, ("extension/android/", "examples/demo-apps/android/", "docs/source/using-executorch-android.md"), exclude_tests=True),
        ),
        (
            "9.2-apple-ios-macos-extension", "9.2", "9-mobile-and-platform-extensions", "Apple iOS/macOS Extension (Swift & Objective-C)",
            _match_files(all_files, ("extension/apple/", "examples/demo-apps/apple_ios/", "docs/source/using-executorch-ios.md"), exclude_tests=True),
        ),
        (
            "9.3-high-level-module-and-on-device-training", "9.3", "9-mobile-and-platform-extensions", "High-Level Module API, Tensor & On-Device Training",
            _match_files(all_files, ("extension/module/", "extension/tensor/", "extension/training/", "extension/runner_util/", "docs/source/using-executorch-cpp.md", "docs/source/training-overview.md"), exclude_tests=True),
        ),
        (
            "9.4-embedded-and-web-targets", "9.4", "9-mobile-and-platform-extensions", "Embedded (Zephyr, ESP32, Pico2) and WebAssembly/WebGPU Targets",
            _match_files(all_files, ("extension/wasm/", "backends/webgpu/", "examples/espressif/", "examples/raspberry_pi/", "examples/arm/", "docs/source/pico2_tutorial.md", "docs/source/backends/arm-cortex-m/"), exclude_tests=True),
        ),
        (
            "10-glossary", "10", None, "Glossary",
            _match_files(all_files, ("exir/program/_program.py", "exir/capture/_config.py", "runtime/executor/program.h", "runtime/executor/method.h", "runtime/core/evalue.h", "devtools/etdump/etdump_flatcc.h", "backends/vulkan/partitioner/vulkan_partitioner.py", "backends/arm/tosa/specification.py", "docs/source/overview.md", "docs/source/ir-exir.md", "docs/source/backends-overview.md")),
        ),
    ]

    pages: list[dict[str, Any]] = []
    for pid, sec_id, parent_id, title, raw_files in spec:
        pfiles = _prioritize_files(raw_files, structure, limit=40)
        cids = _communities_for_files(pfiles, structure)
        syms = [
            (structure.get("symbols") or {})[q]["name"]
            for f in pfiles[:12]
            for q in ((structure.get("files") or {}).get(f) or {}).get("symbols", [])[:4]
            if q in (structure.get("symbols") or {})
        ]
        uniq_syms = list(dict.fromkeys(syms))[:5]
        sym_note = f" Primary code entities: {', '.join(f'`{s}`' for s in uniq_syms)}." if uniq_syms else ""
        pages.append({
            "id": pid,
            "section_id": sec_id,
            "title": title,
            "parent": parent_id,
            "summary": f"Architectural specification and implementation reference for {title} ({len(pfiles)} relevant source files).{sym_note}",
            "communities": cids,
            "files": pfiles,
            "related": [parent_id] if parent_id else (["1-overview"] if pid != "1-overview" else []),
        })

    # Link parent pages to their direct children in `related`
    for p in pages:
        if p["parent"] is None:
            kids = [k["id"] for k in pages if k["parent"] == p["id"]]
            p["related"] = list(dict.fromkeys(p["related"] + kids))

    _link_related_by_deps(structure, pages)
    return {"title": "ExecuTorch DeepWiki", "pages": pages, "planner": "canonical-deepwiki-v1.9"}


def _module_key(path_str: str, is_test: bool) -> str:
    """Normalize a repo-relative file path to its architectural `<top1>/<top2>` module key."""
    if is_test:
        return "tests"
    p = PurePosixPath(path_str.strip("/"))
    dir_parts = [pt for pt in p.parent.parts if pt not in ("", ".")]
    if not dir_parts:
        return "core/root"
    top1 = dir_parts[0].lower()
    if top1 in (".ci", ".github", "scripts", "cmake", "tools", "shim_et", "website", "third-party", "third_party"):
        return "build/infrastructure"
    if top1 == "examples":
        if len(dir_parts) >= 2 and dir_parts[1].lower() in ("models", "llm_server", "portable"):
            return f"examples/{dir_parts[1].lower()}"
        return "examples/applications"
    if top1 in ("src", "include") and len(dir_parts) >= 3:
        return f"{dir_parts[1]}/{dir_parts[2]}"
    if len(dir_parts) >= 2:
        return f"{dir_parts[0]}/{dir_parts[1].lstrip('_')}"
    return dir_parts[0]


def _classify_group(mod_key: str, is_test: bool) -> tuple[str, str, int]:
    l = mod_key.lower()
    if l == "build/infrastructure":
        return ("build", "Build System and Infrastructure", 2)
    if is_test or l == "tests":
        return ("testing", "Testing, Validation and Profiling", 7)
    top1 = l.split("/")[0]
    if top1 in ("exir", "export", "codegen", "compiler", "ir", "schema", "optimizations"):
        return ("compiler", "Compiler, IR and Graph Lowering", 3)
    if top1 in ("quantization",) or "quant" in l:
        return ("quantization", "Quantization and Optimization Systems", 4)
    if top1 in ("backends", "delegates", "drivers") or any(
        k in l for k in ("backend", "neon", "opencl", "tosa", "xnnpack", "vulkan", "qualcomm", "coreml", "mps")
    ):
        return ("backends", "Backend Delegation and Hardware Providers", 5)
    if top1 in ("extension", "extensions", "parsers", "serializer", "deserializer", "bindings", "python") or l.startswith("examples/models"):
        return ("extensions", "Model Export, Extensions and Bindings", 6)
    if top1 in ("runtime", "core", "armnn", "arch", "mm", "sched", "kernels", "ops", "workloads"):
        return ("runtime", "Runtime Execution and Kernel Dispatch", 8)
    if top1 in ("devtools", "profiling", "examples", "tools", "serve", "ingest", "retrieve"):
        return ("platform", "Developer Tools and Platform Targets", 9)
    return ("runtime", "Runtime Execution and Kernel Dispatch", 8)


def _group_and_consolidate(
    structure: dict[str, Any],
    all_files: list[str],
    doc_files_mentioned: set[str],
) -> dict[str, tuple[int, str, list[dict[str, Any]]]]:
    """Group repository code files and rank subsystems using CBM centrality + llm-wiki doc coverage."""
    symbols = structure.get("symbols") or {}
    buckets: dict[str, dict[str, Any]] = {}
    for f, meta in (structure.get("files") or {}).items():
        if f.startswith("docs/") or not meta.get("symbols"):
            continue
        is_t = bool(meta.get("is_test")) or "androidtest" in f.lower()
        mkey = _module_key(f, is_t)
        cid = meta.get("community")
        if mkey not in buckets:
            buckets[mkey] = {
                "id": cid if cid is not None else 0,
                "label": mkey,
                "files": [f],
                "symbol_count": len(meta["symbols"]),
                "all_symbols": list(meta["symbols"]),
                "merged_ids": [cid] if cid is not None else [],
                "is_test": is_t,
            }
        else:
            b = buckets[mkey]
            b["files"].append(f)
            b["symbol_count"] += len(meta["symbols"])
            b["all_symbols"].extend(meta["symbols"])
            if cid is not None and cid not in b["merged_ids"]:
                b["merged_ids"].append(cid)

    for b in buckets.values():
        b["files"] = _prioritize_files(b["files"], structure, limit=40)
        ranked_syms = sorted(
            b.pop("all_symbols", []),
            key=lambda q: -(symbols.get(q, {}).get("fan_in", 0) * 2 + symbols.get(q, {}).get("fan_out", 0)),
        )
        b["top_symbols"] = ranked_syms[:12]
        b["arch_score"] = _score_files(b["files"], structure, doc_files_mentioned)

    groups: dict[str, tuple[int, str, list[dict[str, Any]]]] = {}
    for mkey, mod in buckets.items():
        gkey, gtitle, gorder = _classify_group(mkey, mod["is_test"])
        if gkey not in groups:
            groups[gkey] = (gorder, gtitle, [])
        groups[gkey][2].append(mod)

    final_groups: dict[str, tuple[int, str, list[dict[str, Any]]]] = {}
    max_per_group = 6
    for gkey, (gorder, gtitle, mods) in groups.items():
        mods.sort(key=lambda m: (m["is_test"], -m["arch_score"], m["label"]))
        if len(mods) > max_per_group:
            keep = mods[: max_per_group - 1]
            tail = mods[max_per_group - 1:]
            other_title = "Other Backends" if gkey == "backends" else f"Other {gtitle.split()[0]} Components"
            merged_tail = {
                "id": tail[0]["id"],
                "label": other_title,
                "files": _prioritize_files([f for m in tail for f in m["files"]], structure, limit=40),
                "symbol_count": sum(m["symbol_count"] for m in tail),
                "top_symbols": [s for m in tail for s in m["top_symbols"][:3]][:15],
                "merged_ids": sorted({cid for m in tail for cid in m["merged_ids"]}),
                "is_test": any(m["is_test"] for m in tail),
                "sub_labels": [humanize_label(m["label"]) for m in tail[:6]],
            }
            mods = keep + [merged_tail]
        final_groups[gkey] = (gorder, gtitle, mods)

    return final_groups


def fallback_outline(
    structure: dict[str, Any],
    repo_root: Path | None = None,
    doc_files_mentioned: set[str] | None = None,
) -> dict[str, Any]:
    all_files = scan_git_files(repo_root, structure)
    # Detect ExecuTorch or use generalized canonical 3-source planner
    if "exir/program/_program.py" in all_files and "runtime/executor/method.cpp" in all_files:
        return _build_executorch_canonical_outline(all_files, structure)

    project_title = humanize_label(structure.get("project", "Repository").split("-")[-1])
    comms_all = structure.get("communities") or []
    groups = _group_and_consolidate(structure, all_files, doc_files_mentioned or set())
    sorted_groups = sorted(groups.items(), key=lambda kv: (kv[1][0], kv[0]))

    overview_files = _prioritize_files(
        [f for _gk, (_go, _gt, mods) in sorted_groups for m in mods[:2] for f in m["files"][:3]],
        structure,
        limit=28,
    )

    pages: list[dict[str, Any]] = [{
        "id": "1-overview",
        "section_id": "1",
        "title": "Overview",
        "parent": None,
        "summary": (
            f"End-to-end architecture overview of {project_title}: core subsystems, "
            f"compilation/execution pipeline, entry points, and cross-module dependencies."
        ),
        "communities": [c["id"] for c in comms_all],
        "files": overview_files,
        "related": [],
    }]

    used: set[str] = {"1-overview"}
    sec_num = 2

    for _gkey, (_gorder, gtitle, mods) in sorted_groups:
        parent_id = f"{sec_num}-{slugify(gtitle)}"
        used.add(parent_id)
        all_cids = sorted({cid for m in mods for cid in m.get("merged_ids", [m["id"]])})
        total_files = sum(len(m["files"]) for m in mods)
        total_syms = sum(m.get("symbol_count", 0) for m in mods)
        pages.append({
            "id": parent_id,
            "section_id": str(sec_num),
            "title": gtitle,
            "parent": None,
            "summary": (
                f"Architectural overview of {gtitle}, spanning {total_files} source files "
                f"and {total_syms} code symbols across {len(mods)} subsystems."
            ),
            "communities": all_cids,
            "files": _prioritize_files([f for m in mods for f in m["files"][:6]], structure, limit=35),
            "related": ["1-overview"],
        })
        for sub_idx, m in enumerate(mods, 1):
            sub_sec = f"{sec_num}.{sub_idx}"
            htitle = m["label"] if m["label"].startswith("Other ") else humanize_label(m["label"])
            base = f"{sub_sec}-{slugify(htitle)}"
            pid, n = base, 2
            while pid in used:
                pid, n = f"{base}-{n}", n + 1
            used.add(pid)
            cids = m.get("merged_ids", [m["id"]])
            top_sym_names = [q.split(".")[-1].split("::")[-1] for q in m.get("top_symbols", [])[:4]]
            sym_desc = f" Key symbols include {', '.join(f'`{s}`' for s in top_sym_names)}." if top_sym_names else ""
            sub_lbls = m.get("sub_labels")
            mod_note = f" (consolidating {', '.join(f'`{s}`' for s in sub_lbls)})" if sub_lbls else f" (`{m['label']}`)"
            pages.append({
                "id": pid,
                "section_id": sub_sec,
                "title": htitle,
                "parent": parent_id,
                "summary": (
                    f"{htitle} subsystem{mod_note}, covering {len(m['files'])} files "
                    f"and {m.get('symbol_count', 0)} symbols.{sym_desc}"
                ),
                "communities": cids,
                "files": list(m["files"]),
                "related": [parent_id],
            })
        sec_num += 1

    # Always append the final Glossary chapter (`N. Glossary`) just like deepwiki.com
    glossary_id = f"{sec_num}-glossary"
    pages.append({
        "id": glossary_id,
        "section_id": str(sec_num),
        "title": "Glossary",
        "parent": None,
        "summary": f"Definitions and technical context for {project_title} domain terms, acronyms, file formats, and core code entities.",
        "communities": [c["id"] for c in comms_all[:8]],
        "files": overview_files[:20],
        "related": ["1-overview"],
    })

    _link_related_by_deps(structure, pages)
    return {"title": f"{project_title} DeepWiki", "pages": pages, "planner": "canonical-3source"}


def _link_related_by_deps(structure: dict[str, Any], pages: list[dict[str, Any]]) -> None:
    by_comm: dict[int, list[str]] = defaultdict(list)
    for p in pages:
        if p["id"] in ("overview", "1-overview"):
            continue
        for cid in p["communities"]:
            by_comm[cid].append(p["id"])
    for a, b, _w in structure.get("community_edges") or []:
        for pa in by_comm.get(a, []):
            for pb in by_comm.get(b, []):
                for src, dst in ((pa, pb), (pb, pa)):
                    page = next(p for p in pages if p["id"] == src)
                    if dst not in page["related"] and dst != src and len(page["related"]) < 8:
                        page["related"].append(dst)


def validate_outline(outline: dict[str, Any], structure: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    known_files = set(scan_git_files(repo_root, structure))
    comm_ids = {c["id"] for c in structure.get("communities") or []}
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
        pages.insert(0, fallback_outline(structure, repo_root=repo_root)["pages"][0])
        seen.add(pages[0]["id"])
    ids = {p["id"] for p in pages}
    for p in pages:
        if p["parent"] is not None:
            p["parent"] = slugify(str(p["parent"]))
            if p["parent"] not in ids or p["parent"] == p["id"]:
                p["parent"] = None
        p["related"] = [r for r in dict.fromkeys(p["related"]) if r in ids and r != p["id"]]
        if not p["files"] and p["communities"] and p["id"] not in ("overview", "1-overview"):
            p["files"] = sorted({f for c in structure.get("communities", []) if c["id"] in p["communities"]
                                 for f in c["files"]})
    return {
        "title": str(outline.get("title") or f"{structure.get('project', 'Repo')} DeepWiki"),
        "pages": pages,
        "planner": outline.get("planner", "validated"),
    }


def plan_outline(
    structure: dict[str, Any],
    repo_root: Path | None = None,
    doc_files_mentioned: set[str] | None = None,
) -> dict[str, Any]:
    outline = fallback_outline(structure, repo_root=repo_root, doc_files_mentioned=doc_files_mentioned)
    return validate_outline(outline, structure, repo_root=repo_root)


def write_repo_dossier(
    out_dir: Path,
    structure: dict[str, Any],
    outline: dict[str, Any],
    links: dict[str, Any],
    repo_root: Path | None = None,
) -> Path:
    """Write `wiki/.packets/_repo_dossier.md` summarizing `git` + `CBM` + `llm-wiki` for LLM outline & page steering."""
    wiki_dir = out_dir / "wiki" if (out_dir / "wiki").is_dir() else out_dir
    packets_dir = wiki_dir / ".packets"
    packets_dir.mkdir(parents=True, exist_ok=True)
    dossier_path = packets_dir / "_repo_dossier.md"

    all_files = scan_git_files(repo_root, structure)
    top_dirs: Counter[str] = Counter()
    build_files: list[str] = []
    for f in all_files:
        parts = PurePosixPath(f).parts
        top_dirs[parts[0] if len(parts) > 1 else "."] += 1
        if f.endswith(("CMakeLists.txt", "BUCK", "targets.bzl", "pyproject.toml", "setup.py", ".fbs")):
            build_files.append(f)

    syms = structure.get("symbols") or {}
    top_classes = sorted(
        [
            (q, s) for q, s in syms.items()
            if s.get("label") in ("Class", "Struct", "Interface")
            and not _is_test_or_demo_path(s.get("file", "").lower())
            and len(s.get("name", "")) >= 4
        ],
        key=lambda qs: -(qs[1].get("fan_in", 0) * 2 + qs[1].get("fan_out", 0)),
    )[:30]

    lines = [
        f"# 3-Source Repository Architecture Dossier (`{structure.get('project')}`)",
        "",
        f"- **Git Commit**: `{structure.get('commit', 'HEAD')}`",
        f"- **Repository Root**: `{repo_root or structure.get('repo_root', '.')}`",
        f"- **Total Tracked Files (`git` + `CBM`)**: `{len(all_files)}` (`{len(structure.get('files', {}))}` indexed by CBM)",
        f"- **Total Code Symbols (`CBM`)**: `{len(syms)}` (`{len(structure.get('call_edges', []))}` call edges, `{len(structure.get('inherits', []))}` inheritance edges)",
        f"- **Linked `llm-wiki` / `RAG` Docs**: `{links.get('stats', {}).get('total_collection_docs', 0)}`",
        "",
        "## 1. Git Top-Level Directory Distribution",
        "",
        "| Directory | File Count |",
        "|---|---|",
        *[f"| `{d}` | {cnt} |" for d, cnt in top_dirs.most_common(18)],
        "",
        "## 2. Build & Schema Configuration Files (`git`)",
        "",
        *[f"- `{bf}`" for bf in build_files[:25]],
        "",
        "## 3. Highest-Centrality Classes & Interfaces (`CBM`)",
        "",
        "| Symbol | Kind | File & Lines | Fan-In / Out |",
        "|---|---|---|---|",
        *[
            f"| `{s['name']}` | {s['label']} | `[{s['file']}:{s['start']}-{s['end']}]()` | `{s['fan_in']}` / `{s['fan_out']}` |"
            for _q, s in top_classes
        ],
        "",
        "## 4. Planned DeepWiki Canonical Outline (`wiki/outline.json`)",
        "",
        "| Section | Page ID | Title | Files | Linked Docs |",
        "|---|---|---|---|---|",
    ]
    for p in outline.get("pages", []):
        pdocs = len(links.get("page_to_docs", {}).get(p["id"], []))
        lines.append(
            f"| `{p.get('section_id') or ''}` | `{p['id']}` | {p['title']} | {len(p.get('files', []))} | {pdocs} |"
        )
    dossier_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dossier_path


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)
