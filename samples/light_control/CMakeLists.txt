# SPDX-License-Identifier: Apache-2.0
cmake_minimum_required(VERSION 3.13.1)

include(zeta.cmake NO_POLICY_SCOPE)
include($ENV{ZEPHYR_BASE}/cmake/app/boilerplate.cmake NO_POLICY_SCOPE)
project(light_control)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

list(APPEND HEADERS "${CMAKE_CURRENT_LIST_DIR}/zeta/include/")

list(APPEND SOURCES "${PROJECT_SOURCE_DIR}/src/peripheral.c"
     "${PROJECT_SOURCE_DIR}/src/core.c"
     "${PROJECT_SOURCE_DIR}/src/net.c""${PROJECT_SOURCE_DIR}/src/main.c")

message("Headers: ${HEADERS}")
message("Soucers: ${SOURCES}")
include_directories(${HEADERS})
target_sources(app PRIVATE ${SOURCES})
