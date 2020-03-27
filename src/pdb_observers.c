/**
 * @file   pdb_observers.c
 * @author Lucas Peixoto <lucaspeixotoac@gmail.com>
 * 
 * 
 */

#include <zephyr.h>
#include "pdb.h"
#include "pdb_observers.h"

#ifdef PDB_OBSERVER_CREATE
#undef PDB_OBSERVER_CREATE
#endif

#define PDB_OBSERVER_CREATE(_nm, _sz) \
    K_MSGQ_DEFINE(_nm##_event_queue, sizeof(pdb_event_t), _sz, 1);

#include "pdb_observers.def"
#undef PDB_OBSERVER_CREATE

#include "pdb_observers_thread.def"



