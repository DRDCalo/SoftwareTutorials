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


project(SoftwareTutorials LANGUAGES CXX)

# please keep this layout for version setting, used by the automatic tagging script
set(PACKAGE_VERSION_MAJOR 1)
set(PACKAGE_VERSION_MINOR 2)
set(PACKAGE_VERSION_PATCH 3)

set(PACKAGE_VERSION "${PACKAGE_VERSION_MAJOR}.${PACKAGE_VERSION_MINOR}.${PACKAGE_VERSION_PATCH}")

include(cmake/Key4hepConfig.cmake)

include(GNUInstallDirs)

option(SOFTWARETUTORIALS_BUILD_GAUDITUTORIAL "Build the GaudiTutorial directory" ON)
option(SOFTWARETUTORIALS_BUILD_DD4HEPTUTORIALS "Build the DD4hepTutorials directory" ON)

if(NOT SOFTWARETUTORIALS_BUILD_GAUDITUTORIAL AND NOT SOFTWARETUTORIALS_BUILD_DD4HEPTUTORIALS)
  message(FATAL_ERROR "Both SOFTWARETUTORIALS_BUILD_GAUDITUTORIAL and SOFTWARETUTORIALS_BUILD_DD4HEPTUTORIALS are OFF: at least one must be ON.")
endif()

if(SOFTWARETUTORIALS_BUILD_GAUDITUTORIAL)
  add_subdirectory(GaudiTutorial)
endif()
if(SOFTWARETUTORIALS_BUILD_DD4HEPTUTORIALS)
  add_subdirectory(DD4hepTutorials)
endif()

include(CTest)
if(BUILD_TESTING)
  add_subdirectory(test)
endif()

include(cmake/CreateProjectConfig.cmake)