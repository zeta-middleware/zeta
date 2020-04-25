# ################################################################# #
#                      FILE GENERATED BY ZetaCLI                    #
#                         DON'T EDIT THIS FILE                      #
# ################################################################# #

message(" Zeta >> Configure cmake")

execute_process(COMMAND ../../zeta gen -b "${CMAKE_CURRENT_LIST_DIR}/build" ${CMAKE_CURRENT_LIST_DIR}/zeta.yaml)
# add_dependencies(app zetaGenFiles) Add header directories
list(APPEND HEADERS "${CMAKE_CURRENT_LIST_DIR}/build/zeta/include/")

# Add source files
list(APPEND SOURCES "${CMAKE_CURRENT_LIST_DIR}/build/zeta/src/zeta.c"
     "${CMAKE_CURRENT_LIST_DIR}/build/zeta/src/zeta_threads.c")

list(APPEND CONF_FILE "${CMAKE_CURRENT_LIST_DIR}/zeta.conf")