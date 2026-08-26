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
from drdcalo_tutorials import gaudi_output, sample_input

from Gaudi.Configuration import INFO
from k4FWCore import IOSvc, ApplicationMgr
from Configurables import EventDataSvc, UniqueIDGenSvc, ChronoAuditor, AuditorSvc

chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]

io_svc = IOSvc("IOSvc")
io_svc.Input = sample_input()
io_svc.Output = gaudi_output("simpleCalo_noiseDigitizer.root")

from Configurables import EventStats

eventStats_functional = EventStats("EventStats",

    InputCaloHitCollection=["simplecaloRO"],
    OutputEnergyBarycentre=["EnergyBarycentreX", "EnergyBarycentreY", "EnergyBarycentreZ"],
    OutputTotalEnergy=["TotalEnergy"],
    SaveHistograms=True,
    OutputLevel=INFO
)

from Configurables import RandomNoiseDigitizer
random_noise_digitizer = RandomNoiseDigitizer("RandomNoiseDigitizer",
                                InputCaloSimHitCollection=["simplecaloRO"],
                                OutputCaloDigiHitCollection=["CaloDigiHits"],
                                uidSvcName="uidSvc",
                                NoiseMean=1e-3,
                                NoiseWidth=1e-4,
                                OutputLevel=INFO
                                )

app_mgr = ApplicationMgr(
    TopAlg=[eventStats_functional, random_noise_digitizer],
    EvtSel='NONE',
    EvtMax=-1,
    ExtSvc=[EventDataSvc("EventDataSvc"), UniqueIDGenSvc("uidSvc"), audsvc],
    StopOnSignal=True,
)
