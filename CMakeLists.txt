cmake_minimum_required(VERSION 3.13.1)

set(BOARD_ROOT ${CMAKE_SOURCE_DIR})

include($ENV{ZEPHYR_BASE}/cmake/app/boilerplate.cmake NO_POLICY_SCOPE)
project(Zeta)

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
    "${PROJECT_BINARY_DIR}/zephyr/src/generated/zeta.c"
    "${PROJECT_BINARY_DIR}/zephyr/src/generated/zeta_threads.c"
    )

if(CONFIG_ZTEST)
  message("Ztest enabled, adding test_main.c and user source files to source files list.")
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
    COMMAND python3 ${PROJECT_SOURCE_DIR}/zeta_generate.py -f ../test/zeta_test.yaml 
    BYPRODUCTS "${PROJECT_BINARY_DIR}/zephyr/src/generated/zeta.c" "${PROJECT_BINARY_DIR}/zephyr/src/generated/zeta_threads.c"
    COMMENT "Generating files from templates"
    )
  add_dependencies(app generateFiles)
else()
  message("Ztest disabled, adding main.c and user source files to source files list.")
  list(APPEND SOURCES
    "${PROJECT_SOURCE_DIR}/src/main.c"
    )
  # Generating properties macro create
  add_custom_target(
    generateFiles ALL
    COMMAND python3 ${PROJECT_SOURCE_DIR}/zeta_generate.py -f ../zeta.yaml 
    BYPRODUCTS "${PROJECT_BINARY_DIR}/zephyr/src/generated/zeta.c" "${PROJECT_BINARY_DIR}/zephyr/src/generated/zeta_threads.c"
    COMMENT "Generating files from templates"
    )
  add_dependencies(app generateFiles)
  
endif()  

target_include_directories(app PRIVATE ${HEADERS})
target_sources(app PRIVATE ${SOURCES})

#####################################
# Setting tests                     #
#####################################

# enable_testing()
# # list(APPEND TEST_HEADERS
# #     "build/include/generated"
# #     "build/zephyr/include/generated"
# #     "include"
# #     )

# add_executable(testandoCtest test/src/main_ctest.c)
# target_include_directories(testandoCtest PRIVATE ${HEADERS})
# add_test(TestandoCtest testandoCtest)
