# SoftwareTutorials

This repository hosts software tutorials related to DRDCalo (formerly DRD6) Collaboration
activities: DD4hep and Gaudi, presented at the 2nd and 4th Collaboration Meeting respectively.
Each is completed by following the presentation slides linked in its sub-directory.

## Compilation

These tutorials run inside the key4hep environment, so they need an EL9 machine (AlmaLinux 9,
RHEL 9, ...) with `/cvmfs/` mounted — lxplus, for instance.

``` bash
git clone https://github.com/DRDCalo/SoftwareTutorials.git
cd SoftwareTutorials
source setup.sh
mkdir build install
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
make install -j6
```

`setup.sh` must be **sourced in every new shell**. It

1. sources the key4hep stack, pinned to a fixed release so that everybody works with the same
   software (override with `KEY4HEP_VERSION=... source setup.sh`);
2. runs `k4_local_repo`, pointing the environment at the libraries built here;
3. creates `.venv`, a virtual environment inheriting everything from the stack;
4. makes `drdcalo_tutorials` importable — the module resolving every tutorial's input and output
   paths — through `PYTHONPATH` and a `.pth` file in `.venv`, so even a process that does not
   inherit the variable finds it;
5. writes `.env` with the key4hep runtime paths, which is what an editor hands to a notebook
   kernel. Only those variables are written, never the rest of your shell environment, and the
   file is created `0600`.

If a different key4hep release is already active, `setup.sh` stops rather than mixing the two.
Inside a container step 5 is skipped and it says so: `.env` records absolute paths and is read by
an editor on the host, where the container's mount point would be wrong.

Steps 3 to 5 exist for the notebooks: an editor's Jupyter kernel does not inherit your shell, so
it needs an interpreter it can find (`.venv`) and the environment to run in (`.env`). Both are
ignored by git and are rebuilt by sourcing `setup.sh` again.

### Using the notebooks in VS Code

**Open `SoftwareTutorials` itself as the workspace folder**, not a parent directory. This is the
one thing that has to be right: VS Code applies `${workspaceFolder}/.env`, and from a level above
it finds nothing and the notebook fails with `ModuleNotFoundError: No module named 'awkward'`.
Then choose **Select Kernel** → **Python Environments** and pick `.venv/bin/python` (shown as
*DRDCalo Tutorial*). No kernel has to be registered.

To keep a parent directory as the workspace folder instead, point VS Code at the right file in
that workspace's `.vscode/settings.json`:

``` json
{
    "python.envFile": "${workspaceFolder}/SoftwareTutorials/.env"
}
```

If a module goes missing, the recorded environment is stale: source `setup.sh` again and restart
the kernel. If it stays missing, the variable providing it is not on the allow-list in step 5 of
`setup.sh` — add the name there. If VS Code offers to install packages, it is running an
interpreter without the key4hep stack; fix the workspace folder rather than accepting.

### Disk space

`ddsim` writes a large EDM4hep file: the 500 events configured in the steering files are roughly
600 MB, and each tutorial writes its own. Without `--outputFile` they land in
`DD4hepTutorials/simplecalo1.root` and `DD4hepTutorials/simplecalo2.root` — where the notebooks
look — whatever directory `ddsim` was launched from. On a small quota, write elsewhere and point
the notebook at it:

``` bash
ddsim --steeringFile DD4hepTutorials/simplecalo1/sc1SteeringFile.py --outputFile /tmp/simplecalo1.root
export SIMPLECALO1_FILE=/tmp/simplecalo1.root
```

or lower `SIM.numberOfEvents`; 100 events are already plenty for the energy resolution fit.

Nothing forces you to generate that file at all: the notebooks and all Gaudi exercises fall back
to the bundled 10-event `DD4hepTutorials/data/simplecalo2_sample.root`, and say so when they do.
Every one of these rules lives in `python/drdcalo_tutorials/__init__.py`.
