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

set(SIM_FILE ${PROJECT_SOURCE_DIR}/DD4hepTutorials/data/simplecalo2_sample.root)
if(NOT EXISTS ${SIM_FILE})
    message(FATAL_ERROR "Bundled tutorial input not found: ${SIM_FILE}")
endif()

# Everything the tests write goes into the build directory: the option files are
# named absolutely and the working directory is the build tree, so a `ctest` run
# leaves the checkout untouched.
set(GAUDI_OPTIONS ${PROJECT_SOURCE_DIR}/GaudiTutorial)

add_test(NAME test_EventStats
                WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
                COMMAND k4run ${GAUDI_OPTIONS}/EventStats/options/runEventStatsSolution.py --IOSvc.Input ${SIM_FILE} --IOSvc.Output ${CMAKE_CURRENT_BINARY_DIR}/simpleCalo_eventStats.root --EventStats.HistogramFile ${CMAKE_CURRENT_BINARY_DIR}/debugEventStats.root)

# The multithreaded configuration is what motivates the mutex around the shared
# histograms in EventStats.cpp, so it is exercised as well. Ten events across six
# threads is cheap, and ThreadSanitizer aside it is what catches an unprotected
# TH1::Fill turning into a crash or a corrupted histogram.
add_test(NAME test_EventStatsMultithreading
                WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
                COMMAND k4run ${GAUDI_OPTIONS}/EventStats/options/runEventStatsMultithreading.py --IOSvc.Input ${SIM_FILE} --IOSvc.Output ${CMAKE_CURRENT_BINARY_DIR}/simpleCalo_eventStats_multithreaded.root --EventStats.HistogramFile ${CMAKE_CURRENT_BINARY_DIR}/debugEventStats_multithreaded.root)

add_test(NAME test_MoliereRadius
                WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
                COMMAND k4run ${GAUDI_OPTIONS}/MoliereRadiusFunctional/options/runMoliereRadiusSolution.py --IOSvc.Input ${SIM_FILE} --IOSvc.Output ${CMAKE_CURRENT_BINARY_DIR}/simpleCalo_moliereRadius.root)

add_test(NAME test_RandomNoiseDigitizer
                WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
                COMMAND k4run ${GAUDI_OPTIONS}/RandomNoiseDigitizer/options/runRandomNoiseDigitizerSolution.py --IOSvc.Input ${SIM_FILE} --IOSvc.Output ${CMAKE_CURRENT_BINARY_DIR}/simpleCalo_noiseDigitizer.root)

# For LD_LIBRARY_PATH
# ${PROJECT_BINARY_DIR}                                         # The files <plugins>.components and <plugins>.confdb are here
# ${PROJECT_BINARY_DIR}/${PROJECT_NAME}                         # The plugins (.so) are here
# ${CMAKE_CURRENT_BINARY_DIR}                                   # The tests (.so) are here if there are algorithms in the tests
# ${CMAKE_CURRENT_BINARY_DIR}/genConfDir/${CURRENT_DIR_NAME}    # The files <test>.components and <test>.confdb are here
# For PYTHONPATH
# ${PROJECT_BINARY_DIR}/${PROJECT_NAME}/genConfDir              # The genConfDir of the plugins
# ${CMAKE_CURRENT_BINARY_DIR}/genConfDir                        # The genConfDir of the tests if there are algorithms in the tests

# If the package also includes python code to be imported in a module with the same as the package name,
# then the Python files have to be copied in the build directory to
# ${PROJECT_BINARY_DIR}/${PROJECT_NAME}/genConfDir
# after genConfDir has been populated by Gaudi
# See, for example:
# https://github.com/key4hep/k4FWCore/blob/42497b71c23425a3a26648f30a1285a499dcda28/test/k4FWCoreTest/CMakeLists.txt#L71


# Check that every notebook is well formed and that its code cells are valid Python.
add_test(NAME test_NotebooksValid
                WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
                COMMAND python ${CMAKE_CURRENT_SOURCE_DIR}/check_notebooks.py)

# Execute the solution notebook against the bundled sample by default. Developers can still
# override SIMPLECALO2_FILE at configure time to exercise a full simulation output.
if(NOT DEFINED SIMPLECALO2_FILE)
    set(SIMPLECALO2_FILE
        ${PROJECT_SOURCE_DIR}/DD4hepTutorials/data/simplecalo2_sample.root)
endif()
if(NOT EXISTS ${SIMPLECALO2_FILE})
    message(FATAL_ERROR "EDM4hep notebook input not found: ${SIMPLECALO2_FILE}")
endif()

add_test(NAME test_ReadEdm4hepNotebook
                WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
                COMMAND jupyter nbconvert --to notebook --execute
                        ${PROJECT_SOURCE_DIR}/DD4hepTutorials/notebooks/readEdm4hepSolution.ipynb
                        --output ${CMAKE_CURRENT_BINARY_DIR}/readEdm4hepSolution_executed.ipynb)

# The Section 1 notebook runs on the same bundled file, which carries the same
# simplecaloRO collection. SIMPLECALO1_FILE keeps it off any full simulation that
# happens to be sitting in the source tree.
add_test(NAME test_CellEnergySumNotebook
                WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
                COMMAND jupyter nbconvert --to notebook --execute
                        ${PROJECT_SOURCE_DIR}/DD4hepTutorials/notebooks/plot_cell_energy_sum.ipynb
                        --output ${CMAKE_CURRENT_BINARY_DIR}/plot_cell_energy_sum_executed.ipynb)

get_filename_component(CURRENT_DIR_NAME ${CMAKE_CURRENT_SOURCE_DIR} NAME)

set(test_environment "\
LD_LIBRARY_PATH=\
${PROJECT_BINARY_DIR}:\
${PROJECT_BINARY_DIR}/GaudiTutorial/EventStats:\
${PROJECT_BINARY_DIR}/GaudiTutorial/MoliereRadiusFunctional:\
${PROJECT_BINARY_DIR}/GaudiTutorial/RandomNoiseDigitizer:\
${PROJECT_BINARY_DIR}/${PROJECT_NAME}:\
${CMAKE_CURRENT_BINARY_DIR}:\
${CMAKE_CURRENT_BINARY_DIR}/genConfDir/${CURRENT_DIR_NAME}:\
$ENV{LD_LIBRARY_PATH};\
\
PYTHONPATH=\
${PROJECT_SOURCE_DIR}/python:\
${PROJECT_BINARY_DIR}/GaudiTutorial/EventStats/genConfDir:\
${PROJECT_BINARY_DIR}/GaudiTutorial/MoliereRadiusFunctional/genConfDir:\
${PROJECT_BINARY_DIR}/GaudiTutorial/RandomNoiseDigitizer/genConfDir:\
${PROJECT_BINARY_DIR}/${PROJECT_NAME}/genConfDir:\
${CMAKE_CURRENT_BINARY_DIR}/genConfDir:\
$ENV{PYTHONPATH};\
")
get_property(test_names DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY TESTS)
set_tests_properties(${test_names} PROPERTIES ENVIRONMENT "${test_environment}")

# Must come after set_tests_properties() above, which would otherwise overwrite it.
if(TEST test_ReadEdm4hepNotebook)
    set_property(TEST test_ReadEdm4hepNotebook APPEND PROPERTY
                 ENVIRONMENT "SIMPLECALO2_FILE=${SIMPLECALO2_FILE}")
endif()
if(TEST test_CellEnergySumNotebook)
    set_property(TEST test_CellEnergySumNotebook APPEND PROPERTY
                 ENVIRONMENT "SIMPLECALO1_FILE=${SIM_FILE}")
endif()

message(STATUS "================ Test Environment ================")
message(STATUS "${test_environment}")
message(STATUS "=================================================")
