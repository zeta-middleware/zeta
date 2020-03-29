cmake_minimum_required(VERSION 3.13.1)

set(BOARD_ROOT ${CMAKE_SOURCE_DIR})

include($ENV{ZEPHYR_BASE}/cmake/app/boilerplate.cmake NO_POLICY_SCOPE)
project(Pdb)

# Generate version file
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Generating properties macro create
add_custom_target(
  generatePropertiesTarget
  COMMAND python3 ${PROJECT_SOURCE_DIR}/generate_properties.py
  )
add_dependencies(app generatePropertiesTarget)

# Add header directories
list(APPEND HEADERS
    "${PROJECT_BINARY_DIR}/include/generated"
    "${PROJECT_BINARY_DIR}/zephyr/include/generated"
    "${PROJECT_SOURCE_DIR}/include"
    "${PROJECT_SOURCE_DIR}/include/generated"
    )

# Add source files
list(APPEND SOURCES
    "${PROJECT_SOURCE_DIR}/src/main.c"
    "${PROJECT_SOURCE_DIR}/src/pdb.c"
    "${PROJECT_SOURCE_DIR}/src/pdb_observers.c"
    "${PROJECT_SOURCE_DIR}/src/pdb_unit_tests.c"
    "${PROJECT_SOURCE_DIR}/src/pdb_validators.c"

)

include_directories(${HEADERS})
target_sources(app PRIVATE ${SOURCES})
