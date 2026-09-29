# SoftwareTutorials


This repository hosts a variety of software tutorials related to DRDCalo (formerly DRD6) Collaboration activities.
It includes the tutorials on DD4hep and Gaudi, presented in the 2nd and 4th Collaboration Meeting respectively.

Ideally, this repository is expanded with relevant tutorials in the future.

The tutorials can be completed by following the presentation slides linked in the corresponding sub-directories.


## Compilation

The tutorials can be compiled either together or independently. They require
the Key4hep environment on an AlmaLinux 9 machine with `/cvmfs` mounted, such
as lxplus.

First, clone the repository:

```bash
git clone https://github.com/DRD6/SoftwareTutorials.git
cd SoftwareTutorials
```

### Build both tutorials together

Run these commands from the `SoftwareTutorials` directory:

```bash
source /cvmfs/sw.hsf.org/key4hep/setup.sh
k4_local_repo
mkdir build install
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
make install -j6
```

This builds and installs both `DD4hepTutorials` and `GaudiTutorial`.

### Build only DD4hepTutorials

Run these commands from the `SoftwareTutorials` directory:

```bash
cd DD4hepTutorials
source /cvmfs/sw.hsf.org/key4hep/setup.sh
k4_local_repo
mkdir build install
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
make install -j6
```

The same commands work when `DD4hepTutorials` is checked out as a separate
repository: run them from its repository root, omitting the `cd` command.

### Build only GaudiTutorial

Run these commands from the `SoftwareTutorials` directory:

```bash
cd GaudiTutorial
source /cvmfs/sw.hsf.org/key4hep/setup.sh
k4_local_repo
mkdir build install
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
make install -j6
```

The `k4_local_repo` command configures the environment so that the locally
installed modules are found. Run it from the project directory in every new
shell.

More tutorial-specific information is available in the
[DD4hepTutorials README](DD4hepTutorials/README.md) and the
[GaudiTutorial README](GaudiTutorial/README.md).
