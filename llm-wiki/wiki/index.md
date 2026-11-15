# ArmNN DeepWiki

Generated from `home-jason-Project-deepwiki-armnn` at commit `2b61cecc9df7` (2026-11-14T15:13:53+00:00).

## Pages

- [[1-overview|Overview]] — End-to-end architecture overview of ArmNN: core subsystems, compilation/execution pipeline, entry points, and cross-module dependencies.
- [[2-build-system-and-infrastructure|Build System and Infrastructure]] — Architectural overview of Build System and Infrastructure, spanning 28 source files and 2092 code symbols across 1 subsystems.
  - [[2.1-build-infrastructure|Build Infrastructure]] — Build Infrastructure subsystem (`build/infrastructure`), covering 28 files and 2092 symbols. Key symbols include `push_back`, `data`, `move`, `get`.
- [[3-backend-delegation-and-hardware-providers|Backend Delegation and Hardware Providers]] — Architectural overview of Backend Delegation and Hardware Providers, spanning 150 source files and 2618 code symbols across 6 subsystems.
  - [[3.1-backends-backendscommon|Backends Backendscommon]] — Backends Backendscommon subsystem (`backends/backendsCommon`), covering 28 files and 312 symbols. Key symbols include `to_string`, `ValidateInputsOutputs`, `ValidateNumInputs`, `ValidateNumOutputs`.
  - [[3.2-backends-reference|Backends Reference]] — Backends Reference subsystem (`backends/reference`), covering 28 files and 634 symbols. Key symbols include `GetNumDimensions`, `GetTensorInfo`, `MakeDecoder`, `MakeEncoder`.
  - [[3.3-backends-opencl|Backends OpenCL]] — Backends OpenCL subsystem (`backends/cl`), covering 28 files and 648 symbols. Key symbols include `IsClBackendSupported`, `RunClFunction`, `GetDataType`, `IsLayerSupported`.
  - [[3.4-backends-aclcommon|Backends Aclcommon]] — Backends Aclcommon subsystem (`backends/aclCommon`), covering 10 files and 89 symbols. Key symbols include `GetShape`, `BuildArmComputeTensorInfo`, `ConvertDataLayout`, `ConvertActivationDescriptorToAclActivationLayerInfo`.
  - [[3.5-backends-tosacommon|Backends Tosacommon]] — Backends Tosacommon subsystem (`backends/tosaCommon`), covering 28 files and 86 symbols. Key symbols include `GetTosaTensorShape`, `GenerateUniqueOutputName`, `GetUniqueTosaMappingID`, `GenerateUniqueInputName`.
  - [[3.6-other-backends|Other Backends]] — Other Backends subsystem (consolidating `Backends Neon`, `ArmNN Backends`, `Backends Tosareference`, `Backends Dynamic`), covering 28 files and 849 symbols. Key symbols include `IsNeonBackendSupported`, `info`, `IsLayerTypeSupported`, `CreateTensorHandle`.
- [[4-testing-validation-and-profiling|Testing, Validation and Profiling]] — Architectural overview of Testing, Validation and Profiling, spanning 40 source files and 4535 code symbols across 1 subsystems.
  - [[4.1-tests|Tests]] — Tests subsystem (`tests`), covering 40 files and 4535 symbols. Key symbols include `EndToEndLayerTestImpl`, `ElementwiseTestHelper`, `Setup`, `ComparisonTestImpl`.
- [[5-runtime-execution-and-kernel-dispatch|Runtime Execution and Kernel Dispatch]] — Architectural overview of Runtime Execution and Kernel Dispatch, spanning 157 source files and 3718 code symbols across 6 subsystems.
  - [[5.1-armnn|ArmNN]] — ArmNN subsystem (`src/armnn`), covering 28 files and 1007 symbols. Key symbols include `SetTensorInfo`, `Connect`, `end`, `GetName`.
  - [[5.2-armnn|ArmNN]] — ArmNN subsystem (`include/armnn`), covering 21 files and 440 symbols. Key symbols include `GetShape`, `InvalidArgumentException`, `GetNumElements`, `Exception`.
  - [[5.3-delegate-opaque|Delegate Opaque]] — Delegate Opaque subsystem (`delegate/opaque`), covering 28 files and 128 symbols. Key symbols include `GetTensorInfoForTfLiteOpaqueTensor`, `GetName`, `ValidateNumOutputs`, `IsValid`.
  - [[5.4-delegate-classic|Delegate Classic]] — Delegate Classic subsystem (`delegate/classic`), covering 28 files and 114 symbols. Key symbols include `GetTensorInfoForTfLiteTensor`, `GetLayerName`, `Connect`, `ValidateNumOutputs`.
  - [[5.5-armnnutils|Armnnutils]] — Armnnutils subsystem (`src/armnnUtils`), covering 24 files and 134 symbols. Key symbols include `Permuted`, `Permute`, `GetTensorInfo`, `GetStream`.
  - [[5.6-other-runtime-components|Other Runtime Components]] — Other Runtime Components subsystem (consolidating `ArmNN Optimizations`, `Armnntestutils`, `ArmNN Layers`, `Samples Common`, `Armnntestutils`, `Samples Objectdetection`), covering 28 files and 1895 symbols. Key symbols include `Run`, `FoldPadIntoLayer2dImpl`, `ReplaceConstDequantisationLayer`, `CreateWorkload`.
- [[6-developer-tools-and-platform-targets|Developer Tools and Platform Targets]] — Architectural overview of Developer Tools and Platform Targets, spanning 70 source files and 662 code symbols across 4 subsystems.
  - [[6.1-profiling-common|Profiling Common]] — Profiling Common subsystem (`profiling/common`), covering 28 files and 244 symbols. Key symbols include `IgnoreUnused`, `ProfilingException`, `CentreAlignFormatting`, `InvalidArgumentException`.
  - [[6.2-profiling-client|Profiling Client]] — Profiling Client subsystem (`profiling/client`), covering 28 files and 340 symbols. Key symbols include `ReadUint32`, `GetCurrentState`, `WriteUint32`, `GetNextGuid`.
  - [[6.3-profiling-server|Profiling Server]] — Profiling Server subsystem (`profiling/server`), covering 13 files and 77 symbols. Key symbols include `ParseData`, `ReceivePacket`, `ReadCategoryRecords`, `ParseData`.
  - [[6.4-profiling|Profiling]] — Profiling subsystem (`profiling`), covering 1 files and 1 symbols. Key symbols include `usage`.
- [[7-glossary|Glossary]] — Definitions and technical context for ArmNN domain terms, acronyms, file formats, and core code entities.
