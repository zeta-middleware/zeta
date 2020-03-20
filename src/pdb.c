#include <nvs/nvs.h>
#include <string.h>
#include <zephyr.h>

#include "pdb.h"

/* Checking if PROPERTY_CREATE is defined and undef it */
#ifdef PROPERTY_CREATE
#undef PROPERTY_CREATE
#endif

/* Defining PROPERTY_CREATE for properties generating */
#define PROPERTY_CREATE(_name, _bytes, _validate, _get, _set, _in_flash, _observers, _id) \
    {                                                                   \
     .name = (char *) #_name,                                           \
     .data = (u8_t[]){[0 ... sizeof(u8_t) * _bytes] = 0},               \
     .validate = _validate,                                             \
     .get = _get,                                                       \
     .set = _set,                                                       \
     .size = sizeof(u8_t) * _bytes,                                     \
     .in_flash = _in_flash,                                             \
     .changed = 0,                                                      \
     .observers = _observers,                                           \
     .id = PDB_##_name##_PROPERTY                                       \
    },

static pdb_property_t __properties[PDB_PROPERTY_COUNT] = {
#include "properties.def"
};

#undef PROPERTY_CREATE

size_t pdb_property_get_size(pdb_property_e id, int *error)
{
    size_t size      = 0;
    pdb_property_t *p = pdb_property_get_ref(id);
    if (p) {
        size = (size_t) p->size;
    } else {
        if (error) {
            *error = -EINVAL;
        }
    }
    return size;
}

pdb_property_t *pdb_property_get_ref(pdb_property_e property)
{
    if (property < PDB_PROPERTY_COUNT) {
        return &__properties[property];
    } else {
        return NULL;
    }
}
