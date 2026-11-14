---
id: 2-core-architecture
section_id: '2'
title: 2 Core Architecture
parent: null
order: 30
type: section
source_url: https://github.com/ARM-software/armnn/blob/branches/armnn_24_11
sources:
- Android.mk
- include/armnn/INetwork.hpp
- include/armnn/backends/OptimizationViews.hpp
- include/armnn/backends/SubgraphView.hpp
- include/armnn/backends/WorkloadFactory.hpp
- include/armnnTestUtils/MockBackend.hpp
- src/armnn/Graph.cpp
- src/armnn/Graph.hpp
- src/armnn/InternalTypes.hpp
- src/armnn/Layer.cpp
- src/armnn/Layer.hpp
- src/armnn/LayersFwd.hpp
- src/armnn/Network.cpp
- src/armnn/Network.hpp
- src/armnn/SubgraphView.cpp
- src/armnn/SubgraphViewSelector.cpp
- src/armnn/SubgraphViewSelector.hpp
- src/armnn/layers/LayerWithParameters.hpp
- src/armnn/test/GraphTests.cpp
- src/armnn/test/SubgraphViewTests.cpp
- src/armnnTestUtils/MockBackend.cpp
- src/backends/backendsCommon/LayerSupportBase.cpp
- src/backends/backendsCommon/LayerSupportBase.hpp
- src/backends/backendsCommon/WorkloadFactory.cpp
- src/backends/backendsCommon/test/IsLayerSupportedTestImpl.hpp
- src/backends/backendsCommon/test/OptimizationViewsTests.cpp
- src/backends/backendsCommon/test/OptimizeSubgraphViewTests.cpp
- src/backends/backendsCommon/test/mockBackend/MockImportBackend.cpp
- src/backends/reference/test/RefMemCopyTests.cpp
updated: '2026-11-14'
commit: 2b61cecc9df7a43fca1463795062cf359e6be820
linked_docs:
- 2.1-network-and-graph-system
- 1-armnn-overview
- 2.3-runtime-and-execution
- 3.3-model-serialization
- 5.2-tensorflow-lite-delegate
- 2.2-backend-system
bridge_symbols:
- SetTensorInfo
- Connect
- CreateWorkload
- end
- GetName
- GetInputSlot
---

# Core Architecture

<details>
<summary>Relevant source files</summary>

The following files were used as context for generating this wiki page:

- [Android.mk](Android.mk)
- [include/armnn/INetwork.hpp](include/armnn/INetwork.hpp)
- [include/armnn/backends/OptimizationViews.hpp](include/armnn/backends/OptimizationViews.hpp)
- [include/armnn/backends/SubgraphView.hpp](include/armnn/backends/SubgraphView.hpp)
- [include/armnn/backends/WorkloadFactory.hpp](include/armnn/backends/WorkloadFactory.hpp)
- [include/armnnTestUtils/MockBackend.hpp](include/armnnTestUtils/MockBackend.hpp)
- [src/armnn/Graph.cpp](src/armnn/Graph.cpp)
- [src/armnn/Graph.hpp](src/armnn/Graph.hpp)
- [src/armnn/InternalTypes.hpp](src/armnn/InternalTypes.hpp)
- [src/armnn/Layer.cpp](src/armnn/Layer.cpp)
- [src/armnn/Layer.hpp](src/armnn/Layer.hpp)
- [src/armnn/LayersFwd.hpp](src/armnn/LayersFwd.hpp)
- [src/armnn/Network.cpp](src/armnn/Network.cpp)
- [src/armnn/Network.hpp](src/armnn/Network.hpp)
- [src/armnn/SubgraphView.cpp](src/armnn/SubgraphView.cpp)
- [src/armnn/SubgraphViewSelector.cpp](src/armnn/SubgraphViewSelector.cpp)
- [src/armnn/SubgraphViewSelector.hpp](src/armnn/SubgraphViewSelector.hpp)
- [src/armnn/layers/LayerWithParameters.hpp](src/armnn/layers/LayerWithParameters.hpp)
- [src/armnn/test/GraphTests.cpp](src/armnn/test/GraphTests.cpp)
- [src/armnn/test/SubgraphViewTests.cpp](src/armnn/test/SubgraphViewTests.cpp)
- [src/armnnTestUtils/MockBackend.cpp](src/armnnTestUtils/MockBackend.cpp)
- [src/backends/backendsCommon/LayerSupportBase.cpp](src/backends/backendsCommon/LayerSupportBase.cpp)
- [src/backends/backendsCommon/LayerSupportBase.hpp](src/backends/backendsCommon/LayerSupportBase.hpp)
- [src/backends/backendsCommon/WorkloadFactory.cpp](src/backends/backendsCommon/WorkloadFactory.cpp)
- [src/backends/backendsCommon/test/IsLayerSupportedTestImpl.hpp](src/backends/backendsCommon/test/IsLayerSupportedTestImpl.hpp)
- [src/backends/backendsCommon/test/OptimizationViewsTests.cpp](src/backends/backendsCommon/test/OptimizationViewsTests.cpp)
- [src/backends/backendsCommon/test/OptimizeSubgraphViewTests.cpp](src/backends/backendsCommon/test/OptimizeSubgraphViewTests.cpp)
- [src/backends/backendsCommon/test/mockBackend/MockImportBackend.cpp](src/backends/backendsCommon/test/mockBackend/MockImportBackend.cpp)
- [src/backends/reference/test/RefMemCopyTests.cpp](src/backends/reference/test/RefMemCopyTests.cpp)

</details>



This document provides a high-level overview of ArmNN's system architecture, covering the core components, design principles, and interaction patterns that form the foundation of the machine learning inference engine. For information about specific model format support, see [[3-model-support|Model Support]]. For details about individual compute backends, see [[4-compute-backends|Compute Backends]]. For runtime execution specifics, see [[2.3-runtime-and-execution|Runtime and Execution]].

## System Overview

ArmNN is designed as a modular inference engine that abstracts machine learning models into computational graphs and executes them across heterogeneous compute backends. The architecture follows a clear separation between model representation (`INetwork`/`Graph`), optimization (`Optimize`), and execution (`IRuntime`/`LoadedNetwork`).

### High-Level Architecture

```mermaid
graph TB
    subgraph "Model Import Layer"
        TfLiteParser["TfLiteParser"]
        OnnxParser["OnnxParser"] 
        Deserializer["Deserializer"]
    end
    
    subgraph "Core Framework"
        INetwork["INetwork<br/>Graph Builder Interface"]
        NetworkImpl["NetworkImpl<br/>Concrete Implementation"]
        Graph["Graph<br/>Computational Graph"]
        Layer["Layer Hierarchy<br/>50+ Layer Types"]
    end
    
    subgraph "Optimization Engine"
        Optimize["armnn::Optimize<br/>Backend Assignment"]
        SubgraphView["SubgraphView<br/>Graph Partitioning"]
        OptimizedNetwork["IOptimizedNetwork<br/>Execution Ready"]
    end
    
    subgraph "Runtime Execution"
        IRuntime["IRuntime<br/>Network Loading"]
        LoadedNetwork["LoadedNetwork<br/>Backend Workloads"]
        BackendRegistry["BackendRegistry<br/>Plugin Management"]
    end
    
    subgraph "Backend System"
        IBackendInternal["IBackendInternal<br/>Backend Interface"]
        IWorkloadFactory["IWorkloadFactory<br/>Workload Creation"]
        ILayerSupport["ILayerSupport<br/>Capability Query"]
    end
    
    TfLiteParser --> INetwork
    OnnxParser --> INetwork
    Deserializer --> INetwork
    
    INetwork --> NetworkImpl
    NetworkImpl --> Graph
    Graph --> Layer
    
    INetwork --> Optimize
    Optimize --> SubgraphView
    SubgraphView --> OptimizedNetwork
    
    OptimizedNetwork --> IRuntime
    IRuntime --> LoadedNetwork
    LoadedNetwork --> BackendRegistry
    
    BackendRegistry --> IBackendInternal
    IBackendInternal --> IWorkloadFactory
    IBackendInternal --> ILayerSupport
    
    style INetwork fill:#e1f5fe
    style Graph fill:#e8f5e8
    style LoadedNetwork fill:#fff3e0
```

**Sources:** [src/armnn/Network.cpp:45-689](), [src/armnn/Graph.hpp:30-97](), [include/armnn/INetwork.hpp:345-347](), [src/armnn/Network.hpp:32-261]()

## Core Components

### INetwork and NetworkImpl

The `INetwork` interface serves as the primary entry point for building computational graphs. It provides a factory pattern for creating layers and maintains the graph structure through its implementation `NetworkImpl`.

```mermaid
classDiagram
    class INetwork {
        +AddInputLayer(id, name) IConnectableLayer*
        +AddConvolution2dLayer(desc, name) IConnectableLayer*
        +AddOutputLayer(id, name) IConnectableLayer*
        +Create(options) INetworkPtr
        +PrintGraph() Status
    }
    
    class NetworkImpl {
        -m_Graph unique_ptr~Graph~
        -m_NetworkOptions NetworkOptions
        +GetGraph() Graph&
        +AddInputLayer() IConnectableLayer*
        +AddActivationLayer() IConnectableLayer*
    }
    
    class Graph {
        -m_Layers LayerList
        -m_LayersInOrder bool
        +AddLayer~LayerT~() LayerT*
        +TopologicalSort() Graph&
        +ForEachLayer(func) void
    }
    
    class IConnectableLayer {
        +GetName() char*
        +GetNumInputSlots() unsigned int
        +GetNumOutputSlots() unsigned int
        +GetInputSlot(index) IInputSlot&
        +GetOutputSlot(index) IOutputSlot&
    }
    
    INetwork --> NetworkImpl : "pNetworkImpl"
    NetworkImpl --> Graph : "m_Graph"
    Graph --> IConnectableLayer : "contains"
```

**Sources:** [include/armnn/INetwork.hpp:345-352](), [src/armnn/Network.hpp:32-261](), [src/armnn/Network.cpp:45-47](), [src/armnn/Graph.hpp:30-148]()

### Graph and Layer System

The `Graph` class manages the computational graph structure, maintaining layers in topological order and providing iteration capabilities. Layers inherit from the `Layer` base class, which implements the `IConnectableLayer` interface.

```mermaid
graph TD
    subgraph "Graph Management"
        Graph["Graph<br/>-m_Layers: LayerList<br/>-m_LayersInOrder: bool"]
        LayerList["std::list&lt;Layer*&gt;<br/>Topologically Ordered"]
    end
    
    subgraph "Layer Hierarchy"
        Layer["Layer<br/>Base Implementation"]
        IConnectableLayer["IConnectableLayer<br/>Public Interface"]
        InputLayer["InputLayer"]
        Convolution2dLayer["Convolution2dLayer"]
        OutputLayer["OutputLayer"]
        LayerWithParameters["LayerWithParameters&lt;T&gt;<br/>Template for Parameterized Layers"]
    end
    
    subgraph "Connection System"
        InputSlot["InputSlot<br/>-m_Connection: OutputSlot*<br/>-m_SlotIndex: unsigned int"]
        OutputSlot["OutputSlot<br/>-m_Connections: vector&lt;InputSlot*&gt;<br/>-m_OutputHandler: OutputHandler&"]
        IInputSlot["IInputSlot<br/>Interface"]
        IOutputSlot["IOutputSlot<br/>Interface"]
    end
    
    Graph --> LayerList
    LayerList --> Layer
    
    Layer --> IConnectableLayer
    InputLayer --> Layer
    Convolution2dLayer --> LayerWithParameters
    LayerWithParameters --> Layer
    OutputLayer --> Layer
    
    Layer --> InputSlot
    Layer --> OutputSlot
    InputSlot --> IInputSlot
    OutputSlot --> IOutputSlot
    
    OutputSlot --> InputSlot : "connects to"
```

**Sources:** [src/armnn/Graph.hpp:50-197](), [src/armnn/Layer.hpp:42-284](), [src/armnn/LayersFwd.hpp:1-143](), [src/armnn/layers/LayerWithParameters.hpp:13-42]()

## Backend Architecture

ArmNN uses a plugin-based backend system where each backend implements the `IBackendInternal` interface. Backends provide workload factories for layer execution and layer support queries for optimization.

```mermaid
graph TB
    subgraph "Backend Registry"
        BackendRegistry["BackendRegistry<br/>Plugin Management"]
        BackendFactory["BackendFactory<br/>Backend Creation"]
    end
    
    subgraph "Backend Interface"
        IBackendInternal["IBackendInternal<br/>Backend Contract"]
        IWorkloadFactory["IWorkloadFactory<br/>Workload Creation"]
        ILayerSupport["ILayerSupport<br/>Capability Query"]
        IMemoryManager["IMemoryManager<br/>Memory Management"]
    end
    
    subgraph "Concrete Backends"
        RefBackend["RefBackend<br/>CPU Reference"]
        NeonBackend["NeonBackend<br/>ARM NEON"]
        ClBackend["ClBackend<br/>OpenCL GPU"]
        TosaBackend["TosaBackend<br/>TOSA Reference"]
    end
    
    subgraph "Workload System"
        IWorkload["IWorkload<br/>Execution Unit"]
        RefWorkloads["RefXxxWorkload<br/>Reference Implementations"]
        NeonWorkloads["NeonXxxWorkload<br/>NEON Optimized"]
        ClWorkloads["ClXxxWorkload<br/>GPU Kernels"]
    end
    
    BackendRegistry --> BackendFactory
    BackendFactory --> IBackendInternal
    
    IBackendInternal --> IWorkloadFactory
    IBackendInternal --> ILayerSupport
    IBackendInternal --> IMemoryManager
    
    RefBackend --> IBackendInternal
    NeonBackend --> IBackendInternal
    ClBackend --> IBackendInternal
    TosaBackend --> IBackendInternal
    
    IWorkloadFactory --> IWorkload
    RefWorkloads --> IWorkload
    NeonWorkloads --> IWorkload
    ClWorkloads --> IWorkload
```

**Sources:** [src/backends/backendsCommon/WorkloadFactory.cpp:70-95](), [src/backends/backendsCommon/LayerSupportBase.hpp:13-64](), [include/armnn/backends/WorkloadFactory.hpp:22-136]()

## Network Lifecycle

The ArmNN architecture supports a clear pipeline from model construction to execution, with distinct phases for building, optimization, and runtime execution.

### Construction to Execution Pipeline

```mermaid
flowchart TD
    subgraph "Construction Phase"
        ModelFile["Model File<br/>.tflite, .onnx, .armnn"]
        Parser["Parser<br/>TfLiteParser, OnnxParser"]
        INetwork["INetwork<br/>Graph Builder"]
        NetworkImpl["NetworkImpl<br/>Graph Container"]
    end
    
    subgraph "Optimization Phase"
        OptimizeFunc["armnn::Optimize<br/>Backend Assignment"]
        SubgraphView["SubgraphView<br/>Graph Partitioning"]
        BackendAssignment["Backend Assignment<br/>Layer -> Backend Mapping"]
        OptimizedNetwork["IOptimizedNetwork<br/>Execution Ready"]
    end
    
    subgraph "Runtime Phase"
        IRuntime["IRuntime<br/>Network Loader"]
        LoadedNetwork["LoadedNetwork<br/>Backend Workloads"]
        Workloads["Workload Execution<br/>Backend-Specific Kernels"]
    end
    
    ModelFile --> Parser
    Parser --> INetwork
    INetwork --> NetworkImpl
    
    NetworkImpl --> OptimizeFunc
    OptimizeFunc --> SubgraphView
    SubgraphView --> BackendAssignment
    BackendAssignment --> OptimizedNetwork
    
    OptimizedNetwork --> IRuntime
    IRuntime --> LoadedNetwork
    LoadedNetwork --> Workloads
    
    style OptimizeFunc fill:#e1f5fe
    style LoadedNetwork fill:#e8f5e8
```

**Sources:** [src/armnn/Network.cpp:844-1077](), [src/armnn/SubgraphView.cpp:48-57](), [src/armnn/SubgraphViewSelector.cpp:24-42]()

## Design Patterns and Principles

### Interface Segregation and Abstraction

ArmNN employs extensive interface segregation to separate concerns:

- **`INetwork`/`IOptimizedNetwork`**: Public interfaces for graph building and optimized representations
- **`IConnectableLayer`/`IInputSlot`/`IOutputSlot`**: Abstraction over internal layer implementations
- **`IBackendInternal`/`IWorkloadFactory`/`ILayerSupport`**: Backend plugin interfaces
- **`IRuntime`**: Runtime execution interface

### Template-Based Layer System

Layers with parameters use a template-based approach for type safety:

```mermaid
classDiagram
    class LayerWithParameters~Parameters~ {
        -m_Param Parameters
        +GetParameters() Parameters&
        +SerializeLayerParameters() void
    }
    
    class Convolution2dLayer {
        +DescriptorType Convolution2dDescriptor
        +CreateWorkload() unique_ptr~IWorkload~
    }
    
    class BatchNormalizationLayer {
        +DescriptorType BatchNormalizationDescriptor  
        +m_Mean unique_ptr~ScopedTensorHandle~
        +m_Variance unique_ptr~ScopedTensorHandle~
    }
    
    LayerWithParameters --> Convolution2dLayer
    LayerWithParameters --> BatchNormalizationLayer
```

**Sources:** [src/armnn/layers/LayerWithParameters.hpp:13-62](), [src/backends/backendsCommon/test/IsLayerSupportedTestImpl.hpp:49-80]()

### Graph Modification and Optimization

The architecture supports dynamic graph modification through:

- **Subgraph Views**: Partition graphs for backend-specific optimization
- **Layer Insertion**: Insert compatibility layers (MemCopy, MemImport) between backends  
- **Graph Substitution**: Replace subgraphs with optimized implementations

```mermaid
sequenceDiagram
    participant Graph
    participant SubgraphView  
    participant Backend
    participant OptimizedNetwork
    
    Graph->>SubgraphView: Create partitions
    SubgraphView->>Backend: Query layer support
    Backend->>SubgraphView: Return capabilities
    SubgraphView->>Graph: Insert compatibility layers
    Graph->>OptimizedNetwork: Generate execution graph
```

**Sources:** [src/armnn/Graph.cpp:330-473](), [src/armnn/SubgraphView.cpp:604-671](), [src/armnn/SubgraphViewSelector.cpp:170-298]()

This architecture provides ArmNN with the flexibility to support multiple model formats, optimize for diverse hardware backends, and maintain a clean separation between graph representation and execution concerns.

## Related Wiki Pages

- [[2.1-network-and-graph-system|Network and Graph System]]
- [[2.2-backend-system|Backend System]]
- [[2.3-runtime-and-execution|Runtime and Execution]]
- [[3-model-support|Model Support]]
- [[4-compute-backends|Compute Backends]]


## Dynamic Knowledge Links (Code Graph ↔ LLM-Wiki / RAG)

### Linked Architecture & Design Documents

| Document | Match Channel | Score | Shared Code Symbols |
|---|---|---|---|
| [[2.1-network-and-graph-system|2.1 Network and Graph System]] | `bm25+entity(8)` | `54.799` | `Connect`, `EraseLayer`, `GetInputSlot`, `GetNumInputSlots`, `GetNumOutputSlots` |
| [[1-armnn-overview|1 ArmNN Overview]] | `bm25+entity(3)` | `32.855` | `Connect`, `SetAdditionalInfo`, `SetTensorInfo` |
| [[2.3-runtime-and-execution|2.3 Runtime and Execution]] | `bm25` | `32.216` | *(lexical/graph match)* |
| [[3.3-model-serialization|3.3 Model Serialization]] | `bm25` | `30.749` | *(lexical/graph match)* |
| [[5.2-tensorflow-lite-delegate|5.2 TensorFlow Lite Delegate]] | `bm25` | `30.488` | *(lexical/graph match)* |
| [[2.2-backend-system|2.2 Backend System]] | `wikilink:2.1-network-and-graph-system+entity(1)` | `22.899` | `GetType` |

### High-Centrality Bridge Symbols (CBM Graph)

| Symbol | Kind | Source Location | Fan-In / Fan-Out |
|---|---|---|---|
| `SetTensorInfo` | Method | [src/armnn/Layer.cpp:609-612]() | in: `207` / out: `1` |
| `Connect` | Method | [src/armnn/Layer.cpp:123-129]() | in: `190` / out: `3` |
| `CreateWorkload` | Method | [src/armnnTestUtils/MockBackend.cpp:43-60]() | in: `188` / out: `3` |
| `end` | Method | [src/armnn/Graph.hpp:70-74]() | in: `186` / out: `2` |
| `GetName` | Method | [src/armnn/Layer.hpp:332-332]() | in: `168` / out: `1` |
| `GetInputSlot` | Method | [src/armnn/Layer.hpp:338-338]() | in: `160` / out: `0` |

Sources: [src/armnn/Layer.cpp:609-612](), [src/armnn/Layer.cpp:123-129](), [src/armnnTestUtils/MockBackend.cpp:43-60](), [src/armnn/Graph.hpp:70-74]()

### Cross-Subsystem Coupling

- [[3-model-support|3 Model Support]] — call/import coupling weight `171.0`
- [[4.1-reference-backend|4.1 Reference Backend]] — call/import coupling weight `134.0`
- [[6.2-testing-framework|6.2 Testing Framework]] — call/import coupling weight `134.0`
- [[2.3-runtime-and-execution|2.3 Runtime and Execution]] — call/import coupling weight `121.0`
- [[3.1-tensorflow-lite-parser|3.1 TensorFlow Lite Parser]] — call/import coupling weight `112.0`
- [[2.2-backend-system|2.2 Backend System]] — call/import coupling weight `111.0`
