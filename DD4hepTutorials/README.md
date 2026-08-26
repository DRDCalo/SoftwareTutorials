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
# DD4hepTutorials for DRDCalo

Hands-on exercises for DD4hep, a detector description framework:

 - **simplecalo1**: the fundamentals, by building a simplified calorimeter.
 - **simplecalo2**: a custom Geant4 sensitive detector on top of it.

Follow [this presentation](https://indico.cern.ch/event/1618975/sessions/635708/attachments/3252510/5805581/DRDCaloDD4hepTutorial_April2026.pdf) for both.

## Previous editions of this tutorial
- April 2026, DRDCalo Collaboration Meeting [presentation](https://indico.cern.ch/event/1618975/sessions/635708/attachments/3252510/5805581/DRDCaloDD4hepTutorial_April2026.pdf)
- April 2025, DRDCalo Collaboration Meeting [presentation](https://indico.ijclab.in2p3.fr/event/11400/sessions/5873/attachments/25413/37372/DRD6DD4hepTutorial_April2025.pdf)

## Analysing the output

| What | Notebook |
|---|---|
| Section 1: cell energy sum, Gaussian fit, energy resolution | `notebooks/plot_cell_energy_sum.ipynb` |
| Hands-on 6: hits, layers, lateral shape, contributions | `notebooks/readEdm4hep.ipynb` |

Hands-on 6 has six questions to complete; the finished version sits next to it as
`notebooks/readEdm4hepSolution.ipynb`.

Each notebook prefers the full simulation — `simplecalo1.root` and `simplecalo2.root`, which the
steering files always write into this directory whatever directory `ddsim` was launched from —
and otherwise falls back to the bundled 10-event `data/simplecalo2_sample.root`, saying so when
it does. `SIMPLECALO1_FILE` and `SIMPLECALO2_FILE` override the choice; the rules live in
`python/drdcalo_tutorials/__init__.py`.

Hands-on 6 reads the cell size and grid dimensions out of `simplecalo2/compact/simplecalo2.xml`,
the same constants `sc2_solution1.h` places the cells from, so changing `CellX` and re-running
`ddsim` needs no code edit. Its last cell checks a decoded cell index against the stored hit
position, which catches an input file produced before the geometry was changed.

### Running the notebooks

Open `SoftwareTutorials` itself as the VS Code workspace folder — not a parent directory — then
**Select Kernel** → **Python Environments** → `.venv/bin/python`. VS Code applies
`${workspaceFolder}/.env`, which `setup.sh` fills with the key4hep runtime. A `No module named
'awkward'` error means it did not, almost always because the workspace folder is a level too
high; see the main README.

For JupyterLab instead, run `jupyter lab --no-browser --port 8888` from a shell that has sourced
`setup.sh`, and forward that port.

## Viewing the geometry

`geoWebDisplay simplecalo1/compact/simplecalo1.xml` starts a web server and asks the operating
system to open a browser. On a remote machine that launch usually fails silently — the server is
still running, on the port it printed:

```
Info in <THttpEngine::Create>: Starting HTTP server on port 127.0.0.1:9427
```

Leave the `root [0]` prompt open, since quitting it stops the server, and forward that port to
your own machine — either through the VS Code **PORTS** panel, or:

``` bash
# on your laptop. Use the exact node name: lxplus.cern.ch is load balanced and would
# send you to a different machine, where nothing is listening.
ssh -N -L 9427:127.0.0.1:9427 <user>@lxplus8sXX.cern.ch
```

Then browse to **<http://localhost:9427/win1/>**. The `/win1/` matters: ROOT serves each GUI panel
as a separate named window, so the bare URL returns *404*. `/win2/` is the volume hierarchy
browser, useful on its own during Hands-on 1 and 2.

> ROOT also appends a single-use key to the URL and hands it only to the browser it launches
> itself, so a typed address returns *404* as well. To type one, put `WebGui.OnetimeKey: no` into
> a `.rootrc` in the directory you start `geoWebDisplay` from.

`geoWebDisplay` also drops a `viewer.cxx` in the current directory; it is a ROOT by-product,
ignored by git, and can be deleted.

### Without port forwarding

Export the geometry and look at it locally:

``` bash
geoConverter -compact2tgeo -input simplecalo1/compact/simplecalo1.xml -output simplecalo1_geo.root
# or -compact2gdml for a GDML file
```

Open the result in ROOT, or drag it onto <https://root.cern/js/>.

Happy coding! :rocket:
