/**
 * @file   pdb_observers.c
 * @author Lucas Peixoto <lucaspeixotoac@gmail.com>
 * 
 * 
 */

#include <zephyr.h>
#include "pdb.h"
#include "pdb_observers.h"

#ifdef PDB_MODULE_CREATE
#undef PDB_MODULE_CREATE
#endif

#define PDB_MODULE_CREATE(_nm, _sz, _prior, _cb) \
    K_MSGQ_DEFINE(_nm##_module_event_queue, sizeof(pdb_event_t), 16, 1); \
    K_THREAD_DEFINE(_nm##_module_thread_id, _sz, _nm##_module_thread, NULL, NULL, NULL, _prior, 0, K_NO_WAIT); \
    int _nm##_module_thread(void) {                                     \
        pdb_event_t event = {0};                                        \
        while(1) {                                                      \
            if (!k_msgq_get(&_nm##_module_event_queue, &event, K_SECONDS(10))) { \
                _cb(&event);                                            \
            }                                                           \
        }                                                               \
    }

#include "observers.def"

#undef PDB_MODULE_CREATE


