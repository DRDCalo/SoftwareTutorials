# SoftwareTutorials


This repository hosts a variety of software tutorials related to DRDCalo (formerly DRD6) Collaboration activities.
It includes the tutorials on DD4hep and Gaudi, presented in the 2nd and 4th Collaboration Meeting respectively.

Ideally, this repository is expanded with relevant tutorials in the future.

The tutorials can be completed by following the presentation slides linked in the corresponding sub-directories


## Compilation

These tutorials are made within the key4hep environment.
To compile and run them, access to an EL9 machine (AlmaLinux 9, RHEL 9, ...) with `/cvmfs/` mounted (e.g. lxplus) to source the key4hep stack is required.

To clone and build the repository, run the following commands:


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
2. runs `k4_local_repo`, which points the environment at the libraries built in this repository;
3. creates a virtual environment in `.venv` that inherits everything from the stack;
4. makes `drdcalo_tutorials` importable — the module that resolves the tutorial input and
   output paths — by putting `python/` on `PYTHONPATH` and dropping a `.pth` file into `.venv`,
   so that it is found even by a process that does not inherit the variable;
5. writes a `.env` file capturing the environment, which is what gives the notebooks the
   key4hep runtime.

If the shell already has a different key4hep release active, `setup.sh` stops instead of mixing
the two environments. Start a fresh shell without that release and source `setup.sh` again.

Inside a container, step 5 is skipped and `setup.sh` says so: `.env` records absolute paths and
is read by an editor running on the host, so writing the container's mount point into it would
stop the notebooks working there. Source `setup.sh` on the host as well when you open notebooks
there.

Steps 3 to 5 exist for the notebooks. An editor that starts a Jupyter kernel does not inherit
your shell, so it needs an interpreter it can find (`.venv`) and the environment containing the
Python analysis packages and repository location (`.env`). Both are ignored by git and can be
deleted and recreated at any time by sourcing `setup.sh` again.

### Using the notebooks in VS Code

**Open `SoftwareTutorials` itself as the workspace folder**, not a parent directory. This is the
one thing that has to be right. VS Code applies `${workspaceFolder}/.env` to the interpreter it
launches, and `.env` is what carries the key4hep runtime; if the workspace folder is a level
above, VS Code looks for the wrong `.env`, finds nothing, and the notebook fails with
`ModuleNotFoundError: No module named 'awkward'`.

With the repository open as the workspace folder, source `setup.sh`, then in a notebook choose
**Select Kernel** → **Python Environments** and pick `.venv/bin/python` (shown as *DRDCalo
Tutorial*). No kernel has to be registered, and there is no port forwarding because everything
runs over the existing Remote-SSH connection.

If you must keep a parent directory as the workspace folder, point VS Code at the right file
instead, in that workspace's `.vscode/settings.json`:

``` json
{
    "python.envFile": "${workspaceFolder}/SoftwareTutorials/.env"
}
```

If a notebook reports a missing module, the captured environment is stale: source `setup.sh`
again and restart the kernel. If VS Code offers to install packages, that means it is running an
interpreter without the key4hep stack — fix the workspace folder or `python.envFile` rather than
accepting the install, which cannot make that environment work.

### Disk space

`ddsim` writes a large EDM4hep file: the 500 events configured in the steering files produce
roughly 600 MB, and each tutorial writes its own. If your home directory has a small quota,
write the output elsewhere:

``` bash
ddsim --steeringFile simplecalo1/sc1SteeringFile.py --outputFile /tmp/simplecalo1.root
```

or lower `SIM.numberOfEvents`; 100 events are already plenty for the energy resolution fit.

The Hands-on 6 notebooks and all Gaudi exercises remain usable without generating that large
file: they share the bundled 10-event `DD4hepTutorials/data/simplecalo2_sample.root`. A locally
generated `DD4hepTutorials/simplecalo2.root` is preferred automatically by the notebooks when
present; the Gaudi exercises stay on the small sample unless `--IOSvc.Input` says otherwise.
Both rules live in `python/drdcalo_tutorials/__init__.py`, which is where every tutorial
resolves its input and output paths.
