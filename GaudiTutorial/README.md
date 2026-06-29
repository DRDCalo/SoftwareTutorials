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
# GaudiTutorials for DRD6

This repository hosts tutorials for using the *Gaudi* software as part of the larger *key4hep* ecosystem.

It contains hands-on exercises to get familiar with Gaudi steering files and algorithms.
To experiment with the tutorial, you can follow [this presentation](https://indico.cern.ch/event/1551941/sessions/613344/#20250918) at the 4th DRD-Calo Collaboration Meeting, which covers the *EventStats*, *RandomNoiseDigitizer*, and *MoliereRadius* exercises.

This README contains a short description for each of the hosted exercises.
The exercises run on data that has been created with with the *simplecalo* calorimeter from the **DD4hepTutorials** exercises.
An example data file will be downloaded automatically when compiling the repository.

## EventStats

The goal of this exercise is to become familiar with the Gaudi steering file.
For this purpose, an EventStats algorithm is provided, which saves the energy barycentre and total energy for each event using the `podio::UserDataCollection`.

You should adapt the steering file `runEventStats.py` in the `EventStats/options' folder such that this algorithm is executed on the data.
A solution file is provided.

## RandomNoiseDigitizer

The goal of this exercise is to complete a simple digitising algorithm from a skeleton file.

## MoliereRadius

The goal of this exercise is to complete a Gaudi algorithm to compute a physics value from the data, and to revise adding algorithms to the steering file.
Solution files are provided.
