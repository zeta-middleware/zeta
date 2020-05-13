cmake_minimum_required(VERSION 3.13.1)

include(zeta.cmake NO_POLICY_SCOPE)
include($ENV{ZEPHYR_BASE}/cmake/app/boilerplate.cmake NO_POLICY_SCOPE)
project(project_name)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include_directories(${HEADERS})
target_sources(app PRIVATE ${SOURCES})
