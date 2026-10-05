#
# Copyright (c) 2020-2024 Key4hep-Project.
#
# This file is part of Key4hep.
# See https://key4hep.github.io/key4hep-doc/ for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from Gaudi.Configuration import DEBUG
from k4FWCore import IOSvc, ApplicationMgr
from Configurables import EventDataSvc

io_svc = IOSvc("IOSvc")
io_svc.Input = "../../data/clusterID_e-_1-20GeV_eval.root"
io_svc.Output = "mlshowerid_output_e-_1-20GeV.root"

from Configurables import MLShowerID, MLShowerIDSolution

# After you finish all hands-on.
# Otherwise, you can switch to MLShowerIDSolution for the Solution processor
ml_shower_id = MLShowerID(
    "MLShowerID",
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
