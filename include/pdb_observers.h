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

#include "observers.def"

#undef PDB_OBSERVER_CREATE


#endif
