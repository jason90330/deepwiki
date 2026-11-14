---
id: 4-compute-backends
section_id: '4'
title: 4 Compute Backends
parent: null
order: 110
type: section
source_url: https://github.com/ARM-software/armnn/blob/branches/armnn_24_11
sources:
- delegate/test/BatchMatMulTest.cpp
- include/armnn/backends/IBackendInternal.hpp
- scripts/get_compute_library.sh
- src/backends/aclCommon/ArmComputeSubgraphUtils.hpp
- src/backends/backendsCommon/IBackendInternal.cpp
- src/backends/backendsCommon/test/CompatibilityTests.cpp
- src/backends/backendsCommon/test/JsonPrinterTestImpl.cpp
- src/backends/backendsCommon/test/layerTests/BatchMatMulTestImpl.cpp
- src/backends/cl/ClBackend.cpp
- src/backends/cl/ClBackend.hpp
- src/backends/cl/workloads/ClBatchMatMulWorkload.cpp
- src/backends/cl/workloads/ClBatchMatMulWorkload.hpp
- src/backends/cl/workloads/ClQLstmWorkload.cpp
- src/backends/neon/NeonBackend.cpp
- src/backends/neon/NeonBackend.hpp
- src/backends/neon/NeonInterceptorScheduler.cpp
- src/backends/neon/NeonInterceptorScheduler.hpp
- src/backends/neon/workloads/NeonBatchMatMulWorkload.cpp
- src/backends/neon/workloads/NeonBatchMatMulWorkload.hpp
- src/backends/neon/workloads/NeonQLstmWorkload.cpp
- src/backends/reference/RefBackend.cpp
- src/backends/reference/RefBackend.hpp
updated: '2026-11-14'
commit: 2b61cecc9df7a43fca1463795062cf359e6be820
linked_docs:
- 2.2-backend-system
- 4.2-neon-backend
- 6.1-build-system
- 7-advanced-topics
- 7.2-workload-system
- 2.3-runtime-and-execution
bridge_symbols:
- OptimizeSubgraphView
- OptimizeSubgraphView
- BatchMatMulTestImpl
- ClQLstmWorkloadValidate
- NeonQLstmWorkloadValidate
- FuseLayer
---

# Compute Backends

<details>
<summary>Relevant source files</summary>

The following files were used as context for generating this wiki page:

- [delegate/test/BatchMatMulTest.cpp](delegate/test/BatchMatMulTest.cpp)
- [include/armnn/backends/IBackendInternal.hpp](include/armnn/backends/IBackendInternal.hpp)
- [scripts/get_compute_library.sh](scripts/get_compute_library.sh)
- [src/backends/aclCommon/ArmComputeSubgraphUtils.hpp](src/backends/aclCommon/ArmComputeSubgraphUtils.hpp)
- [src/backends/backendsCommon/IBackendInternal.cpp](src/backends/backendsCommon/IBackendInternal.cpp)
- [src/backends/backendsCommon/test/CompatibilityTests.cpp](src/backends/backendsCommon/test/CompatibilityTests.cpp)
- [src/backends/backendsCommon/test/JsonPrinterTestImpl.cpp](src/backends/backendsCommon/test/JsonPrinterTestImpl.cpp)
- [src/backends/backendsCommon/test/layerTests/BatchMatMulTestImpl.cpp](src/backends/backendsCommon/test/layerTests/BatchMatMulTestImpl.cpp)
- [src/backends/cl/ClBackend.cpp](src/backends/cl/ClBackend.cpp)
- [src/backends/cl/ClBackend.hpp](src/backends/cl/ClBackend.hpp)
- [src/backends/cl/workloads/ClBatchMatMulWorkload.cpp](src/backends/cl/workloads/ClBatchMatMulWorkload.cpp)
- [src/backends/cl/workloads/ClBatchMatMulWorkload.hpp](src/backends/cl/workloads/ClBatchMatMulWorkload.hpp)
- [src/backends/cl/workloads/ClQLstmWorkload.cpp](src/backends/cl/workloads/ClQLstmWorkload.cpp)
- [src/backends/neon/NeonBackend.cpp](src/backends/neon/NeonBackend.cpp)
- [src/backends/neon/NeonBackend.hpp](src/backends/neon/NeonBackend.hpp)
- [src/backends/neon/NeonInterceptorScheduler.cpp](src/backends/neon/NeonInterceptorScheduler.cpp)
- [src/backends/neon/NeonInterceptorScheduler.hpp](src/backends/neon/NeonInterceptorScheduler.hpp)
- [src/backends/neon/workloads/NeonBatchMatMulWorkload.cpp](src/backends/neon/workloads/NeonBatchMatMulWorkload.cpp)
- [src/backends/neon/workloads/NeonBatchMatMulWorkload.hpp](src/backends/neon/workloads/NeonBatchMatMulWorkload.hpp)
- [src/backends/neon/workloads/NeonQLstmWorkload.cpp](src/backends/neon/workloads/NeonQLstmWorkload.cpp)
- [src/backends/reference/RefBackend.cpp](src/backends/reference/RefBackend.cpp)
- [src/backends/reference/RefBackend.hpp](src/backends/reference/RefBackend.hpp)

</details>



This document covers ArmNN's compute backend system, which provides hardware acceleration and execution implementations for neural network operations. The backend system enables ArmNN to execute models on different compute devices including CPU reference implementations, ARM NEON accelerated CPU operations, GPU acceleration via OpenCL, and reference implementations for emerging standards like TOSA.

For information about the core network and graph representation that backends operate on, see [[2.1-network-and-graph-system|Network and Graph System]]. For details about runtime execution and workload management, see [[2.3-runtime-and-execution|Runtime and Execution]].

## Backend Architecture Overview

ArmNN implements a pluggable backend architecture where each compute backend provides implementations for specific hardware or execution environments. The system is built around the `IBackendInternal` interface, which defines the contract that all backends must implement.

### Backend Interface Hierarchy

```mermaid
graph TD
    IBackend["IBackend<br/>Base Interface"]
    IBackendInternal["IBackendInternal<br/>Core Backend Interface"]
    
    RefBackend["RefBackend<br/>CPU Reference"]
    NeonBackend["NeonBackend<br/>ARM CPU Acceleration"]
    ClBackend["ClBackend<br/>GPU OpenCL"]
    TosaBackend["TosaRefBackend<br/>TOSA Reference"]
    
    IBackend --> IBackendInternal
    IBackendInternal --> RefBackend
    IBackendInternal --> NeonBackend
    IBackendInternal --> ClBackend
    IBackendInternal --> TosaBackend
    
    BackendRegistry["BackendRegistry<br/>Backend Discovery"]
    BackendRegistry --> RefBackend
    BackendRegistry --> NeonBackend
    BackendRegistry --> ClBackend
```

**Sources:** [include/armnn/backends/IBackendInternal.hpp:75-212](), [src/backends/reference/RefBackend.hpp:30-67](), [src/backends/neon/NeonBackend.hpp:29-74](), [src/backends/cl/ClBackend.hpp:24-285]()

### Core Backend Components

Each backend implementation provides several key components that integrate with the ArmNN framework:

```mermaid
graph TB
    subgraph "Backend Implementation"
        Backend["Backend Class<br/>(RefBackend, NeonBackend, ClBackend)"]
        WorkloadFactory["IWorkloadFactory<br/>Creates Operation Workloads"]
        LayerSupport["ILayerSupport<br/>Capability Queries"]
        MemoryManager["IMemoryManager<br/>Memory Allocation"]
        TensorHandleFactory["ITensorHandleFactory<br/>Tensor Management"]
    end
    
    subgraph "Backend Services"
        BackendContext["IBackendContext<br/>Runtime Context"]
        ModelContext["IBackendSpecificModelContext<br/>Model-Specific Config"]
        ProfilingContext["IBackendProfilingContext<br/>Performance Monitoring"]
    end
    
    Backend --> WorkloadFactory
    Backend --> LayerSupport
    Backend --> MemoryManager
    Backend --> TensorHandleFactory
    Backend --> BackendContext
    Backend --> ModelContext
    Backend --> ProfilingContext
```

**Sources:** [include/armnn/backends/IBackendInternal.hpp:87-98](), [src/backends/backendsCommon/IBackendInternal.cpp:13-147]()

## ARM Compute Library Integration

The NEON and OpenCL backends leverage the ARM Compute Library (ACL) for optimized kernel implementations. The system includes dependency management for ACL versions:

### ACL Dependency Management

The [scripts/get_compute_library.sh:1-112]() script manages ACL dependency versions:

- **Default ACL Version:** Pinned to specific SHA: `7d6fc756b2a9dfd8776be1c5c17ba45e2652c9fc`
- **Repository Source:** ML Platform server at `https://review.mlplatform.org/ml/ComputeLibrary`
- **Version Synchronization:** ACL version is synchronized with ArmNN releases to ensure compatibility

```mermaid
graph LR
    ArmNN["ArmNN Build System"]
    GetCLScript["get_compute_library.sh<br/>ACL Version Management"]
    MLPlatform["ML Platform Server<br/>ACL Repository"]
    CLFramework["clframework/<br/>Local ACL Build"]
    
    ArmNN --> GetCLScript
    GetCLScript --> MLPlatform
    MLPlatform --> CLFramework
    
    NeonBackend["NEON Backend"] --> CLFramework
    ClBackend["OpenCL Backend"] --> CLFramework
```

**Sources:** [scripts/get_compute_library.sh:9-20](), [scripts/get_compute_library.sh:80-94]()

## Backend Capabilities System

Each backend reports its capabilities through the `BackendCapabilities` system, which enables runtime capability queries and optimization decisions:

| Capability | Reference | NEON | OpenCL | Description |
|------------|-----------|------|--------|-------------|
| `NonConstWeights` | ✓ | ✓ | ✓ | Support for non-constant weight tensors |
| `ProtectedContentAllocation` | ✗ | ✗ | ✓ | Protected memory allocation support |
| `ConstantTensorsAsInputs` | ✓ | ✓ | ✓ | Constant tensors as layer inputs |
| `PreImportIOTensors` | ✓ | ✗ | ✗ | Pre-import input/output tensors |
| `ExternallyManagedMemory` | ✓ | ✓ | ✓ | External memory management |
| `MultiAxisPacking` | ✗ | ✗ | ✗ | Multi-axis tensor packing |
| `SingleAxisPacking` | ✓ | ✓ | ✓ | Single-axis tensor packing |
| `HasFp16` | ✓ | Dynamic | Dynamic | Half-precision floating point support |

**Sources:** [src/backends/reference/RefBackend.hpp:12-23](), [src/backends/neon/NeonBackend.hpp:15-26](), [src/backends/cl/ClBackend.cpp:276-290]()

## Workload System Architecture

Backends implement operations through workloads, which encapsulate the execution logic for specific layer types. The workload system provides a consistent interface across different backend implementations:

### Workload Creation Flow

```mermaid
graph TD
    LayerType["Layer Type<br/>(e.g., BatchMatMul)"]
    WorkloadFactory["Backend WorkloadFactory<br/>(RefWorkloadFactory, NeonWorkloadFactory, ClWorkloadFactory)"]
    QueueDescriptor["QueueDescriptor<br/>(BatchMatMulQueueDescriptor)"]
    Workload["Backend Workload<br/>(RefBatchMatMulWorkload, NeonBatchMatMulWorkload, ClBatchMatMulWorkload)"]
    
    LayerType --> WorkloadFactory
    WorkloadFactory --> QueueDescriptor
    QueueDescriptor --> Workload
    
    subgraph "Workload Execution"
        Execute["Execute() Method"]
        ACLFunction["ARM Compute Library Function<br/>(NEMatMul, CLMatMul)"]
        RefImpl["Reference Implementation"]
    end
    
    Workload --> Execute
    Execute --> ACLFunction
    Execute --> RefImpl
```

**Sources:** [src/backends/cl/workloads/ClBatchMatMulWorkload.cpp:57-113](), [src/backends/neon/workloads/NeonBatchMatMulWorkload.cpp:57-107]()

### Backend-Specific Optimizations

Each backend implements the `OptimizeSubgraphView` method to perform backend-specific graph optimizations:

```mermaid
graph TB
    SubgraphView["SubgraphView<br/>Input Graph Partition"]
    
    subgraph "NEON Backend Optimizations"
        ActivationFusion["Activation Fusion<br/>Fuse activation into convolution/FC"]
        ReduceChaining["Reduce Layer Chaining<br/>Multi-axis reduction optimization"]
        ReshapeRemoval["Reshape Removal<br/>Remove unnecessary reshapes"]
    end
    
    subgraph "OpenCL Backend Optimizations"
        CLActivationFusion["Activation Fusion<br/>GPU-specific fusion patterns"]
        CLReduceChaining["Reduce Chaining<br/>GPU reduce optimizations"]
    end
    
    subgraph "Reference Backend Optimizations"
        PadFusion["Pad Fusion<br/>Fold padding into pooling operations"]
        RefReshapeRemoval["Reshape Removal<br/>Remove redundant reshapes"]
    end
    
    OptimizationViews["OptimizationViews<br/>Optimized Graph Output"]
    
    SubgraphView --> ActivationFusion
    SubgraphView --> CLActivationFusion
    SubgraphView --> PadFusion
    
    ActivationFusion --> OptimizationViews
    CLActivationFusion --> OptimizationViews
    PadFusion --> OptimizationViews
```

**Sources:** [src/backends/neon/NeonBackend.cpp:144-622](), [src/backends/cl/ClBackend.cpp:292-659](), [src/backends/reference/RefBackend.cpp:72-136]()

## Memory Management and Tensor Handles

Each backend provides memory management through specialized memory managers and tensor handle factories:

### Memory Manager Hierarchy

```mermaid
graph TD
    IMemoryManager["IMemoryManager<br/>Base Interface"]
    
    RefMemoryManager["RefMemoryManager<br/>CPU Reference Memory"]
    NeonMemoryManager["NeonMemoryManager<br/>ACL Allocator Integration"]
    ClMemoryManager["ClMemoryManager<br/>OpenCL Buffer Management"]
    
    IMemoryManager --> RefMemoryManager
    IMemoryManager --> NeonMemoryManager
    IMemoryManager --> ClMemoryManager
    
    subgraph "Allocators"
        DefaultAllocator["DefaultAllocator<br/>Standard malloc/free"]
        ACLAllocator["arm_compute::Allocator<br/>ACL Memory Management"]
        CLBufferAllocator["arm_compute::CLBufferAllocator<br/>OpenCL Buffer Allocation"]
        CustomAllocator["ICustomAllocator<br/>User-Provided Allocator"]
    end
    
    RefMemoryManager --> DefaultAllocator
    NeonMemoryManager --> ACLAllocator
    ClMemoryManager --> CLBufferAllocator
    ClMemoryManager --> CustomAllocator
```

**Sources:** [src/backends/neon/NeonBackend.cpp:52-56](), [src/backends/cl/ClBackend.cpp:50-57](), [src/backends/reference/RefBackend.cpp:61-64]()

### Custom Memory Allocator Support

The OpenCL backend supports custom memory allocators through the `ClBackendCustomAllocatorWrapper` class, enabling integration with DMA buffers and protected memory:

**Supported Memory Sources:**
- `MemorySource::Malloc` - Standard heap allocation
- `MemorySource::DmaBuf` - DMA buffer file descriptors  
- `MemorySource::DmaBufProtected` - Protected DMA buffers

**Sources:** [src/backends/cl/ClBackend.hpp:97-211](), [src/backends/cl/ClBackend.hpp:213-281]()

## Profiling Integration

Backends integrate with ArmNN's profiling system through interceptor schedulers and profiling contexts:

### NEON Profiling Architecture

```mermaid
graph LR
    Scheduler["arm_compute::IScheduler<br/>ACL Default Scheduler"]
    Interceptor["NeonInterceptorScheduler<br/>Profiling Wrapper"]
    KernelTimer["NeonTimer::KernelMeasurements<br/>Performance Data"]
    
    Scheduler --> Interceptor
    Interceptor --> KernelTimer
    
    subgraph "Intercepted Methods"
        Schedule["schedule()<br/>Individual Kernel Execution"]
        RunWorkloads["run_workloads()<br/>Batch Execution"]
        ScheduleOp["schedule_op()<br/>Operator Scheduling"]
    end
    
    Interceptor --> Schedule
    Interceptor --> RunWorkloads
    Interceptor --> ScheduleOp
```

**Sources:** [src/backends/neon/NeonInterceptorScheduler.hpp:17-44](), [src/backends/neon/NeonInterceptorScheduler.cpp:25-67]()

## Backend Registration and Discovery

Backends are registered with the ArmNN runtime through the backend registry system, enabling dynamic backend discovery and selection:

```mermaid
graph TB
    BackendRegistry["BackendRegistry<br/>Global Backend Discovery"]
    
    subgraph "Backend Registration"
        RefRegistration["Reference Backend<br/>Always Available"]
        NeonRegistration["NEON Backend<br/>Conditional on ARM CPU"]
        ClRegistration["OpenCL Backend<br/>Conditional on OpenCL Support"]
        TosaRegistration["TOSA Backend<br/>Reference Implementation"]
    end
    
    subgraph "Runtime Integration"
        IRuntime["IRuntime<br/>Network Execution"]
        LoadedNetwork["LoadedNetwork<br/>Backend Assignment"]
        Optimization["armnn::Optimize<br/>Backend Selection"]
    end
    
    BackendRegistry --> RefRegistration
    BackendRegistry --> NeonRegistration
    BackendRegistry --> ClRegistration
    BackendRegistry --> TosaRegistration
    
    IRuntime --> LoadedNetwork
    Optimization --> LoadedNetwork
    LoadedNetwork --> BackendRegistry
```

**Sources:** [src/backends/backendsCommon/test/CompatibilityTests.cpp:31-44](), [src/backends/backendsCommon/test/CompatibilityTests.cpp:152-210]()

## Related Wiki Pages

- [[4.1-reference-backend|Reference Backend]]
- [[4.2-neon-backend|NEON Backend]]
- [[4.3-opencl-backend|OpenCL Backend]]
- [[4.4-tosa-backend|TOSA Backend]]
- [[2.1-network-and-graph-system|Network and Graph System]]
- [[2.3-runtime-and-execution|Runtime and Execution]]


## Dynamic Knowledge Links (Code Graph ↔ LLM-Wiki / RAG)

### Linked Architecture & Design Documents

| Document | Match Channel | Score | Shared Code Symbols |
|---|---|---|---|
| [[2.2-backend-system|2.2 Backend System]] | `bm25+entity(5)` | `79.797` | `AreParenthesesMatching`, `BatchMatMulTestImpl`, `ExtractMeasurements`, `FuseConvolution2dLayer`, `FuseLayer` |
| [[4.2-neon-backend|4.2 NEON Backend]] | `bm25+entity(5)` | `60.116` | `AreParenthesesMatching`, `BatchMatMulTestImpl`, `ClBatchMatMulWorkload`, `ExtractMeasurements`, `GetSoftmaxProfilerJson` |
| [[6.1-build-system|6.1 Build System]] | `bm25+entity(5)` | `57.171` | `AreParenthesesMatching`, `BatchMatMulTestImpl`, `ClBatchMatMulWorkload`, `ClQLstmWorkloadValidate`, `GetSoftmaxProfilerJson` |
| [[7-advanced-topics|7 Advanced Topics]] | `bm25+entity(6)` | `57.008` | `AreParenthesesMatching`, `BatchMatMulTestImpl`, `ExtractMeasurements`, `GetSoftmaxProfilerJson`, `ValidateProfilerJson` |
| [[7.2-workload-system|7.2 Workload System]] | `bm25+entity(4)` | `54.919` | `AreParenthesesMatching`, `BatchMatMulTestImpl`, `ExtractMeasurements`, `GetSoftmaxProfilerJson` |
| [[2.3-runtime-and-execution|2.3 Runtime and Execution]] | `wikilink:2.2-backend-system` | `36.149` | *(lexical/graph match)* |

### High-Centrality Bridge Symbols (CBM Graph)

| Symbol | Kind | Source Location | Fan-In / Fan-Out |
|---|---|---|---|
| `OptimizeSubgraphView` | Method | [src/backends/neon/NeonBackend.cpp:140-618]() | in: `0` / out: `53` |
| `OptimizeSubgraphView` | Method | [src/backends/cl/ClBackend.cpp:292-729]() | in: `0` / out: `49` |
| `BatchMatMulTestImpl` | Function | [src/backends/backendsCommon/test/layerTests/BatchMatMulTestImpl.cpp:20-80]() | in: `13` / out: `16` |
| `ClQLstmWorkloadValidate` | Function | [src/backends/cl/workloads/ClQLstmWorkload.cpp:247-395]() | in: `0` / out: `22` |
| `NeonQLstmWorkloadValidate` | Function | [src/backends/neon/workloads/NeonQLstmWorkload.cpp:243-391]() | in: `0` / out: `22` |
| `FuseLayer` | Function | [src/backends/aclCommon/ArmComputeSubgraphUtils.hpp:52-70]() | in: `9` / out: `3` |

Sources: [src/backends/neon/NeonBackend.cpp:140-618](), [src/backends/cl/ClBackend.cpp:292-729](), [src/backends/backendsCommon/test/layerTests/BatchMatMulTestImpl.cpp:20-80](), [src/backends/cl/workloads/ClQLstmWorkload.cpp:247-395]()

### Cross-Subsystem Coupling

- [[2-core-architecture|2 Core Architecture]] — call/import coupling weight `111.0`
- [[2.1-network-and-graph-system|2.1 Network and Graph System]] — call/import coupling weight `111.0`
- [[1-armnn-overview|1 ArmNN Overview]] — call/import coupling weight `26.0`
- [[3.3-model-serialization|3.3 Model Serialization]] — call/import coupling weight `19.0`
- [[2.3-runtime-and-execution|2.3 Runtime and Execution]] — call/import coupling weight `14.0`
- [[4.2-neon-backend|4.2 NEON Backend]] — call/import coupling weight `12.0`
