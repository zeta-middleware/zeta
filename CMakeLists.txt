# TODO: Gerar os arquivos dentro da pasta build
cmake_minimum_required(VERSION 3.13.1)

set(BOARD_ROOT ${CMAKE_SOURCE_DIR})

include($ENV{ZEPHYR_BASE}/cmake/app/boilerplate.cmake NO_POLICY_SCOPE)
project(Pdb)

# Generate version file
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Add header directories
list(APPEND HEADERS
    "${PROJECT_BINARY_DIR}/include/generated"
    "${PROJECT_BINARY_DIR}/zephyr/include/generated"
    "${PROJECT_SOURCE_DIR}/include"
    )

# Add source files
list(APPEND SOURCES
    "${PROJECT_BINARY_DIR}/zephyr/src/generated/pdb.c"
    "${PROJECT_BINARY_DIR}/zephyr/src/generated/pdb_threads.c"
    )

if(CONFIG_ZTEST)
  message("Ztest enabled, adding test_main.c file to source files.")
  list(APPEND HEADERS
    "${PROJECT_SOURCE_DIR}/test/include"
    )
  list(APPEND SOURCES
    "${PROJECT_SOURCE_DIR}/test/src/test_main.c"
    "${PROJECT_SOURCE_DIR}/test/src/test_functions.c"
    )
  # Generating properties macro create
  add_custom_target(
    generateFiles ALL
    COMMAND python3 ${PROJECT_SOURCE_DIR}/mount_system.py -f ../test/pdb_test.yaml 
    BYPRODUCTS "${PROJECT_BINARY_DIR}/zephyr/src/generated/pdb.c" "${PROJECT_BINARY_DIR}/zephyr/src/generated/pdb_threads.c"
    COMMENT "Generating files from templates"
    )
  add_dependencies(app generateFiles)
else()
  message("Ztest disabled, adding main.c file to source files.")
  list(APPEND SOURCES
    "${PROJECT_SOURCE_DIR}/src/main.c"
    )
  # Generating properties macro create
  add_custom_target(
    generateFiles ALL
    COMMAND python3 ${PROJECT_SOURCE_DIR}/mount_system.py -f ../pdb.yaml 
    BYPRODUCTS "${PROJECT_BINARY_DIR}/zephyr/src/generated/pdb.c" "${PROJECT_BINARY_DIR}/zephyr/src/generated/pdb_threads.c"
    COMMENT "Generating files from templates"
    )
  add_dependencies(app generateFiles)
  
endif()  

include_directories(${HEADERS})
target_sources(app PRIVATE ${SOURCES})
