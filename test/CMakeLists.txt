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

add_test(NAME test_EventStats
                WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/GaudiTutorial/data
                COMMAND k4run ${PROJECT_SOURCE_DIR}/GaudiTutorial/EventStats/options/runEventStatsSolution.py --IOSvc.Input ${PROJECT_SOURCE_DIR}/GaudiTutorial/data/simpleCalo_simulation.root --IOSvc.Output ${PROJECT_SOURCE_DIR}/GaudiTutorial/data/simpleCalo_eventStats.root)

add_test(NAME test_MoliereRadius
                WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/GaudiTutorial/data
                COMMAND k4run ${PROJECT_SOURCE_DIR}/GaudiTutorial/MoliereRadiusFunctional/options/runMoliereRadiusSolution.py --IOSvc.Input ${PROJECT_SOURCE_DIR}/GaudiTutorial/data/simpleCalo_simulation.root --IOSvc.Output ${PROJECT_SOURCE_DIR}/GaudiTutorial/data/simpleCalo_moliereRadius.root)

add_test(NAME test_RandomNoiseDigitizer
                WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/GaudiTutorial/data
                COMMAND k4run ${PROJECT_SOURCE_DIR}/GaudiTutorial/RandomNoiseDigitizer/options/runRandomNoiseDigitizerSolution.py --IOSvc.Input ${PROJECT_SOURCE_DIR}/GaudiTutorial/data/simpleCalo_simulation.root --IOSvc.Output ${PROJECT_SOURCE_DIR}/GaudiTutorial/data/simpleCalo_noiseDigitizer.root)

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
${PROJECT_BINARY_DIR}/GaudiTutorial/EventStats/genConfDir:\
${PROJECT_BINARY_DIR}/GaudiTutorial/MoliereRadiusFunctional/genConfDir:\
${PROJECT_BINARY_DIR}/GaudiTutorial/RandomNoiseDigitizer/genConfDir:\
${PROJECT_BINARY_DIR}/${PROJECT_NAME}/genConfDir:\
${CMAKE_CURRENT_BINARY_DIR}/genConfDir:\
$ENV{PYTHONPATH};\
")
get_property(test_names DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY TESTS)
set_tests_properties(${test_names} PROPERTIES ENVIRONMENT "${test_environment}")

message(STATUS "================ Test Environment ================")
message(STATUS "${test_environment}")
message(STATUS "=================================================")
