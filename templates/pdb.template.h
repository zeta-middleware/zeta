/*!
 * @file pdb.template.h
 * @brief This is the abstraction information relative to NB hardware
 * DON'T EDIT THIS FILE
 */

#ifndef PDB_H_
#define PDB_H_

#include <stddef.h>
#include <zephyr.h>
#include <zephyr/types.h>

#define PDB_THREAD_NVS_STACK_SIZE $storage_stack_size
#define PDB_THREAD_STACK_SIZE $pdb_stack_size
#define PDB_THREAD_PRIORITY 0

#define PDB_VALUE_REF(x) (u8_t *) (&x), sizeof(x)

#define PDB_CHECK_VAL(_p, _e, _err, ...) \
    if (_p == _e) {                       \
        printk(__VA_ARGS__);              \
        return _err;                      \
    }

#define PDB_CHECK(_p, _err, ...) \
    if (_p) {                     \
        printk(__VA_ARGS__);      \
        return _err;              \
    }

$channels_enum

typedef struct {
    k_tid_t source_thread;
    pdb_channel_e id;
} pdb_event_t;

typedef void (*pdb_callback_f)(pdb_channel_e id);

union opt_data {
    struct {
        u8_t pend_persistent : 1;
        u8_t pend_callback : 1;
    } field;
    u8_t data;
};

struct pdb_channel {
    const char *name;
    u8_t *data;
    int (*validate)(u8_t *data, size_t size);
    int (*pre_get)(pdb_channel_e id, u8_t *channel_value, size_t size);
    int (*get)(pdb_channel_e id, u8_t *channel_value, size_t size);
    int (*pre_set)(pdb_channel_e id, u8_t *channel_value, size_t size);
    int (*set)(pdb_channel_e id, u8_t *channel_value, size_t size);
    int (*pos_set)(pdb_channel_e id, u8_t *channel_value, size_t size);
    u8_t size;
    u8_t persistent;
    union opt_data opt;
    struct k_sem *sem;
    const k_tid_t *publishers_id;
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

/** 
 * Returns the channel name
 * 
 * @param id id channel id
 * 
 * @return channel name
 */
const char *pdb_channel_name(pdb_channel_e id, int *error);

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
/* int pdb_channel_get_private(pdb_channel_e id, u8_t *channel_value, size_t size); */

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
/* int pdb_channel_set_private(pdb_channel_e id, u8_t *channel_value, size_t size); */


#endif
