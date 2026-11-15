# 3-Source Repository Architecture Dossier (`home-jason-Project-deepwiki-executorch`)

- **Git Commit**: `b3b565b5b62f5e03d57c9054b5a2570a04f0d937`
- **Repository Root**: `/home/jason/Project/deepwiki/executorch`
- **Total Tracked Files (`git` + `CBM`)**: `11298` (`10202` indexed by CBM)
- **Total Code Symbols (`CBM`)**: `85820` (`25000` call edges, `1411` inheritance edges)
- **Linked `llm-wiki` / `RAG` Docs**: `143`

## 1. Git Top-Level Directory Distribution

| Directory | File Count |
|---|---|
| `backends` | 6220 |
| `examples` | 1746 |
| `extension` | 789 |
| `kernels` | 603 |
| `docs` | 335 |
| `exir` | 327 |
| `runtime` | 272 |
| `.ci` | 189 |
| `devtools` | 152 |
| `.github` | 114 |
| `website` | 114 |
| `codegen` | 53 |
| `.` | 45 |
| `test` | 38 |
| `tools` | 36 |
| `export` | 33 |
| `zephyr` | 32 |
| `shim_et` | 30 |

## 2. Build & Schema Configuration Files (`git`)

- `.ci/scripts/BUCK`
- `BUCK`
- `CMakeLists.txt`
- `backends/aoti/BUCK`
- `backends/aoti/CMakeLists.txt`
- `backends/aoti/passes/BUCK`
- `backends/aoti/slim/c10/core/BUCK`
- `backends/aoti/slim/c10/core/targets.bzl`
- `backends/aoti/slim/c10/core/test/BUCK`
- `backends/aoti/slim/c10/core/test/targets.bzl`
- `backends/aoti/slim/c10/cuda/BUCK`
- `backends/aoti/slim/c10/cuda/targets.bzl`
- `backends/aoti/slim/c10/macros/BUCK`
- `backends/aoti/slim/c10/macros/targets.bzl`
- `backends/aoti/slim/core/BUCK`
- `backends/aoti/slim/core/targets.bzl`
- `backends/aoti/slim/core/test/BUCK`
- `backends/aoti/slim/core/test/targets.bzl`
- `backends/aoti/slim/cuda/BUCK`
- `backends/aoti/slim/cuda/targets.bzl`
- `backends/aoti/slim/cuda/test/BUCK`
- `backends/aoti/slim/cuda/test/targets.bzl`
- `backends/aoti/slim/factory/BUCK`
- `backends/aoti/slim/factory/targets.bzl`
- `backends/aoti/slim/factory/test/BUCK`

## 3. Highest-Centrality Classes & Interfaces (`CBM`)

| Symbol | Kind | File & Lines | Fan-In / Out |
|---|---|---|---|
| `OpFeatures` | Class | `[backends/vulkan/op_registry.py:28-129]()` | `92` / `0` |
| `Converter<std::string>` | Class | `[backends/apple/coreml/runtime/kvstore/key_value_store.hpp:96-106]()` | `70` / `0` |
| `Tensor` | Class | `[extension/apple/ExecuTorch/Exported/ExecuTorch+Tensor.swift:1127-1131]()` | `61` / `0` |
| `EdgeCompileConfig` | Class | `[exir/capture/_config.py:38-51]()` | `58` / `0` |
| `WorkerError` | Class | `[examples/llm_server/python/worker_client.py:108-127]()` | `42` / `0` |
| `ExecutorchBackendConfig` | Class | `[exir/capture/_config.py:56-140]()` | `31` / `0` |
| `Value` | Class | `[extension/apple/ExecuTorch/Exported/ExecuTorch+Value.swift:169-173]()` | `29` / `0` |
| `NSNumber` | Class | `[extension/apple/ExecuTorch/Exported/ExecuTorch+Value.swift:205-212]()` | `25` / `0` |
| `MemoryPlanningPass` | Class | `[exir/passes/memory_planning_pass.py:193-372]()` | `25` / `0` |
| `CudaPartitioner` | Class | `[backends/cuda/cuda_partitioner.py:20-53]()` | `25` / `0` |
| `ImageProcessorConfig` | Class | `[extension/android/executorch_android/src/main/java/org/pytorch/executorch/extension/image/ImageProcessorConfig.kt:116-167]()` | `23` / `0` |
| `MLXPartitioner` | Class | `[backends/mlx/partitioner.py:95-386]()` | `23` / `0` |
| `ImageProcessor` | Class | `[extension/android/executorch_android/src/main/java/org/pytorch/executorch/extension/image/ImageProcessor.kt:37-361]()` | `22` / `0` |
| `PartitionAnchors` | Class | `[backends/cadence/aot/quantizer/patterns.py:40-71]()` | `20` / `0` |
| `CompileSpec` | Class | `[exir/_serialize/generated/executorch_flatbuffer/CompileSpec.py:11-65]()` | `20` / `0` |
| `SerializeError` | Class | `[exir/serde/export_serialize.py:125-126]()` | `18` / `0` |
| `AddModule` | Class | `[examples/models/toy_model/model.py:42-54]()` | `18` / `0` |
| `PartitionAnchors` | Class | `[backends/nxp/quantizer/patterns.py:60-93]()` | `17` / `0` |
| `Shape` | Class | `[backends/nxp/backend/ir/tflite_generator/tflite_model.py:302-368]()` | `17` / `0` |
| `OpStep` | Class | `[backends/mlx/pattern_utils.py:105-193]()` | `17` / `0` |
| `ResourceLimitError` | Class | `[backends/native/runtime/deserialize/DeserializeError.h:13-16]()` | `17` / `0` |
| `QuantizationConfig` | Class | `[backends/qualcomm/quantizer/qconfig.py:39-45]()` | `17` / `0` |
| `NodeArgsIdx` | Class | `[backends/nxp/quantizer/patterns.py:44-56]()` | `16` / `0` |
| `Linear` | Class | `[backends/qualcomm/quantizer/annotators/htp_rules.py:965-1044]()` | `15` / `0` |
| `Module` | Class | `[extension/apple/ExecuTorch/Exported/ExecuTorch+Module.swift:210-327]()` | `14` / `0` |
| `SPVGenerator` | Class | `[backends/vulkan/runtime/gen_vulkan_spv.py:791-1441]()` | `14` / `0` |
| `Operator` | Class | `[backends/nxp/backend/ir/tflite_generator/tflite_model.py:493-654]()` | `14` / `0` |
| `ExportPassBaseError` | Class | `[exir/pass_base.py:232-233]()` | `12` / `0` |
| `XTS3Operation` | Class | `[backends/espressif/serialization/xts3.py:135-140]()` | `11` / `0` |
| `XnnpackPartitioner` | Class | `[backends/xnnpack/partition/xnnpack_partitioner.py:30-143]()` | `11` / `0` |

## 4. Planned DeepWiki Canonical Outline (`wiki/outline.json`)

| Section | Page ID | Title | Files | Linked Docs |
|---|---|---|---|---|
| `1` | `1-overview` | Overview | 10 | 6 |
| `1.1` | `1.1-getting-started` | Getting Started | 22 | 6 |
| `1.2` | `1.2-export-api-and-recipe-system` | Export API and Recipe System | 37 | 6 |
| `2` | `2-build-system-and-infrastructure` | Build System and Infrastructure | 38 | 6 |
| `2.1` | `2.1-cmake-configuration-and-targets` | CMake Configuration and Targets | 17 | 6 |
| `2.2` | `2.2-kernel-libraries-and-selective-build` | Kernel Libraries and Selective Build | 31 | 6 |
| `2.3` | `2.3-schema-generation-and-flatbuffers` | Schema Generation and FlatBuffers | 36 | 6 |
| `2.4` | `2.4-python-bindings-and-dependencies` | Python Bindings and Dependencies | 15 | 6 |
| `2.5` | `2.5-buck2-and-shim-build-layer` | Buck2 and Shim Build Layer | 30 | 6 |
| `3` | `3-exir-core-system` | EXIR Core System | 40 | 6 |
| `3.1` | `3.1-program-structure-and-compilation-flow` | Program Structure and Compilation Flow | 12 | 6 |
| `3.2` | `3.2-graph-transformation-pass-system` | Graph Transformation Pass System | 30 | 6 |
| `3.3` | `3.3-memory-planning-and-allocation` | Memory Planning and Allocation | 5 | 6 |
| `3.4` | `3.4-program-emission-and-serialization` | Program Emission and Serialization | 35 | 6 |
| `3.5` | `3.5-verification-and-dialect-system` | Verification and Dialect System | 34 | 6 |
| `4` | `4-quantization-systems` | Quantization Systems | 38 | 6 |
| `4.1` | `4.1-quantization-framework-and-patterns` | Quantization Framework and Patterns | 35 | 6 |
| `4.2` | `4.2-backend-specific-quantization` | Backend-Specific Quantization | 35 | 6 |
| `5` | `5-backend-delegation-architecture` | Backend Delegation Architecture | 40 | 6 |
| `5.1` | `5.1-partitioning-and-operator-support` | Partitioning and Operator Support | 17 | 6 |
| `5.2` | `5.2-vulkan-gpu-backend` | Vulkan GPU Backend | 40 | 6 |
| `5.3` | `5.3-qualcomm-qnn-backend` | Qualcomm QNN Backend | 40 | 6 |
| `5.4` | `5.4-arm-tosa-and-ethos-u-backend` | ARM TOSA and Ethos-U Backend | 40 | 6 |
| `5.5` | `5.5-cadence-dsp-backend` | Cadence DSP Backend | 36 | 6 |
| `5.6` | `5.6-xnnpack-cpu-backend` | XNNPACK CPU Backend | 36 | 6 |
| `5.7` | `5.7-cuda-aoti-and-apple-metal-backends` | CUDA / AOTI and Apple Metal Backends | 40 | 6 |
| `5.8` | `5.8-other-backends` | Other Hardware Backends (OpenVINO, MediaTek, Samsung, NXP, MLX, TensorRT) | 40 | 6 |
| `6` | `6-model-export-and-llm-support` | Model Export and LLM Support | 40 | 6 |
| `6.1` | `6.1-llama-model-export` | LLaMA and Generative Model Export | 40 | 6 |
| `6.2` | `6.2-llm-runner-framework` | LLM Runner Framework | 36 | 6 |
| `6.3` | `6.3-custom-operators-and-extensions` | Custom Operators and Extensions | 39 | 6 |
| `6.4` | `6.4-multimodal-and-audio-models` | Multimodal and Audio Models | 36 | 6 |
| `7` | `7-testing-and-cicd-infrastructure` | Testing and CI/CD Infrastructure | 36 | 6 |
| `7.1` | `7.1-cicd-workflows-and-validation` | CI/CD Workflows and Validation | 31 | 6 |
| `7.2` | `7.2-model-and-backend-testing-framework` | Model and Backend Testing Framework | 40 | 6 |
| `7.3` | `7.3-performance-benchmarking-and-profiling` | Performance Benchmarking and Profiling | 36 | 6 |
| `8` | `8-runtime-execution` | Runtime Execution | 39 | 6 |
| `8.1` | `8.1-core-runtime-architecture` | Core Runtime Architecture | 38 | 6 |
| `8.2` | `8.2-kernel-registration-and-dispatch` | Kernel Registration and Dispatch | 36 | 6 |
| `8.3` | `8.3-developer-tools-devtools` | Developer Tools (DevTools: ETDump, ETRecord, Inspector) | 38 | 6 |
| `9` | `9-mobile-and-platform-extensions` | Mobile and Platform Extensions | 40 | 6 |
| `9.1` | `9.1-android-extension` | Android Extension (Java/Kotlin & JNI) | 33 | 6 |
| `9.2` | `9.2-apple-ios-macos-extension` | Apple iOS/macOS Extension (Swift & Objective-C) | 26 | 6 |
| `9.3` | `9.3-high-level-module-and-on-device-training` | High-Level Module API, Tensor & On-Device Training | 37 | 6 |
| `9.4` | `9.4-embedded-and-web-targets` | Embedded (Zephyr, ESP32, Pico2) and WebAssembly/WebGPU Targets | 40 | 6 |
| `10` | `10-glossary` | Glossary | 10 | 6 |
