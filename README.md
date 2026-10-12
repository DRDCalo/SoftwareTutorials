# SoftwareTutorials


This repository hosts a variety of software tutorials related to DRDCalo (formerly DRD6) Collaboration activities.
It includes the tutorials on DD4hep and Gaudi, presented in the 2nd and 4th Collaboration Meeting respectively.

Ideally, this repository is expanded with relevant tutorials in the future.

The tutorials can be completed by following the presentation slides linked in the corresponding sub-directories.


## Compilation

The repository is a single CMake project that builds both `DD4hepTutorials`
and `GaudiTutorial`. It requires the Key4hep environment on an AlmaLinux 9
machine with `/cvmfs` mounted, such as lxplus.

First, clone the repository:

```bash
git clone https://github.com/DRD6/SoftwareTutorials.git
cd SoftwareTutorials
```

Then build and install everything:

```bash
source /cvmfs/sw.hsf.org/key4hep/setup.sh
k4_local_repo
mkdir build install
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
make install -j6
```

To build only one of the two directories, disable the other one at configure
time:

```bash
# Build only DD4hepTutorials
cmake .. -DCMAKE_INSTALL_PREFIX=../install -DSOFTWARETUTORIALS_BUILD_GAUDITUTORIAL=OFF

# Build only GaudiTutorial
cmake .. -DCMAKE_INSTALL_PREFIX=../install -DSOFTWARETUTORIALS_BUILD_DD4HEPTUTORIALS=OFF
```

The `k4_local_repo` command configures the environment so that the locally
installed modules are found. Run it from the project directory in every new
shell.

More tutorial-specific information is available in the
[DD4hepTutorials README](DD4hepTutorials/README.md) and the
[GaudiTutorial README](GaudiTutorial/README.md).
