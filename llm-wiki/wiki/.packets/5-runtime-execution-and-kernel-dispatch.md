# 3-Source Context Packet (`git` + `CBM` + `llm-wiki`) for `5-runtime-execution-and-kernel-dispatch` — Runtime Execution and Kernel Dispatch

- **Target Wiki File**: `wiki/5-runtime-execution-and-kernel-dispatch.md`
- **Archetype**: `Parent Hub Page`
- **Parent Page**: `None (Top-Level Chapter)`
- **Summary**: Architectural overview of Runtime Execution and Kernel Dispatch, spanning 157 source files and 3718 code symbols across 6 subsystems.
- **Valid `[[wikilink]]` Neighbours**: `[[1-overview|Overview]]`, `[[3-backend-delegation-and-hardware-providers|Backend Delegation and Hardware Providers]]`, `[[3.1-backends-backendscommon|Backends Backendscommon]]`, `[[3.2-backends-reference|Backends Reference]]`, `[[3.3-backends-opencl|Backends OpenCL]]`, `[[3.4-backends-aclcommon|Backends Aclcommon]]`, `[[3.6-other-backends|Other Backends]]`, `[[5.1-armnn|ArmNN]]`

## 1. Relevant Source Files (`git` + `CBM`, use verbatim in `<details>`)
- `[samples/common/include/Audio/DataStructures.hpp](samples/common/include/Audio/DataStructures.hpp)`
- `[src/armnn/Tensor.cpp](src/armnn/Tensor.cpp)`
- `[include/armnn/Exceptions.hpp](include/armnn/Exceptions.hpp)`
- `[include/armnn/Tensor.hpp](include/armnn/Tensor.hpp)`
- `[src/armnn/Layer.cpp](src/armnn/Layer.cpp)`
- `[include/armnn/utility/IgnoreUnused.hpp](include/armnn/utility/IgnoreUnused.hpp)`
- `[delegate/classic/src/ClassicDelegateUtils.hpp](delegate/classic/src/ClassicDelegateUtils.hpp)`
- `[delegate/opaque/src/OpaqueDelegateUtils.hpp](delegate/opaque/src/OpaqueDelegateUtils.hpp)`
- `[include/armnnTestUtils/WorkloadTestUtils.hpp](include/armnnTestUtils/WorkloadTestUtils.hpp)`
- `[include/armnn/BackendId.hpp](include/armnn/BackendId.hpp)`
- `[include/armnn/Types.hpp](include/armnn/Types.hpp)`
- `[src/armnnTestUtils/TensorCopyUtils.cpp](src/armnnTestUtils/TensorCopyUtils.cpp)`
- `[include/armnn/Optional.hpp](include/armnn/Optional.hpp)`
- `[src/armnn/Descriptors.cpp](src/armnn/Descriptors.cpp)`
- `[include/armnn/utility/PolymorphicDowncast.hpp](include/armnn/utility/PolymorphicDowncast.hpp)`
- `[src/armnnSerializer/Serializer.cpp](src/armnnSerializer/Serializer.cpp)`
- `[src/armnn/Layer.hpp](src/armnn/Layer.hpp)`
- `[include/armnn/LstmParams.hpp](include/armnn/LstmParams.hpp)`
- `[src/armnn/Graph.hpp](src/armnn/Graph.hpp)`
- `[src/armnn/Exceptions.cpp](src/armnn/Exceptions.cpp)`
- `[src/armnnUtils/Permute.cpp](src/armnnUtils/Permute.cpp)`
- `[src/armnnUtils/TensorUtils.cpp](src/armnnUtils/TensorUtils.cpp)`
- `[delegate/classic/src/armnn_delegate.cpp](delegate/classic/src/armnn_delegate.cpp)`

## 2. Grounded Code Symbols (`CBM`, use verbatim for `[file:start-end]()` pill citations)
- `InvalidArgumentException` (Class) @ `[include/armnn/Exceptions.hpp:80-84]()` [fan-in=273, fan-out=0] — 
- `Exception` (Class) @ `[include/armnn/Exceptions.hpp:46-65]()` [fan-in=181, fan-out=0] — /// Base class for all ArmNN exceptions so that users can filter to just those.
- `TensorInfo` (Class) @ `[include/armnn/Tensor.hpp:152-274]()` [fan-in=121, fan-out=0] — 
- `EmptyOptional` (Class) @ `[include/armnn/Optional.hpp:32-32]()` [fan-in=102, fan-out=0] — /// EmptyOptional is used to initialize the Optional class in case we want /// to have default value for an Optional in a function declaration.
- `NullPointerException` (Class) @ `[include/armnn/Exceptions.hpp:146-150]()` [fan-in=101, fan-out=0] — 
- `ParseException` (Class) @ `[include/armnn/Exceptions.hpp:92-96]()` [fan-in=98, fan-out=0] — 
- `LayerValidationException` (Class) @ `[include/armnn/Exceptions.hpp:105-108]()` [fan-in=73, fan-out=0] — 
- `TensorShape` (Class) @ `[include/armnn/Tensor.hpp:20-150]()` [fan-in=53, fan-out=0] — 
- `BackendId` (Class) @ `[include/armnn/BackendId.hpp:78-148]()` [fan-in=48, fan-out=0] — 
- `Tensor` (Class) @ `[include/armnn/Tensor.hpp:321-326]()` [fan-in=39, fan-out=0] — /// A tensor defined by a TensorInfo (shape and data type) and a mutable backing store.
- `ConstTensor` (Class) @ `[include/armnn/Tensor.hpp:329-392]()` [fan-in=32, fan-out=0] — /// A tensor defined by a TensorInfo (shape and data type) and an immutable backing store.
- `UnimplementedException` (Class) @ `[include/armnn/Exceptions.hpp:98-103]()` [fan-in=35, fan-out=0] — 
- `RuntimeException` (Class) @ `[include/armnn/Exceptions.hpp:120-123]()` [fan-in=18, fan-out=0] — 
- `MemoryImportException` (Class) @ `[include/armnn/Exceptions.hpp:125-128]()` [fan-in=10, fan-out=0] — 
- `FileNotFoundException` (Class) @ `[include/armnn/Exceptions.hpp:86-90]()` [fan-in=7, fan-out=0] — 
- `GraphValidationException` (Class) @ `[include/armnn/Exceptions.hpp:110-113]()` [fan-in=6, fan-out=0] — 
- `BackendUnavailableException` (Class) @ `[include/armnn/Exceptions.hpp:68-72]()` [fan-in=0, fan-out=0] — /// Class for non-fatal exceptions raised while initialising a backend
- `IBackend` (Class) @ `[include/armnn/Types.hpp:273-281]()` [fan-in=0, fan-out=0] — /// Each backend should implement an IBackend.
- `IDeviceSpec` (Class) @ `[include/armnn/Types.hpp:301-308]()` [fan-in=0, fan-out=0] — /// Device specific knowledge to be passed to the optimizer.
- `ConstructInPlace` (Class) @ `[include/armnn/Optional.hpp:36-39]()` [fan-in=0, fan-out=0] — /// Disambiguation tag that can be passed to the constructor to indicate that /// the contained object should be constructed in-place
- `OptionalBase` (Class) @ `[include/armnn/Optional.hpp:45-73]()` [fan-in=0, fan-out=0] — /// OptionalBase is the common functionality between reference and non-reference /// optional types.
- `BadOptionalAccessException` (Class) @ `[include/armnn/Exceptions.hpp:115-118]()` [fan-in=2, fan-out=0] — 

## 3. Grounded Source Code Excerpts (`git` Working Tree)
### `InvalidArgumentException` in `[include/armnn/Exceptions.hpp:80-84]()`
```cpp
class InvalidArgumentException : public Exception
{
public:
    using Exception::Exception;
};
```

### `Exception` in `[include/armnn/Exceptions.hpp:46-61]()`
```cpp
class Exception : public std::exception
{
public:
    explicit Exception(const std::string& message);

    /// exception with context
    explicit Exception(const std::string& message,
                       const CheckLocation& location);

    /// preserving previous exception context
    /// and adding local context information
    explicit Exception(const Exception& other,
                       const std::string& message,
                       const CheckLocation& location);

    virtual const char* what() const noexcept override;
```

### `TensorInfo` in `[include/armnn/Tensor.hpp:152-167]()`
```cpp
class TensorInfo
{
public:
    /// Empty (invalid) constructor.
    TensorInfo();

    TensorInfo(const TensorShape& shape,
               DataType dataType,
               float quantizationScale = 1.0f,
               int32_t quantizationOffset = 0,
               bool isConstant = false);

    TensorInfo(unsigned int numDimensions,
               const unsigned int* dimensionSizes,
               DataType dataType,
               float quantizationScale = 1.0f,
```

### `NullPointerException` in `[include/armnn/Exceptions.hpp:146-150]()`
```cpp
class NullPointerException : public Exception
{
public:
    using Exception::Exception;
};
```

### `ParseException` in `[include/armnn/Exceptions.hpp:92-96]()`
```cpp
class ParseException : public Exception
{
public:
    using Exception::Exception;
};
```


## 4. Linked Official Docs (`llm-wiki` / `RAG`)
- **ArmNN** (`wiki/5.2-armnn.md`, score=88.992, shared_symbols=['BackendId', 'ConstTensor', 'EmptyOptional', 'Exception', 'InvalidArgumentException', 'LayerValidationException', 'NullPointerException', 'ParseException']): # ArmNN ↑ [[5-runtime-execution-and-kernel-dispatch|Runtime Execution and Kernel Dispatch]] > ArmNN subsystem (`include/armnn`), covering 21 files and 440 symbols. Key symbols include `GetShape`, `InvalidArgumentException`, `GetNumElements`, `Exception`. <details> <summary>Relevant source files</summary> The following files were used as context for gener
- **Overview** (`wiki/1-overview.md`, score=67.096, shared_symbols=['Exception', 'InvalidArgumentException', 'LayerValidationException', 'NullPointerException', 'ParseException', 'TensorInfo']): # Overview > End-to-end architecture overview of ArmNN: core subsystems, compilation/execution pipeline, entry points, and cross-module dependencies. <details> <summary>Relevant source files</summary> The following files were used as context for generating this wiki page: - [src/armnn/Tensor.cpp](src/armnn/Tensor.cpp) - [include/armnn/Exceptions.hpp](inc
- **Glossary** (`wiki/7-glossary.md`, score=61.096, shared_symbols=['BackendId', 'ConstTensor', 'Exception', 'InvalidArgumentException', 'LayerValidationException', 'NullPointerException', 'ParseException', 'Tensor']): # Glossary > Definitions and technical context for ArmNN domain terms, acronyms, file formats, and core code entities. <details> <summary>Relevant source files</summary> The following files were used as context for generating this wiki page: - [src/armnn/Tensor.cpp](src/armnn/Tensor.cpp) - [include/armnn/Exceptions.hpp](include/armnn/Exceptions.hpp) - [i
- **Profiling Common** (`wiki/6.1-profiling-common.md`, score=60.665, shared_symbols=['BadOptionalAccessException', 'EmptyOptional', 'Exception', 'InvalidArgumentException', 'Optional', 'Tensor', 'TimeoutException', 'UnimplementedException']): # Profiling Common ↑ [[6-developer-tools-and-platform-targets|Developer Tools and Platform Targets]] > Profiling Common subsystem (`profiling/common`), covering 28 files and 244 symbols. Key symbols include `IgnoreUnused`, `ProfilingException`, `CentreAlignFormatting`, `InvalidArgumentException`. <details> <summary>Relevant source files</summary> The fol
- **ArmNN DeepWiki** (`wiki/index.md`, score=52.868, shared_symbols=['Exception', 'InvalidArgumentException']): # ArmNN DeepWiki Generated from `home-jason-Project-deepwiki-armnn` at commit `2b61cecc9df7` (2026-11-14T15:13:53+00:00). ## Pages - [[1-overview|Overview]] — End-to-end architecture overview of ArmNN: core subsystems, compilation/execution pipeline, entry points, and cross-module dependencies. - [[2-build-system-and-infrastructure|Build System and Infras
- **ArmNN** (`wiki/5.1-armnn.md`, score=37.746, shared_symbols=['Tensor', 'TensorInfo']): # ArmNN ↑ [[5-runtime-execution-and-kernel-dispatch|Runtime Execution and Kernel Dispatch]] > ArmNN subsystem (`src/armnn`), covering 28 files and 1007 symbols. Key symbols include `SetTensorInfo`, `Connect`, `end`, `GetName`. <details> <summary>Relevant source files</summary> The following files were used as context for generating this wiki page: - [sr

## 5. Pre-Verified DeepWiki v1.9.9.5 Mermaid Diagrams
### Natural Language Space <-> Code Entity Space
```mermaid
graph LR
  subgraph NL_Space["Natural Language Space"]
    NL_0["Invalid Argument Exception"]
    NL_1["Exception"]
    NL_2["Tensor Info"]
    NL_3["Empty Optional"]
    NL_4["Null Pointer Exception"]
    NL_5["Parse Exception"]
  end
  subgraph Code_Space["Code Entity Space"]
    CE_0["InvalidArgumentException (Exceptions.hpp:80)"]
    CE_1["Exception (Exceptions.hpp:46)"]
    CE_2["TensorInfo (Tensor.hpp:152)"]
    CE_3["EmptyOptional (Optional.hpp:32)"]
    CE_4["NullPointerException (Exceptions.hpp:146)"]
    CE_5["ParseException (Exceptions.hpp:92)"]
  end
  NL_0 -->|"implemented by"| CE_0
  NL_1 -->|"implemented by"| CE_1
  NL_2 -->|"implemented by"| CE_2
  NL_3 -->|"implemented by"| CE_3
  NL_4 -->|"implemented by"| CE_4
  NL_5 -->|"implemented by"| CE_5
```

### Subsystem Architecture Flowchart
```mermaid
flowchart TD
  subgraph sub_this["Runtime Execution and Kernel Dispatch"]
    subgraph sg_0["samples/common/include"]
      n_samples_common_include_Audio["Audio/"]
    end
    subgraph sg_1["src"]
      n_src_armnn["armnn/"]
      n_src_armnnTestUtils["armnnTestUtils/"]
      n_src_armnnSerializer["armnnSerializer/"]
      n_src_armnnUtils["armnnUtils/"]
    end
    subgraph sg_2["include"]
      n_include_armnn["armnn/"]
      n_include_armnnTestUtils["armnnTestUtils/"]
    end
    subgraph sg_3["include/armnn"]
      n_include_armnn_utility["utility/"]
    end
    subgraph sg_4["delegate/classic"]
      n_delegate_classic_src["src/"]
    end
  end
  n_page_5_1_armnn(["ArmNN"])
  n_page_5_3_delegate_opaque(["Delegate Opaque"])
  n_page_5_4_delegate_classic(["Delegate Classic"])
  n_page_5_6_other_runtime_components(["Other Runtime Components"])
  n_delegate_classic_src -.-> n_page_5_4_delegate_classic
  n_src_armnn -.-> n_page_5_6_other_runtime_components
  n_delegate_opaque_src -.-> n_page_5_3_delegate_opaque
  n_src_armnn -.-> n_page_5_1_armnn
  n_include_armnn -.-> n_page_5_1_armnn
  n_include_armnn -.-> n_page_5_6_other_runtime_components
  n_include_armnn -.-> n_page_5_3_delegate_opaque
  n_include_armnn -.-> n_page_5_4_delegate_classic
  n_include_armnn --> n_src_armnn
  n_include_armnn_utility --> n_src_armnnSerializer
  n_src_armnn -.-> n_page_5_3_delegate_opaque
```

### Class Hierarchy Diagram
```mermaid
classDiagram
  class InvalidArgumentException {
  }
  class Exception {
  }
  class TensorInfo {
    +GetShape()
    +SetShape()
    +GetNumDimensions()
    +GetNumElements()
    +GetDataType()
    +SetDataType()
  }
  class EmptyOptional {
  }
  class NullPointerException {
  }
  class ParseException {
  }
  class LayerValidationException {
  }
  class TensorShape {
    +GetDimensionality()
  }
```

### Call Sequence Diagram
```mermaid
sequenceDiagram
  participant Exceptions as "Exceptions"
  participant Tensor as "Tensor"
  participant Optional as "Optional"
  Exceptions->>Exceptions: InvalidArgumentException() -' Exception()
  Exceptions->>Tensor: Exception() -' TensorInfo()
  Tensor->>Optional: TensorInfo() -' EmptyOptional()
  Optional->>Exceptions: EmptyOptional() -' NullPointerException()
  Exceptions->>Exceptions: NullPointerException() -' ParseException()
```

## 6. DeepWiki v1.9.9.5 Authoring Checklist for `wiki/5-runtime-execution-and-kernel-dispatch.md`
1. Keep YAML frontmatter at top (`id`, `title`, `parent`, `sources`, `linked_docs`, `bridge_symbols`).
2. Keep `<details><summary>Relevant source files</summary>` block immediately after `# Title`.
3. Start with `## Purpose and Scope`, then numbered `## 1. ...`, `## 2. ...` sections separated by `---`.
4. Include at least 2 ```mermaid``` diagrams (including a `Natural Language Space` <-> `Code Entity Space` mapping).
5. Cite code entities inline using `[path/to/file.ext:start-end]()` and end every `##` section with `Sources: [file:start-end]()`.
6. Run `deepwiki_cli.py build --enrich-only ...` and `deepwiki_cli.py validate ...` after editing.
