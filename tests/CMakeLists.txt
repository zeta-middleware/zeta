cmake_minimum_required(VERSION 3.13.1)

set(BOARD_ROOT ${CMAKE_SOURCE_DIR})

include(zeta.cmake NO_POLICY_SCOPE)

find_package(Zephyr HINTS $ENV{ZEPHYR_BASE})
project(Zeta)


# Generate version file
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Add header directories
list(APPEND HEADERS
    "${PROJECT_BINARY_DIR}/zephyr/include/generated"
    "${PROJECT_SOURCE_DIR}/include"
    )

list(APPEND SOURCES
    "${PROJECT_SOURCE_DIR}/src/test_main.c"
    "${PROJECT_SOURCE_DIR}/src/test_functions.c"
    )

target_include_directories(app PRIVATE ${HEADERS})
target_sources(app PRIVATE ${SOURCES})
