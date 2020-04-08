/*!
 * @file
 * @brief This is the abstraction information relative to NB hardware
 *
 */

#ifndef PDB_H_
#define PDB_H_

#include <stddef.h>
#include <zephyr.h>
#include <zephyr/types.h>

#define PDB_THREAD_SIZE 1024
#define PDB_THREAD_PRIORITY -2


#define PDB_VALUE_REF(x) (u8_t *) (&x), sizeof(x)
#define PDB_CHECK_VAL(_p, _e, _err, ...) \
    if (_p != _e) {                       \
        printk(__VA_ARGS__);              \
        return _err;                      \
    }

#define PDB_CHECK(_p, _err, ...) \
    if (_p) {                     \
        printk(__VA_ARGS__);      \
        return _err;              \
    }


typedef enum {
    PDB_FIRMWARE_VERSION_CHANNEL,
    PDB_PERSISTENT_VAL_CHANNEL,
    PDB_ECHO_HAL_CHANNEL,
    PDB_SET_GET_CHANNEL,
    PDB_CHANNEL_COUNT
} __attribute__((packed)) pdb_channel_e;

typedef struct {
    k_tid_t source_thread;
    pdb_channel_e id;
} pdb_event_t;

typedef void (*pdb_callback_f)(pdb_channel_e id);

struct pdb_channel {
    /* #TODO: Adicionar owners da property */
    const char *name;
    u8_t *data;
    int (*validate)(u8_t *data, size_t size);
    int (*pre_get)(pdb_channel_e id);
    int (*get)(pdb_channel_e id, u8_t *channel_value, size_t size);
    int (*pre_set)(pdb_channel_e id);
    int (*set)(pdb_channel_e id, u8_t *channel_value, size_t size);
    int (*pos_set)(pdb_channel_e id);
    u8_t size;
    u8_t persistent;
    u8_t changed;
    struct k_sem *sem;
    k_tid_t *publishers_id;
    pdb_callback_f *subscribers_cbs;
    pdb_channel_e id;
};
typedef struct pdb_channel pdb_channel_t;

/**
 * Returns the channel size.
 *
 * @param id channel ID.
 * @param error variable to handle possible errors.
 *
 * @return channel size.
 */
size_t pdb_channel_size(pdb_channel_e id, int *error);

/* TODO: Add doxygen comments about pdb_channel_name */
const char *pdb_channel_name(pdb_channel_e id);

/**
 * Gets the channel value.
 *
 * @param id channel ID.
 * @param channel_value handle the channel value.
 * @param size channel value size.
 *
 * @return error code.
 */
int pdb_channel_get(pdb_channel_e id, u8_t *channel_value, size_t size);

/**
 * Gets the channel value private.
 *
 * @param id channel ID.
 * @param channel_value handle the channel value.
 * @param size channel value size.
 *
 * @return error code.
 */
int pdb_channel_get_private(pdb_channel_e id, u8_t *channel_value, size_t size);

/**
 * Sets the channel value.
 *
 * @param id channel ID.
 * @param channel_value channel value that must to be setted.
 * @param size channel value size.
 *
 * @return error code.
 */
int pdb_channel_set(pdb_channel_e id, u8_t *channel_value, size_t size);


/**
 * Sets the channel value private.
 *
 * @param id channel ID.
 * @param channel_value channel value that must to be setted.
 * @param size channel value size.
 *
 * @return error code.
 */
int pdb_channel_set_private(pdb_channel_e id, u8_t *channel_value, size_t size);


#endif
