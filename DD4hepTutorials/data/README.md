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
# Bundled EDM4hep sample

`simplecalo2_sample.root` is a deterministic 10-event input shared by the DD4hep analysis tools
and the Gaudi exercises. It contains `EventHeader`, `MCParticles`, `simplecaloRO`, and
`simplecaloROContributions` and was generated with the completed simplecalo2 geometry using
key4hep release `2026-04-08` and random seed `12345`.

All lengths are in **mm** and all times in **ns**, as EDM4hep specifies: `simplecaloRO.position`
is the centre of the cell, `simplecaloROContributions.stepPosition` the position of the
individual Geant4 step that contributed. Energies are in GeV for hits and contributions.

The small sample lets the notebook run after a fresh clone. It is not intended to replace the
full 500-event simulation when producing statistically meaningful plots — the notebooks say so
out loud when they fall back to it. After completing the cell-placement exercise, regenerate a
full `DD4hepTutorials/simplecalo2.root` with:

```bash
ddsim --steeringFile DD4hepTutorials/simplecalo2/sc2SteeringFile.py
```

The steering file names both its compact file and its output relative to itself, so the command
above works from any directory and always writes `DD4hepTutorials/simplecalo2.root`, which is
where the notebooks look. Pass `--outputFile` to put it somewhere else, and point the notebooks
at it with `SIMPLECALO2_FILE`.

To reproduce the bundled fixture after enabling the completed cell-placement implementation:

```bash
ddsim --steeringFile DD4hepTutorials/simplecalo2/sc2SteeringFile.py \
  --numberOfEvents 10 \
  --outputFile DD4hepTutorials/data/simplecalo2_sample.root \
  --random.seed 12345 \
  --random.enableEventSeed
```

The geometry it was produced with is the one in `simplecalo2/compact/simplecalo2.xml` at the time:
10 x 10 cells of 10 cm. Change `CellX` there and this file no longer matches — the last cell of
`readEdm4hepSolution.ipynb` compares a decoded cell index against the stored hit position and will
say so.

SHA-256: `a4faa81b48a13e48f4363224e039c41f949d3452acdd223ebaba61b9f1b672b2`
