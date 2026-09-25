#[[
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
]]

CMAKE_MINIMUM_REQUIRED(VERSION 3.12)

project(GaudiTutorial LANGUAGES CXX)

include(GNUInstallDirs)

# Keep this directory self-contained: these dependencies and settings must be
# available both when GaudiTutorial is the top-level project and when it is
# included by SoftwareTutorials.
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Gaudi REQUIRED)
find_package(ROOT REQUIRED COMPONENTS RIO Tree Hist)
find_package(EDM4HEP REQUIRED)
find_package(k4FWCore REQUIRED)
find_package(DD4hep REQUIRED)

add_subdirectory(EventStats)
add_subdirectory(MoliereRadiusFunctional)
add_subdirectory(RandomNoiseDigitizer)
