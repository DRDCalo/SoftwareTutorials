<!--
Copyright (c) 2020-2024 Key4hep-Project.

This file is part of Key4hep.
See https://key4hep.github.io/key4hep-doc/ for further info.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
# MLShowerID

Gaudi processor for testing Tiny PointNet ONNX inference on SimpleCalo showers.

The processing flow is:

```text
SimCalorimeterHitCollection
  -> raw (x, y, z, energy) point tensor and validity mask
  -> ONNX model with embedded training normalization
  -> ONNX softmax scores [electron, hadronic]
  -> one output Cluster containing all converted CalorimeterHits
```

The number of accepted hits is read from the ONNX points tensor shape.
Hits are ordered by decreasing energy. Electron showers were trained with
label 0 and pion showers with label 1. The two cluster shape parameters are
stored as electron score first and hadronic score second.

The ONNX model is loaded once during algorithm initialization. Its expected
interface is:

```text
points: float32 [batch, 1024, 4]
mask:   bool    [batch, 1024]
scores: float32 [batch, 2]
```

