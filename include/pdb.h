/*!
 * @file
 * @brief This is the abstraction information relative to NB hardware
 *
 */

#ifndef PDB_H_
#define PDB_H_

#include <stddef.h>
#include <zephyr/types.h>

/*!
 * @brief This is the NB thread stack size.
 * By default it has 512 bytes. Just change this if you are sure about it.
 */
#define PDB_THREAD_SIZE 1024
/*!
 * @brief This is the priority of the thread related to the system.
 */
#define PDB_THREAD_PRIORITY 5
#define PDB_MAX_PROPERTY_SIZE 12

#define PDB_REF(x) (u8_t *) &x, sizeof(x)


/* Checking if PROPERTY_CREATE is defined and undef it */
#ifdef PROPERTY_CREATE
#undef PROPERTY_CREATE
#endif

/* Defining PROPERTY_CREATE for enum generating */
#define PROPERTY_CREATE(_name, _bytes, _validate, _get, _set, _in_flash, _observers, _id) PDB_##_name##_PROPERTY,

typedef enum {
#include "properties.def"
              PDB_PROPERTY_COUNT
} pdb_property_e;

#undef PROPERTY_CREATE

struct pdb_property {
    char *name;
    u8_t *data;
    int (*validate)(u8_t *data, size_t size);
    int (*get)(pdb_property_e id, u8_t *property_value, size_t size);
    int (*set)(pdb_property_e id, u8_t *property_value, size_t size);
    u8_t size;
    u8_t in_flash;
    u8_t changed;
    u8_t observers;
    pdb_property_e id;
};
typedef struct pdb_property pdb_property_t;

size_t pdb_property_get_size(pdb_property_e id, int *error);

pdb_property_t *pdb_property_get_ref(pdb_property_e property);

int pdb_property_get(pdb_property_e id, u8_t *property_value, size_t size);

int pdb_property_get_private(pdb_property_e id, u8_t *property_value, size_t size);

int pdb_property_set(pdb_property_e id, u8_t *property_value, size_t size);

int pdb_property_set_private(pdb_property_e id, u8_t *property_value, size_t size);

void pdb_thread(void);

u8_t pdb_u8(pdb_property_e id, int *error);

u16_t pdb_u16(pdb_property_e id, int *error);

u32_t pdb_u32(pdb_property_e id, int *error);

u64_t pdb_u64(pdb_property_e id, int *error);


struct pdb_buffer {
    u8_t content[PDB_MAX_PROPERTY_SIZE];
    u8_t size;
};

typedef struct pdb_buffer pdb_buffer_t;

/**!
 * @brief Clear the buffer content.
 *
 * @param buffer a valid buffer reference.
 * @retval int return 0 if success.
 */
int pdb_buffer_clear(pdb_buffer_t *buffer);

/*!
 * @brief Push data to the content in a stack way.
 *
 * @param buffer reference to the buffer that will have the data extracted.
 * @param data the address where the data will be read from.
 * @param size the size of the data that will be copied.
 *
 * @retval 0 if ok
 * @retval -EINVAL if an error occurs.
 */
int pdb_buffer_push_data(pdb_buffer_t *buffer, u8_t *data, size_t size);

/*!
 * @brief Pop data from the payload stack (buffer->data field).
 *
 * @param buffer reference to the buffer that will have the data extracted.
 * @param data the address where the data will be placed.
 * @param size the size of the data that will be retrieved.
 *
 * @retval 0 if ok
 * @retval -EINVAL if an error occurs.
 */
int pdb_buffer_pop_data(pdb_buffer_t *buffer, u8_t *data, size_t size);

#endif
