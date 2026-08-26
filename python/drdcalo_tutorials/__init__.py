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
import sys
from pathlib import Path
from xml.etree import ElementTree

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

#: Where the simplecalo1 steering file writes its full simulation output.
SIMULATED_INPUT_SC1 = DD4HEP_TUTORIALS / "simplecalo1.root"

#: The compact files the two exercises build their geometry from. Hands-on 6 reads
#: its cell dimensions back out of the simplecalo2 one through compact_constants()
#: instead of repeating the numbers, so that the analysis follows the geometry
#: whenever the XML is changed.
SIMPLECALO1_COMPACT = DD4HEP_TUTORIALS / "simplecalo1" / "compact" / "simplecalo1.xml"
SIMPLECALO2_COMPACT = DD4HEP_TUTORIALS / "simplecalo2" / "compact" / "simplecalo2.xml"


def sample_input() -> str:
    """The bundled 10-event sample.

    Used by the Gaudi exercises: it is small, quick, and there right after a
    clone, so nobody has to run the simulation first. Pass --IOSvc.Input to
    k4run to analyse a different file.
    """
    return str(SAMPLE_INPUT)


def _announce_fallback(expected: Path, steering: str) -> None:
    """Say out loud that the bundled 10-event sample is being used.

    Silently analysing a different file than the one the reader thinks they
    produced is the most confusing thing this module could do, so the fallback
    is never quiet. stderr, because in a notebook that is the stream that stands
    out from the analysis output.
    """
    print(
        f"NOTE: {expected} does not exist, falling back to the bundled 10-event sample.\n"
        f"      Ten events are enough to make the code run, not to make a plot worth "
        f"showing.\n"
        f"      Produce the full simulation with:  ddsim --steeringFile {steering}",
        file=sys.stderr,
    )


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
    _announce_fallback(SIMULATED_INPUT, "simplecalo2/sc2SteeringFile.py")
    return str(SAMPLE_INPUT)


def simplecalo1_input() -> str:
    """The simplecalo1 events to analyse in the Section 1 notebook.

    A full simulation generated in the DD4hep tutorial is preferred when it is
    there; otherwise the bundled sample is used, which carries the same
    `simplecaloRO` collection and so gives a meaningful energy sum even though it
    was produced with simplecalo2. Set SIMPLECALO1_FILE to read another file.
    """
    override = os.getenv("SIMPLECALO1_FILE")
    if override:
        return str(Path(override).expanduser())
    if SIMULATED_INPUT_SC1.exists():
        return str(SIMULATED_INPUT_SC1)
    _announce_fallback(SIMULATED_INPUT_SC1, "simplecalo1/sc1SteeringFile.py")
    return str(SAMPLE_INPUT)


def gaudi_output(filename: str) -> str:
    """Path for a file written by a Gaudi exercise, creating the directory."""
    GAUDI_DATA.mkdir(parents=True, exist_ok=True)
    return str(GAUDI_DATA / filename)


def compact_constants(compact) -> dict:
    """The <constant> definitions of a compact file, lengths in mm.

    `<constant name="CellX" value="10.0*cm"/>` comes back as `{"CellX": 100.0}`.
    Values are evaluated in the order the file defines them, so a constant can
    refer to an earlier one the way the compact file does. mm is also the unit
    EDM4hep stores positions in, so what comes back compares with a hit position
    directly.
    """
    values = {"mm": 1.0, "cm": 10.0, "m": 1000.0}
    for constant in ElementTree.parse(str(compact)).iter("constant"):
        name, value = constant.get("name"), constant.get("value")
        values[name] = eval(value, {"__builtins__": {}}, values)
    return values
