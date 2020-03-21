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

int pdb_property_get(pdb_property_e id, u8_t *property_value, size_t size)
{
    int error               = 0;
    pdb_property_t *property = pdb_property_get_ref(id);
    if (property && property->get) {
        error = property->get(id, property_value, size);
        if (error) {
            printk("Current property get: %d, error code: %d\n", id, error);
        }
    } else {
        printk("The property #%d does not have a get implementation.\n", id);
    }
    return error;
}

int pdb_property_get_private(pdb_property_e id, u8_t *property_value, size_t size)
{
    return 0;
}

int pdb_property_set(pdb_property_e id, u8_t *property_value, size_t size)
{
    int error               = 0;
    int valid               = 1;
    pdb_property_t *property = pdb_property_get_ref(id);
    if (property && property->set) {
        if (property->validate) {
            valid = property->validate(property_value, size);
        }
        if (valid) {
            error = property->set(id, property_value, size);
            if (error) {
                printk("Current property set: %d, error code: %d\n", id, error);
            }
        } else {
            error = -EINVAL;
        }
    } else {
        printk("The property %d is read only.\n", id);
        error = -ENODEV;
    }
    return error;
}

int pdb_property_set_private(pdb_property_e id, u8_t *property_value, size_t size)
{
    return 0;
}


u8_t pdb_u8(pdb_property_e id, int *error)
{
    u8_t temp = 0;
    if (error) {
        *error = pdb_property_get(id, PDB_REF(temp));
    } else {
        pdb_property_get(id, PDB_REF(temp));
    }
    return temp;
}
u16_t pdb_u16(pdb_property_e id, int *error)
{
    u16_t temp = 0;
    if (error) {
        *error = pdb_property_get(id, PDB_REF(temp));
    } else {
        pdb_property_get(id, PDB_REF(temp));
    }
    return temp;
}
u32_t pdb_u32(pdb_property_e id, int *error)
{
    u32_t temp = 0;
    if (error) {
        *error = pdb_property_get(id, PDB_REF(temp));
    } else {
        pdb_property_get(id, PDB_REF(temp));
    }
    return temp;
}
u64_t pdb_u64(pdb_property_e id, int *error)
{
    u64_t temp = 0;
    if (error) {
        *error = pdb_property_get(id, PDB_REF(temp));
    } else {
        pdb_property_get(id, PDB_REF(temp));
    }
    return temp;
}

int pdb_buffer_clear(pdb_buffer_t *buffer)
{
    memset(buffer->content, 0, PDB_MAX_PROPERTY_SIZE);
    buffer->size = 0;
    return 0;
}

int pdb_buffer_push_data(pdb_buffer_t *buffer, u8_t *data, size_t size)
{
    if (size > 0 && ((buffer->size + size) <= PDB_MAX_PROPERTY_SIZE)) {
        u8_t *ptr = &buffer->content[0] + buffer->size;
        memcpy(ptr, data, size);
        buffer->size += (u8_t) size;
        return 0;
    }
    return -EINVAL;
}

int pdb_buffer_pop_data(pdb_buffer_t *buffer, u8_t *data, size_t size)
{
    u8_t *ptr  = &buffer->content[0];
    s32_t jump = buffer->size - size;
    if (jump >= 0) {
        ptr = ptr + jump;
        memcpy((void *) data, (void *) ptr, size);
        memset((void *) ptr, 0, size);
        buffer->size -= size;
        return 0;
    }
    return -EINVAL;
}

void pdb_thread()
{
    return;
}

