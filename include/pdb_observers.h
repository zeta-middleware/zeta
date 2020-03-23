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

#ifdef PDB_MODULE_CREATE
#undef PDB_MODULE_CREATE
#endif

#define PDB_MODULE_CREATE(_nm, _sz, _prior, _cb) \
    int _nm##_module_thread(void); \
    struct k_msgq _nm##_module_event_queue;

#include "observers.def"

#undef PDB_MODULE_CREATE


#endif
