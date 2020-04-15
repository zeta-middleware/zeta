# TODO: Gerar os arquivos dentro da pasta build
cmake_minimum_required(VERSION 3.13.1)

set(BOARD_ROOT ${CMAKE_SOURCE_DIR})

include($ENV{ZEPHYR_BASE}/cmake/app/boilerplate.cmake NO_POLICY_SCOPE)
project(Pdb)

# Generate version file
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Generating properties macro create
add_custom_target(
  generateFiles ALL
  COMMAND python3 ${PROJECT_SOURCE_DIR}/mount_system.py ${CMAKE_CURRENT_SOURCE_DIR}
  BYPRODUCTS "${PROJECT_BINARY_DIR}/zephyr/src/generated/pdb.c" "${PROJECT_BINARY_DIR}/zephyr/src/generated/pdb_threads.c"
  COMMENT "Generating files from templates"
  )
add_dependencies(app generateFiles)

# Add header directories
list(APPEND HEADERS
    "${PROJECT_BINARY_DIR}/include/generated"
    "${PROJECT_BINARY_DIR}/zephyr/include/generated"
    "${PROJECT_SOURCE_DIR}/include"
    )

# Add source files
list(APPEND SOURCES
    "${PROJECT_SOURCE_DIR}/src/main.c"
    "${PROJECT_BINARY_DIR}/zephyr/src/generated/pdb.c"
    "${PROJECT_BINARY_DIR}/zephyr/src/generated/pdb_threads.c"
)

include_directories(${HEADERS})
target_sources(app PRIVATE ${SOURCES})
