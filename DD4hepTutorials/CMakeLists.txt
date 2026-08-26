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

# DD4hep 1.36 still relies on CMake's legacy FindBoost compatibility mode.
if(POLICY CMP0167)
  cmake_policy(SET CMP0167 OLD)
endif()

project(DD4hepTutorials)

include(GNUInstallDirs)

find_package(DD4hep REQUIRED)

dd4hep_set_compiler_flags()
dd4hep_configure_output()

# Collect all source files
set(SOURCES
  ${PROJECT_SOURCE_DIR}/simplecalo1/src/simplecalo1.cpp
  ${PROJECT_SOURCE_DIR}/simplecalo2/src/simplecalo2.cpp
)
add_compile_options(-Wno-unused-variable)

# Create a single plugin
dd4hep_add_plugin(${PROJECT_NAME} SOURCES ${SOURCES} USES
  DD4hep::DDCore
  DD4hep::DDCond
  ROOT::Core
  ROOT::Geom
  ROOT::GenVector
  ROOT::MathCore
)

# Add both include directories
target_include_directories(${PROJECT_NAME} PRIVATE
  ${PROJECT_SOURCE_DIR}/simplecalo1/include
  ${PROJECT_SOURCE_DIR}/simplecalo2/include
)

add_subdirectory(sdaction)
