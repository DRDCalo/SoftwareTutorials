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

Welcome to the DD4hep Tutorials of DRDCalo repository!

This repository contains hands-on exercises to help you learn DD4hep, a powerful detector description framework. The exercises are organized into separate folders:

 - **simplecalo1**: Learn the fundamentals of DD4hep by building your first simplified calorimeter.
 - **simplecalo2**: Build on simplecalo1 and explore how to set up a custom Geant4 Sensitive Detector.

For instructions on **simplecalo1** and **simplecalo2** follow [this presentation](https://indico.cern.ch/event/1618975/sessions/635708/attachments/3252510/5805581/DRDCaloDD4hepTutorial_April2026.pdf).

## Previous editions of this tutorial
- April 2026, DRDCalo Collaboration Meeting [presentation](https://indico.cern.ch/event/1618975/sessions/635708/attachments/3252510/5805581/DRDCaloDD4hepTutorial_April2026.pdf)
- April 2025, DRDCalo Collaboration Meeting [presentation](https://indico.ijclab.in2p3.fr/event/11400/sessions/5873/attachments/25413/37372/DRD6DD4hepTutorial_April2025.pdf)

## Analysing the output

All analysis lives in notebooks, all of it Python:

| What | Notebook |
|---|---|
| Section 1: cell energy sum, Gaussian fit, energy resolution | `notebooks/plot_cell_energy_sum.ipynb` |
| Hands-on 6: hits, layers, lateral shape, contributions | `notebooks/readEdm4hep.ipynb` |

Hands-on 6 is a notebook with six questions to complete. The finished version sits next to it as
`notebooks/readEdm4hepSolution.ipynb`. A deterministic 10-event input file is included as
`data/simplecalo2_sample.root`, so every notebook works directly after cloning.

Each notebook resolves its own input. Section 1 prefers `simplecalo1.root` and Hands-on 6 prefers
`simplecalo2.root`, both in this directory, and both fall back to the bundled sample when the full
simulation has not been produced yet. `SIMPLECALO1_FILE` and `SIMPLECALO2_FILE` override the
choice. The rules live in `drdcalo_tutorials.simplecalo1_input()` and
`.simplecalo2_input()`, which is also where the Gaudi exercises get their paths.

### Running the notebooks

Uproot reads the EDM4hep ROOT file, DD4hep's native bit-field decoder interprets cell IDs,
Awkward Array and NumPy process the data, SciPy fits, and Matplotlib draws the results. No ROOT
histograms or canvases are involved. `setup.sh` in the top directory of the repository provides
these packages, registers a Jupyter kernel, and exports the repository location used to find the
sample; see the main README.

In **VS Code with Remote-SSH**, open `SoftwareTutorials` itself as the workspace folder — not a
parent directory — then choose **Select Kernel** → **Python Environments** and pick
`.venv/bin/python`. VS Code applies `${workspaceFolder}/.env`, which `setup.sh` fills with the
key4hep runtime, and that is what makes `uproot`, `dd4hep` and the rest importable.

If the notebook fails with `No module named 'awkward'`, or VS Code offers to install packages,
the environment file was not applied — almost always because the workspace folder is a level
above the repository. See the main README for the `python.envFile` setting that fixes that
without moving the workspace.

To use JupyterLab instead, start it from a shell in which `setup.sh` has been sourced and forward
its port the same way as for the geometry viewer below:

``` bash
jupyter lab --no-browser --port 8888
```

The plots are ordinary Matplotlib figures displayed directly in the notebook.

## Viewing the geometry

`geoWebDisplay simplecalo1/compact/simplecalo1.xml` starts a small web server and asks the
operating system to open a browser on it. If a browser window appears, you are done.

If nothing appears, the server is still running and only the browser launch failed. This is the
normal case on a remote machine or inside a container, where `xdg-open` is often missing. Look
for this line in the output:

```
Info in <THttpEngine::Create>: Starting HTTP server on port 127.0.0.1:8090
```

Leave the `root [0]` prompt open, since quitting it stops the server, and forward that port to
your own machine:

``` bash
# in a terminal on your laptop. Use the exact node name: lxplus.cern.ch is load balanced
# and would send you to a different machine, where nothing is listening.
ssh -N -L 8090:127.0.0.1:8090 <user>@lxplus8sXX.cern.ch
```

Then browse to **<http://localhost:8090/win1/>**. In VS Code with Remote-SSH the `ssh` command is
not needed: open the **PORTS** panel next to the terminal, choose *Forward a Port* and enter
`8090`.

> The `/win1/` matters. ROOT serves each GUI panel as a separate named window, so the bare
> `http://localhost:8090/` returns *404*. `/win2/` is the volume hierarchy browser, which is
> useful on its own while working through Hands-on 1 and 2.

The `.rootrc` in this directory fixes the port and disables ROOT's one-time URL key so that the
address above never changes. `geoWebDisplay` also drops a `viewer.cxx` file in the current
directory; it is a ROOT by-product and can be deleted.

### Without port forwarding

If forwarding is not an option, export the geometry and look at it locally:

``` bash
geoConverter -compact2tgeo -input simplecalo1/compact/simplecalo1.xml -output simplecalo1_geo.root
# or -compact2gdml for a GDML file
```

Copy the result to your machine and open it in ROOT, or drag it onto <https://root.cern/js/>.

Happy coding! :rocket:
