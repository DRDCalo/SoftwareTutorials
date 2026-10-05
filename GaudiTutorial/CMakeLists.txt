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
include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/Key4hepConfig.cmake)

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake ${CMAKE_MODULE_PATH})

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
find_package(onnxruntime)
if (NOT onnxruntime_FOUND)
  message(STATUS "Could not find onnxruntime (> 1.17.1). Looking for an older version")
  find_package(ONNXRuntime)
endif()

if(onnxruntime_FOUND OR ONNXRuntime_FOUND)
else()
  message(FATAL_ERROR "Failed to locate ONNXRuntime!")
endif()


# The exercises and their tests use this input file.  Keep the download in
# GaudiTutorial so it is also available when this directory is configured as a
# standalone project.
set(SIM_FILE ${CMAKE_CURRENT_SOURCE_DIR}/data/simpleCalo_simulation.root)
set(ML_PI_FILE ${CMAKE_CURRENT_SOURCE_DIR}/data/clusterID_pi-_1-20GeV_eval.root)
set(ML_E_FILE ${CMAKE_CURRENT_SOURCE_DIR}/data/clusterID_e-_1-20GeV_eval.root)
set(ML_MODEL ${CMAKE_CURRENT_SOURCE_DIR}/data/pointnet_simplecalo.onnx)

function(download_if_missing url destination)
    if(EXISTS "${destination}")
        message(STATUS "File already exists: ${destination}, skipping download.")
        return()
    endif()

    get_filename_component(destination_dir "${destination}" DIRECTORY)
    file(MAKE_DIRECTORY "${destination_dir}")

    set(temp_file "${destination}.part")
    file(DOWNLOAD "${url}" "${temp_file}"
         STATUS download_status
         TIMEOUT 120
         TLS_VERIFY ON)

    list(GET download_status 0 status_code)
    if(NOT status_code EQUAL 0)
        list(GET download_status 1 status_message)
        file(REMOVE "${temp_file}")
        message(FATAL_ERROR "Download failed: ${url}: ${status_message}")
    endif()

    file(RENAME "${temp_file}" "${destination}")
endfunction()

set(BASE_URL "https://fccsw.web.cern.ch/fccsw/tutorials/DRD6_2025_Ancona")

download_if_missing("${BASE_URL}/simpleCalo_simulation.root" "${SIM_FILE}")
download_if_missing("${BASE_URL}/clusterID_pi-_1-20GeV_eval.root" "${ML_PI_FILE}")
download_if_missing("${BASE_URL}/clusterID_e-_1-20GeV_eval.root" "${ML_E_FILE}")
download_if_missing("${BASE_URL}/pointnet_simplecalo.onnx" "${ML_MODEL}")

add_subdirectory(EventStats)
add_subdirectory(MoliereRadiusFunctional)
add_subdirectory(RandomNoiseDigitizer)
add_subdirectory(MLShowerID)
