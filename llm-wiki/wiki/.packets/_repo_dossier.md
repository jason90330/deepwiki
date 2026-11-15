# 3-Source Repository Architecture Dossier (`home-jason-Project-deepwiki-armnn`)

- **Git Commit**: `2b61cecc9df7a43fca1463795062cf359e6be820`
- **Repository Root**: `/home/jason/Project/deepwiki/armnn`
- **Total Tracked Files (`git` + `CBM`)**: `2425` (`2332` indexed by CBM)
- **Total Code Symbols (`CBM`)**: `13625` (`0` call edges, `0` inheritance edges)
- **Linked `llm-wiki` / `RAG` Docs**: `40`

## 1. Git Top-Level Directory Distribution

| Directory | File Count |
|---|---|
| `src` | 1654 |
| `delegate` | 226 |
| `profiling` | 143 |
| `tests` | 118 |
| `samples` | 95 |
| `include` | 83 |
| `third-party` | 33 |
| `.` | 21 |
| `docs` | 21 |
| `build-tool` | 11 |
| `cmake` | 9 |
| `scripts` | 6 |
| `LICENSES` | 3 |
| `docker` | 2 |

## 2. Build & Schema Configuration Files (`git`)

- `CMakeLists.txt`
- `delegate/CMakeLists.txt`
- `delegate/armnnDelegateJNI/CMakeLists.txt`
- `delegate/classic/CMakeLists.txt`
- `delegate/opaque/CMakeLists.txt`
- `include/armnn/backends/CMakeLists.txt`
- `profiling/CMakeLists.txt`
- `profiling/client/src/CMakeLists.txt`
- `profiling/common/src/CMakeLists.txt`
- `profiling/server/src/basePipeServer/CMakeLists.txt`
- `profiling/server/src/timelineDecoder/CMakeLists.txt`
- `samples/CMakeLists.txt`
- `samples/KeywordSpotting/CMakeLists.txt`
- `samples/ObjectDetection/CMakeLists.txt`
- `samples/SpeechRecognition/CMakeLists.txt`
- `src/armnnDeserializer/CMakeLists.txt`
- `src/armnnSerializer/ArmnnSchema.fbs`
- `src/armnnSerializer/CMakeLists.txt`
- `src/armnnTestUtils/CMakeLists.txt`
- `src/armnnTfLiteParser/CMakeLists.txt`
- `src/backends/aclCommon/CMakeLists.txt`
- `src/backends/aclCommon/test/CMakeLists.txt`
- `src/backends/backendsCommon/CMakeLists.txt`
- `src/backends/backendsCommon/memoryOptimizerStrategyLibrary/CMakeLists.txt`
- `src/backends/backendsCommon/memoryOptimizerStrategyLibrary/test/CMakeLists.txt`

## 3. Highest-Centrality Classes & Interfaces (`CBM`)

| Symbol | Kind | File & Lines | Fan-In / Out |
|---|---|---|---|
| `InvalidArgumentException` | Class | `[include/armnn/Exceptions.hpp:80-84]()` | `273` / `0` |
| `Exception` | Class | `[include/armnn/Exceptions.hpp:46-65]()` | `181` / `0` |
| `TensorInfo` | Class | `[include/armnn/Tensor.hpp:152-274]()` | `121` / `0` |
| `EmptyOptional` | Class | `[include/armnn/Optional.hpp:32-32]()` | `102` / `0` |
| `NullPointerException` | Class | `[include/armnn/Exceptions.hpp:146-150]()` | `101` / `0` |
| `ParseException` | Class | `[include/armnn/Exceptions.hpp:92-96]()` | `98` / `0` |
| `LayerValidationException` | Class | `[include/armnn/Exceptions.hpp:105-108]()` | `73` / `0` |
| `TypeAnyOf` | Class | `[src/backends/backendsCommon/LayerSupportRules.hpp:89-99]()` | `64` / `0` |
| `TensorShape` | Class | `[include/armnn/Tensor.hpp:20-150]()` | `53` / `0` |
| `TypesAreEqual` | Class | `[src/backends/backendsCommon/LayerSupportRules.hpp:71-78]()` | `49` / `0` |
| `BackendId` | Class | `[include/armnn/BackendId.hpp:78-148]()` | `48` / `0` |
| `Tensor` | Class | `[include/armnn/Tensor.hpp:321-326]()` | `39` / `0` |
| `UnimplementedException` | Class | `[include/armnn/Exceptions.hpp:98-103]()` | `35` / `0` |
| `BaseDescriptor` | Class | `[include/armnn/Descriptors.hpp:22-26]()` | `34` / `0` |
| `ConstTensor` | Class | `[include/armnn/Tensor.hpp:329-392]()` | `32` / `0` |
| `ProfilingException` | Class | `[profiling/common/include/ProfilingException.hpp:49-65]()` | `32` / `0` |
| `InvalidArgumentException` | Class | `[profiling/common/include/ProfilingException.hpp:84-88]()` | `18` / `0` |
| `RuntimeException` | Class | `[include/armnn/Exceptions.hpp:120-123]()` | `18` / `0` |
| `CreationOptions` | Class | `[include/armnn/IRuntime.hpp:70-183]()` | `14` / `0` |
| `BatchMatMulDescriptor` | Class | `[include/armnn/Descriptors.hpp:1584-1638]()` | `13` / `0` |
| `sqrt` | Class | `[src/backends/reference/workloads/Sqrt.hpp:13-23]()` | `12` / `0` |
| `MemoryImportException` | Class | `[include/armnn/Exceptions.hpp:125-128]()` | `10` / `0` |
| `half` | Class | `[third-party/half/half.hpp:1077-1191]()` | `9` / `0` |
| `BroadcastToDescriptor` | Class | `[include/armnn/Descriptors.hpp:1659-1676]()` | `9` / `0` |
| `basic_string_view` | Class | `[third-party/fmt/core.h:347-430]()` | `7` / `0` |
| `FileNotFoundException` | Class | `[include/armnn/Exceptions.hpp:86-90]()` | `7` / `0` |
| `TimeoutException` | Class | `[profiling/common/include/ProfilingException.hpp:90-94]()` | `6` / `0` |
| `LayerTestResult` | Class | `[include/armnnTestUtils/LayerTestResult.hpp:15-59]()` | `6` / `0` |
| `ResolveTypeImpl<DataType::BFloat16>` | Class | `[src/armnn/ResolveType.hpp:73-76]()` | `6` / `0` |
| `GraphValidationException` | Class | `[include/armnn/Exceptions.hpp:110-113]()` | `6` / `0` |

## 4. Planned DeepWiki Canonical Outline (`wiki/outline.json`)

| Section | Page ID | Title | Files | Linked Docs |
|---|---|---|---|---|
| `1` | `1-overview` | Overview | 17 | 6 |
| `2` | `2-build-system-and-infrastructure` | Build System and Infrastructure | 6 | 6 |
| `2.1` | `2.1-build-infrastructure` | Build Infrastructure | 28 | 6 |
| `3` | `3-backend-delegation-and-hardware-providers` | Backend Delegation and Hardware Providers | 23 | 6 |
| `3.1` | `3.1-backends-backendscommon` | Backends Backendscommon | 28 | 6 |
| `3.2` | `3.2-backends-reference` | Backends Reference | 28 | 6 |
| `3.3` | `3.3-backends-opencl` | Backends OpenCL | 28 | 6 |
| `3.4` | `3.4-backends-aclcommon` | Backends Aclcommon | 10 | 6 |
| `3.5` | `3.5-backends-tosacommon` | Backends Tosacommon | 28 | 6 |
| `3.6` | `3.6-other-backends` | Other Backends | 28 | 6 |
| `4` | `4-testing-validation-and-profiling` | Testing, Validation and Profiling | 6 | 6 |
| `4.1` | `4.1-tests` | Tests | 40 | 6 |
| `5` | `5-runtime-execution-and-kernel-dispatch` | Runtime Execution and Kernel Dispatch | 23 | 6 |
| `5.1` | `5.1-armnn` | ArmNN | 28 | 6 |
| `5.2` | `5.2-armnn` | ArmNN | 21 | 6 |
| `5.3` | `5.3-delegate-opaque` | Delegate Opaque | 28 | 6 |
| `5.4` | `5.4-delegate-classic` | Delegate Classic | 28 | 6 |
| `5.5` | `5.5-armnnutils` | Armnnutils | 24 | 6 |
| `5.6` | `5.6-other-runtime-components` | Other Runtime Components | 28 | 6 |
| `6` | `6-developer-tools-and-platform-targets` | Developer Tools and Platform Targets | 19 | 6 |
| `6.1` | `6.1-profiling-common` | Profiling Common | 28 | 6 |
| `6.2` | `6.2-profiling-client` | Profiling Client | 28 | 6 |
| `6.3` | `6.3-profiling-server` | Profiling Server | 13 | 6 |
| `6.4` | `6.4-profiling` | Profiling | 1 | 6 |
| `7` | `7-glossary` | Glossary | 17 | 6 |
