from Gaudi.Configuration import DEBUG
from k4FWCore import IOSvc, ApplicationMgr
from Configurables import EventDataSvc

io_svc = IOSvc("IOSvc")
io_svc.Input = "../../data/clusterID_e-_1-20GeV_eval.root"
io_svc.Output = "mlshowerid_output_e-_1-20GeV.root"

from Configurables import MLShowerIDSolution
ml_shower_id = MLShowerIDSolution(
    "MLShowerIDSolution",
    InputSimCaloHitCollection=["simplecaloRO"],
    OutputCaloHitCollection=["MLShowerIDCaloHits"],
    OutputClusterCollection=["MLShowerIDClusters"],
    ONNXModelPath="../../data/pointnet_simplecalo.onnx",
    OutputLevel=DEBUG,
)

app_mgr = ApplicationMgr(
    TopAlg=[ml_shower_id],
    EvtSel="NONE",
    EvtMax=100,
    ExtSvc=[EventDataSvc("EventDataSvc")],
    StopOnSignal=True,
)
