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
file(GLOB sources
  ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp
)

file(GLOB headers
  ${CMAKE_CURRENT_SOURCE_DIR}/include/*.hh
)

add_library(sdaction SHARED ${sources} ${headers})

target_include_directories(sdaction PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

set_target_properties(sdaction PROPERTIES PUBLIC_HEADER "${headers}")

target_link_libraries(
  sdaction
  DD4hep::DDCore
  DD4hep::DDG4
)

dd4hep_generate_rootmap(sdaction)

install(TARGETS sdaction EXPORT ${CMAKE_PROJECT_NAME}Targets
  LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}" COMPONENT shlib
  PUBLIC_HEADER DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}" COMPONENT dev
)
