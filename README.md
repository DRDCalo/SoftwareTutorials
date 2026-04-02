# SoftwareTutorials


This repository hosts a variety of software tutorials related to DRDCalo (formerly DRD6) Collaboriation activities.
It includes the tutorials on DD4hep and Gaudi, presented in the 2nd and 4th Collaboration Meeting respectively.

Ideally, this repository is expanded with relevant tutorials in the future.

The tutorials can be completed by following the presentation slides linked in the corresponding sub-directories


## Compilation

These tutorials are made within the key4hep environment.
To compile and run them, access to an Alma9 machine with `/cvmfs/` mounted (e.g. lxplus) to source the key4hep stack is required.

To clone and build the repository, run the following commands:


``` bash
source /cvmfs/sw.hsf.org/key4hep/setup.sh
git clone https://github.com/DRD6/SoftwareTutorials.git
cd SoftwareTutorials
k4_local_repo
mkdir build install
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
make install -j6
```

The `k4_local_repo` command sets the environment variables and makes sure the local modules are found by the system.
It needs to be run in **every new shell**.
