# 3-Source Context Packet (`git` + `CBM` + `llm-wiki`) for `6-model-export-and-llm-support` — Model Export and LLM Support

- **Target Wiki File**: `wiki/6-model-export-and-llm-support.md`
- **Archetype**: `Parent Hub Page`
- **Parent Page**: `None (Top-Level Chapter)`
- **Summary**: Architectural specification and implementation reference for Model Export and LLM Support (40 relevant source files). Primary code entities: `MuseGlimmerImageSpan`, `MuseGlimmerPreparationSpec`, `MuseGlimmerPreparedInput`, `Backing`, `RequestHandle`.
- **Valid `[[wikilink]]` Neighbours**: `[[1-overview|Overview]]`, `[[6.1-llama-model-export|LLaMA and Generative Model Export]]`, `[[6.2-llm-runner-framework|LLM Runner Framework]]`, `[[6.3-custom-operators-and-extensions|Custom Operators and Extensions]]`, `[[6.4-multimodal-and-audio-models|Multimodal and Audio Models]]`, `[[1.1-getting-started|Getting Started]]`, `[[1.2-export-api-and-recipe-system|Export API and Recipe System]]`, `[[2.2-kernel-libraries-and-selective-build|Kernel Libraries and Selective Build]]`

## 1. Relevant Source Files (`git` + `CBM`, use verbatim in `<details>`)
- `[examples/models/muse-glimmer/runtime/prompt_preparation.h](examples/models/muse-glimmer/runtime/prompt_preparation.h)`
- `[extension/llm/serving/serving_runtime.cpp](extension/llm/serving/serving_runtime.cpp)`
- `[extension/llm/cache/cache_registry.cpp](extension/llm/cache/cache_registry.cpp)`
- `[examples/models/__init__.py](examples/models/__init__.py)`
- `[extension/llm/serving/detail/prompt_preparer.h](extension/llm/serving/detail/prompt_preparer.h)`
- `[examples/models/codegen/__init__.py](examples/models/codegen/__init__.py)`
- `[examples/models/deeplab_v3/model.py](examples/models/deeplab_v3/model.py)`
- `[examples/models/muse-glimmer/runtime/cuda_dflash_executor.cpp](examples/models/muse-glimmer/runtime/cuda_dflash_executor.cpp)`
- `[examples/models/deit_tiny/model.py](examples/models/deit_tiny/model.py)`
- `[examples/models/checkpoint.py](examples/models/checkpoint.py)`
- `[extension/llm/custom_ops/op_sdpa.cpp](extension/llm/custom_ops/op_sdpa.cpp)`
- `[examples/models/gemma4_31b/gemma4_31b_engine.cpp](examples/models/gemma4_31b/gemma4_31b_engine.cpp)`
- `[examples/models/muse-glimmer/runtime/mlx_executor.cpp](examples/models/muse-glimmer/runtime/mlx_executor.cpp)`
- `[examples/models/efficient_sam/efficient_sam_core/efficient_sam_decoder.py](examples/models/efficient_sam/efficient_sam_core/efficient_sam_decoder.py)`
- `[examples/models/qwen3_5_moe/qwen35_moe_engine.cpp](examples/models/qwen3_5_moe/qwen35_moe_engine.cpp)`
- `[examples/models/emformer_rnnt/model.py](examples/models/emformer_rnnt/model.py)`
- `[examples/models/edsr/model.py](examples/models/edsr/model.py)`
- `[examples/models/efficient_sam/efficient_sam_core/efficient_sam_encoder.py](examples/models/efficient_sam/efficient_sam_core/efficient_sam_encoder.py)`
- `[examples/models/codegen/convert_weight.py](examples/models/codegen/convert_weight.py)`
- `[examples/models/parakeet/parakeet_transcriber.cpp](examples/models/parakeet/parakeet_transcriber.cpp)`
- `[examples/models/supertonic/runtime/supertonic_runner.cpp](examples/models/supertonic/runtime/supertonic_runner.cpp)`
- `[examples/models/efficient_sam/efficient_sam_core/efficient_sam.py](examples/models/efficient_sam/efficient_sam_core/efficient_sam.py)`
- `[examples/models/llava/export_llava.py](examples/models/llava/export_llava.py)`
- `[examples/models/llava/model.py](examples/models/llava/model.py)`
- `[examples/models/supertonic/export/common.py](examples/models/supertonic/export/common.py)`
- `[examples/models/llama/static_attention.py](examples/models/llama/static_attention.py)`
- `[examples/models/voxtral_tts/voxtral_tts_runner.cpp](examples/models/voxtral_tts/voxtral_tts_runner.cpp)`
- `[extension/llm/custom_ops/op_sdpa_impl.h](extension/llm/custom_ops/op_sdpa_impl.h)`
- `[examples/models/deepseek-r1-distill-llama-8B/README.md](examples/models/deepseek-r1-distill-llama-8B/README.md)`
- `[examples/models/dinov2/README.md](examples/models/dinov2/README.md)`

## 2. Grounded Code Symbols (`CBM`, use verbatim for `[file:start-end]()` pill citations)
- `MuseGlimmerPreparationSpec` (Class) @ `[examples/models/muse-glimmer/runtime/prompt_preparation.h:22-33]()` [fan-in=0, fan-out=0] — // One instance per executor. Sharing this immutable value with the CPU preparer // binds its payloads to that exact executor, not just compatible tensor shapes
- `CustomGroupNorm` (Class) @ `[examples/models/efficient_sam/efficient_sam_core/efficient_sam_decoder.py:166-191]()` [fan-in=1, fan-out=0] — # TODO: Remove CustomGroupNorm implementation once issue #6817 is resolved
- `PositionEmbeddingRandom` (Class) @ `[examples/models/efficient_sam/efficient_sam_core/efficient_sam_decoder.py:108-162]()` [fan-in=1, fan-out=0] — Positional encoding using random spatial frequencies.
- `ExportBounds` (Class) @ `[examples/models/supertonic/export/common.py:30-44]()` [fan-in=9, fan-out=0] — 
- `Model` (Class) @ `[examples/models/__init__.py:11-55]()` [fan-in=3, fan-out=0] — 
- `EmformerRnntJoinerExample` (Class) @ `[examples/models/emformer_rnnt/model.py:98-112]()` [fan-in=1, fan-out=0] — This is a wrapper for validating joiner for the Emformer RNN-T architecture. It does not reflect the actual usage such as beam search, but rather an example for
- `EmformerRnntPredictorExample` (Class) @ `[examples/models/emformer_rnnt/model.py:62-76]()` [fan-in=1, fan-out=0] — This is a wrapper for validating predictor for the Emformer RNN-T architecture. It does not reflect the actual usage such as beam search, but rather an example 
- `EmformerRnntTranscriberExample` (Class) @ `[examples/models/emformer_rnnt/model.py:27-41]()` [fan-in=1, fan-out=0] — This is a wrapper for validating transcriber for the Emformer RNN-T architecture. It does not reflect the actual usage such as beam search, but rather an exampl
- `ChunkScratch` (Class) @ `[extension/llm/custom_ops/op_sdpa.cpp:1025-1076]()` [fan-in=0, fan-out=0] — // One worker's scratch for the chunked kernel, carved from a single arena so // there is one allocate_temp for the whole op and disjoint per-worker slabs. // D
- `ImageEncoderViT` (Class) @ `[examples/models/efficient_sam/efficient_sam_core/efficient_sam_encoder.py:183-261]()` [fan-in=1, fan-out=0] — # Image encoder for efficient SAM.
- `PatchEmbed` (Class) @ `[examples/models/efficient_sam/efficient_sam_core/efficient_sam_encoder.py:32-54]()` [fan-in=1, fan-out=0] — 2D Image to Patch Embedding
- `MuseGlimmerImageSpan` (Class) @ `[examples/models/muse-glimmer/runtime/prompt_preparation.h:35-38]()` [fan-in=0, fan-out=0] — 
- `MuseGlimmerPreparedInput` (Class) @ `[examples/models/muse-glimmer/runtime/prompt_preparation.h:42-86]()` [fan-in=0, fan-out=0] — 
- `Backing` (Class) @ `[examples/models/muse-glimmer/runtime/prompt_preparation.h:62-81]()` [fan-in=0, fan-out=0] — 
- `ServingRuntime::Impl` (Class) @ `[extension/llm/serving/serving_runtime.cpp:223-1918]()` [fan-in=0, fan-out=0] — 
- `CheckedSuffix` (Class) @ `[extension/llm/serving/serving_runtime.cpp:692-696]()` [fan-in=0, fan-out=0] — 
- `Command` (Class) @ `[extension/llm/serving/serving_runtime.cpp:241-251]()` [fan-in=0, fan-out=0] — 
- `PrefixSelection` (Class) @ `[extension/llm/serving/serving_runtime.cpp:685-688]()` [fan-in=0, fan-out=0] — 
- `Slot` (Class) @ `[extension/llm/serving/serving_runtime.cpp:230-237]()` [fan-in=0, fan-out=0] — 
- `RequestState` (Class) @ `[extension/llm/serving/serving_runtime.cpp:84-219]()` [fan-in=0, fan-out=0] — 
- `TextRequest` (Class) @ `[extension/llm/serving/serving_runtime.cpp:46-82]()` [fan-in=0, fan-out=0] — 
- `Backend` (Class) @ `[examples/models/__init__.py:58-65]()` [fan-in=0, fan-out=0] — 

## 3. Grounded Source Code Excerpts (`git` Working Tree)
### `MuseGlimmerPreparationSpec` in `[examples/models/muse-glimmer/runtime/prompt_preparation.h:22-33]()`
```cpp
struct MuseGlimmerPreparationSpec final {
  const aten::ScalarType activation_dtype;
  const int32_t hidden_dim;
  const int32_t max_context_length;
  const int32_t max_forward_tokens;
  const int32_t vocab_size;
  const bool has_vision;
  const int64_t max_soft_tokens;
  const MuseGlimmerImageLimits image_limits;
  const batching::Token bos_id = 200000;
  const batching::Token patch_id = 200092;
};
```

### `CustomGroupNorm` in `[examples/models/efficient_sam/efficient_sam_core/efficient_sam_decoder.py:166-181]()`
```python
class CustomGroupNorm(nn.Module):
    def __init__(self, num_groups, num_channels, eps=1e-5, affine=True):
        """Custom Group Normalization."""
        super(CustomGroupNorm, self).__init__()
        self.num_groups = num_groups
        self.num_channels = num_channels
        self.eps = eps
        self.affine = affine

        if self.affine:
            self.weight = nn.Parameter(torch.ones(num_channels))
            self.bias = nn.Parameter(torch.zeros(num_channels))

    def forward(self, x):
        N, C, *rest = x.shape
        G = self.num_groups
```

### `PositionEmbeddingRandom` in `[examples/models/efficient_sam/efficient_sam_core/efficient_sam_decoder.py:108-123]()`
```python
class PositionEmbeddingRandom(nn.Module):
    """
    Positional encoding using random spatial frequencies.
    """

    def __init__(self, num_pos_feats: int) -> None:
        super().__init__()
        self.register_buffer(
            "positional_encoding_gaussian_matrix", torch.randn((2, num_pos_feats))
        )

    def _pe_encoding(self, coords: torch.Tensor) -> torch.Tensor:
        """Positionally encode points that are normalized to [0,1]."""
        # assuming coords are in [0, 1]^2 square and have d_1 x ... x d_n x 2 shape
        coords = 2 * coords - 1
        coords = coords @ self.positional_encoding_gaussian_matrix
```

### `ExportBounds` in `[examples/models/supertonic/export/common.py:30-44]()`
```python
class ExportBounds:
    text_max: int = 512
    latent_max: int = 512

    def __post_init__(self) -> None:
        for name, value in (
            ("text", self.text_max),
            ("latent", self.latent_max),
        ):
            if value < 2:
                raise ValueError(f"{name} maximum must be at least 2")
            if value > MAX_MODEL_POSITIONS:
                raise ValueError(
                    f"{name} maximum must not exceed {MAX_MODEL_POSITIONS}"
                )
```

### `Model` in `[examples/models/__init__.py:11-26]()`
```python
class Model(str, Enum):
    Mul = "mul"
    Linear = "linear"
    Add = "add"
    AddMul = "add_mul"
    Softmax = "softmax"
    Conv1d = "conv1d"
    Dl3 = "dl3"
    Edsr = "edsr"
    EmformerTranscribe = "emformer_transcribe"
    EmformerPredict = "emformer_predict"
    EmformerJoin = "emformer_join"
    Llama2 = "llama2"
    Llama = "llama"
    Llama32VisionEncoder = "llama3_2_vision_encoder"
    Lstm = "lstm"
```


## 4. Linked Official Docs (`llm-wiki` / `RAG`)
- **Model and Backend Testing Framework** (`wiki/7.2-model-and-backend-testing-framework.md`, score=247.236, shared_symbols=['Attention', 'ExportBounds', 'Model']): # Model and Backend Testing Framework ↑ [[7-testing-and-cicd-infrastructure|Testing and CI/CD Infrastructure]] > Architectural specification and implementation reference for Model and Backend Testing Framework (40 relevant source files). Primary code entities: `MuseGlimmerImageSpan`, `MuseGlimmerPreparationSpec`, `MuseGlimmerPreparedInput`, `Backing`, `Bac
- **Testing and CI/CD Infrastructure** (`wiki/7-testing-and-cicd-infrastructure.md`, score=137.325, shared_symbols=['Model']): # Testing and CI/CD Infrastructure > Architectural specification and implementation reference for Testing and CI/CD Infrastructure (36 relevant source files). Primary code entities: `BenchmarkResults`, `save_json`, `to_dict`, `to_v3_format`, `BenchmarkFilters`. <details> <summary>Relevant source files</summary> The following files were used as context for
- **ExecuTorch DeepWiki** (`wiki/index.md`, score=134.499, shared_symbols=[]): # ExecuTorch DeepWiki Generated from `home-jason-Project-deepwiki-executorch` at commit `b3b565b5b62f` (2026-11-15T15:02:11+00:00). ## Pages - [[1-overview|Overview]] — Architectural specification and implementation reference for Overview (10 relevant source files). Primary code entities: `Module`, `MethodHolder`, `PlannedMemory`, `EdgeProgramManager`, `_
- **LLaMA and Generative Model Export** (`wiki/6.1-llama-model-export.md`, score=124.368, shared_symbols=['Attention', 'Model']): # LLaMA and Generative Model Export ↑ [[6-model-export-and-llm-support|Model Export and LLM Support]] > Architectural specification and implementation reference for LLaMA and Generative Model Export (40 relevant source files). Primary code entities: `Attention`, `forward`, `AttentionGatedDeltaNet`, `__init__`, `ETPybindEvalWrapper`. <details> <summary>Rel
- **CI/CD Workflows and Validation** (`wiki/7.1-cicd-workflows-and-validation.md`, score=122.868, shared_symbols=['Model']): # CI/CD Workflows and Validation ↑ [[7-testing-and-cicd-infrastructure|Testing and CI/CD Infrastructure]] > Architectural specification and implementation reference for CI/CD Workflows and Validation (31 relevant source files). Primary code entities: `BenchmarkResults`, `save_json`, `to_dict`, `to_v3_format`, `BenchmarkFilters`. <details> <summary>Relevan
- **Performance Benchmarking and Profiling** (`wiki/7.3-performance-benchmarking-and-profiling.md`, score=122.868, shared_symbols=['Model']): # Performance Benchmarking and Profiling ↑ [[7-testing-and-cicd-infrastructure|Testing and CI/CD Infrastructure]] > Architectural specification and implementation reference for Performance Benchmarking and Profiling (36 relevant source files). Primary code entities: `Allocator`, `MemAllocation`, `MemEvent`, `ProfileData`, `ETDumpGen`. <details> <summary>R

## 5. Pre-Verified DeepWiki v1.9.9.5 Mermaid Diagrams
### Natural Language Space <-> Code Entity Space
```mermaid
graph LR
  subgraph NL_Space["Natural Language Space"]
    NL_0["Muse Glimmer Preparation Spec"]
    NL_1["Custom Group Norm"]
    NL_2["Position Embedding Random"]
    NL_3["Export Bounds"]
    NL_4["Model"]
    NL_5["Emformer Rnnt Joiner Example"]
  end
  subgraph Code_Space["Code Entity Space"]
    CE_0["MuseGlimmerPreparationSpec (prompt_preparation.h:22)"]
    CE_1["CustomGroupNorm (efficient_sam_decoder.py:166)"]
    CE_2["PositionEmbeddingRandom (efficient_sam_decoder.py:108)"]
    CE_3["ExportBounds (common.py:30)"]
    CE_4["Model (__init__.py:11)"]
    CE_5["EmformerRnntJoinerExample (model.py:98)"]
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
  subgraph sub_this["Model Export and LLM Support"]
    subgraph sg_0["examples/models/muse-glimmer"]
      n_examples_models_muse_glimmer_runtime["runtime/"]
    end
    subgraph sg_1["extension/llm"]
      n_extension_llm_serving["serving/"]
      n_extension_llm_cache["cache/"]
      n_extension_llm_custom_ops["custom_ops/"]
    end
    subgraph sg_2["examples"]
      n_examples_models["models/"]
    end
    subgraph sg_3["extension/llm/serving"]
      n_extension_llm_serving_detail["detail/"]
    end
    subgraph sg_4["examples/models"]
      n_examples_models_codegen["codegen/"]
      n_examples_models_deeplab_v3["deeplab_v3/"]
      n_examples_models_deit_tiny["deit_tiny/"]
      n_examples_models_gemma4_31b["gemma4_31b/"]
      n_examples_models_qwen3_5_moe["qwen3_5_moe/"]
      n_examples_models_emformer_rnnt["emformer_rnnt/"]
      n_examples_models_edsr["edsr/"]
    end
  end
  n_page_2_build_system_and_infrastructure(["Build System and Infrastructure"])
  n_page_6_1_llama_model_export(["LLaMA and Generative Model Export"])
  n_page_6_2_llm_runner_framework(["LLM Runner Framework"])
  n_page_8_runtime_execution(["Runtime Execution"])
  n_examples_models_muse_glimmer_runtime -.-> n_page_6_1_llama_model_export
  n_extension_llm_serving -.-> n_page_2_build_system_and_infrastructure
  n_examples_models_muse_glimmer_runtime -.-> n_page_8_runtime_execution
  n_extension_llm_serving -.-> n_page_6_2_llm_runner_framework
  n_extension_llm_custom_ops -.-> n_page_2_build_system_and_infrastructure
  n_extension_llm_custom_ops --> n_extension_llm_serving_detail
  n_extension_llm_cache -.-> n_page_6_2_llm_runner_framework
  n_extension_llm_serving_detail -.-> n_page_6_2_llm_runner_framework
  n_extension_llm_custom_ops -.-> n_page_8_runtime_execution
  n_examples_models_gemma4_31b -.-> n_page_6_1_llama_model_export
  n_examples_models_muse_glimmer_runtime -.-> n_page_6_2_llm_runner_framework
  n_extension_llm_serving --> n_extension_llm_serving_detail
  n_examples_models_qwen3_5_moe -.-> n_page_6_1_llama_model_export
  n_examples_models_gemma4_31b -.-> n_page_8_runtime_execution
  n_examples_models_supertonic_runtime -.-> n_page_6_1_llama_model_export
```

### Class Hierarchy Diagram
```mermaid
classDiagram
  class ExportBounds {
    +__post_init__()
  }
  class Model {
    +__str__()
  }
  class NGramCache {
    +__init__()
    +add()
    +__iter__()
    +__str__()
  }
  class MethodContract {
  }
  class EfficientSam {
    +__init__()
    +predict_masks()
    +get_rescaled_pts()
    +get_image_embeddings()
    +forward()
    +preprocess()
  }
  class CustomGroupNorm {
    +__init__()
    +forward()
  }
  class MaskDecoder {
    +__init__()
    +forward()
    +predict_masks()
  }
  class PositionEmbeddingRandom {
    +__init__()
    +_pe_encoding()
    +custom_cumsum()
    +forward()
    +forward_with_coords()
  }
```

### Call Sequence Diagram
```mermaid
sequenceDiagram
  participant prompt_preparation as "prompt_preparation"
  participant efficient_sam_decoder as "efficient_sam_decoder"
  participant common as "common"
  participant __init__ as "__init__"
  participant model as "model"
  prompt_preparation->>efficient_sam_decoder: MuseGlimmerPreparationSpec() -' CustomGroupNorm()
  efficient_sam_decoder->>efficient_sam_decoder: CustomGroupNorm() -' PositionEmbeddingRandom()
  efficient_sam_decoder->>common: PositionEmbeddingRandom() -' ExportBounds()
  common->>__init__: ExportBounds() -' Model()
  __init__->>model: Model() -' EmformerRnntJoinerExample()
```

## 6. DeepWiki v1.9.9.5 Authoring Checklist for `wiki/6-model-export-and-llm-support.md`
1. Keep YAML frontmatter at top (`id`, `title`, `parent`, `sources`, `linked_docs`, `bridge_symbols`).
2. Keep `<details><summary>Relevant source files</summary>` block immediately after `# Title`.
3. Start with `## Purpose and Scope`, then numbered `## 1. ...`, `## 2. ...` sections separated by `---`.
4. Include at least 2 ```mermaid``` diagrams (including a `Natural Language Space` <-> `Code Entity Space` mapping).
5. Cite code entities inline using `[path/to/file.ext:start-end]()` and end every `##` section with `Sources: [file:start-end]()`.
6. Run `deepwiki_cli.py build --enrich-only ...` and `deepwiki_cli.py validate ...` after editing.
