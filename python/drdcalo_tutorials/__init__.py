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
"""Where the tutorials read their input and write their output.

Every exercise resolves its files through this module, so the layout of the
repository is written down once instead of once per script. `setup.sh` puts
this directory on PYTHONPATH, which is also how the tutorial plugins become
importable, so anything that can run an exercise can import this.

The module sits at <repository>/python/drdcalo_tutorials, which is what makes
`REPOSITORY` below correct. The helpers return strings, ready to be assigned to
a Gaudi property.
"""

import os
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]

DD4HEP_TUTORIALS = REPOSITORY / "DD4hepTutorials"
GAUDI_TUTORIALS = REPOSITORY / "GaudiTutorial"

#: Generated Gaudi output. Kept out of the source directories, and out of git.
GAUDI_DATA = GAUDI_TUTORIALS / "data"

#: The 10-event sample committed to the repository, so that the exercises run
#: straight after a clone without a multi-hundred-MB simulation.
SAMPLE_INPUT = DD4HEP_TUTORIALS / "data" / "simplecalo2_sample.root"

#: Where the simplecalo2 steering file writes its full simulation output.
SIMULATED_INPUT = DD4HEP_TUTORIALS / "simplecalo2.root"


def sample_input() -> str:
    """The bundled 10-event sample.

    Used by the Gaudi exercises: it is small, quick, and there right after a
    clone, so nobody has to run the simulation first. Pass --IOSvc.Input to
    k4run to analyse a different file.
    """
    return str(SAMPLE_INPUT)


def simplecalo2_input() -> str:
    """The simplecalo2 events to analyse in the notebooks.

    A full simulation generated in the DD4hep tutorial is preferred when it is
    there; otherwise the bundled sample is used. Set SIMPLECALO2_FILE to read
    another compatible file instead. Note that the full simulation is several
    hundred MB, which is why the Gaudi exercises stay on sample_input().
    """
    override = os.getenv("SIMPLECALO2_FILE")
    if override:
        return str(Path(override).expanduser())
    if SIMULATED_INPUT.exists():
        return str(SIMULATED_INPUT)
    return str(SAMPLE_INPUT)


def gaudi_output(filename: str) -> str:
    """Path for a file written by a Gaudi exercise, creating the directory."""
    GAUDI_DATA.mkdir(parents=True, exist_ok=True)
    return str(GAUDI_DATA / filename)
