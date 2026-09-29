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
from pathlib import Path

from Gaudi.Configuration import INFO
from k4FWCore import IOSvc, ApplicationMgr
from Configurables import EventDataSvc, AuditorSvc, ChronoAuditor

data_dir = Path(__file__).resolve().parents[2] / "data"

io_svc = IOSvc("IOSvc")
io_svc.Input = str(data_dir / "simpleCalo_simulation.root")
io_svc.Output = str(data_dir / "simpleCalo_eventStats.root")

# The following would also work if k4run is called from EventStats/options:
# io_svc.Input = "../../data/simpleCalo_simulation.root"
# io_svc.Input = "../../data/simpleCalo_simulation.root"

chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]

from Configurables import EventStats

eventStats_functional = EventStats("EventStats",
    InputCaloHitCollection = ["simplecaloRO"],
    OutputEnergyBarycentre = ["EnergyBarycentreX", "EnergyBarycentreY", "EnergyBarycentreZ"],
    OutputTotalEnergy = ["TotalEnergy"],
    SaveHistograms = True,
    OutputLevel = INFO
)

app_mgr = ApplicationMgr(
    TopAlg = [eventStats_functional],
    EvtSel = 'NONE',
    EvtMax = -1,
    ExtSvc = [EventDataSvc("EventDataSvc"), audsvc],
    StopOnSignal = True,
)
