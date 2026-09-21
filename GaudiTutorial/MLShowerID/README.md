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

