/**
 * @file   pdb_observers.h
 * @author Lucas Peixoto <lucaspeixotoac@gmail.com>
 * 
 * @brief  
 * 
 * 
 */

#ifndef PDB_OBSERVERS_H_
#define PDB_OBSERVERS_H_

#include "pdb.h"

#ifdef PDB_OBSERVER_CREATE
#undef PDB_OBSERVER_CREATE
#endif

#define PDB_OBSERVER_CREATE(_nm, _sz) \
    extern struct k_msgq _nm##_event_queue;

#include "pdb_observers.def"
#undef PDB_OBSERVER_CREATE

#define PDB_OBSERVER_THREAD_CREATE(_nm, _sz, _prior, _cb);              \
    void _cb(pdb_event_t *event);                                       \
    int _nm##_module_thread(void) {                                     \
        pdb_event_t event = {0};                                        \
        while(1) {                                                      \
            if (!k_msgq_get(&_nm##_event_queue, &event, K_SECONDS(10))) { \
                _cb(&event);                                            \
            }                                                           \
        }                                                               \
    }                                                                   \
    K_THREAD_DEFINE(_nm##_module_thread_id, _sz, _nm##_module_thread, NULL, NULL, NULL, _prior, 0, K_NO_WAIT); 


#endif
