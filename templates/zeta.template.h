/*!
 * @file zeta.template.h
 * @brief This is the abstraction information relative to NB hardware
 * DON'T EDIT THIS FILE
 */

#ifndef ZETA_H_
#define ZETA_H_

#include <stddef.h>
#include <zephyr.h>
#include <zephyr/types.h>

#define ZETA_THREAD_NVS_STACK_SIZE $storage_stack_size
#define ZETA_THREAD_STACK_SIZE $zeta_stack_size
#define ZETA_THREAD_PRIORITY 0

#define ZETA_VALUE_REF(x) (u8_t *) (&x), sizeof(x)

#define ZETA_CHECK_VAL(_p, _e, _err, ...) \
    if (_p == _e) {                      \
        printk(__VA_ARGS__);             \
        return _err;                     \
    }

#define ZETA_CHECK(_p, _err, ...) \
    if (_p) {                    \
        printk(__VA_ARGS__);     \
        return _err;             \
    }

$channels_enum

    typedef struct {
    k_tid_t source_thread;
    zeta_channel_e id;
} zeta_event_t;

typedef void (*zeta_callback_f)(zeta_channel_e id);

union opt_data {
    struct {
        u8_t pend_persistent : 1;
        u8_t pend_callback : 1;
    } field;
    u8_t data;
};

struct zeta_channel {
    const char *name;
    u8_t *data;
    int (*validate)(u8_t *data, size_t size);
    int (*pre_get)(zeta_channel_e id, u8_t *channel_value, size_t size);
    int (*get)(zeta_channel_e id, u8_t *channel_value, size_t size);
    int (*pos_get)(zeta_channel_e id, u8_t *channel_value, size_t size);
    int (*pre_set)(zeta_channel_e id, u8_t *channel_value, size_t size);
    int (*set)(zeta_channel_e id, u8_t *channel_value, size_t size);
    int (*pos_set)(zeta_channel_e id, u8_t *channel_value, size_t size);
    u8_t size;
    u8_t persistent;
    union opt_data opt;
    struct k_sem *sem;
    const k_tid_t *publishers_id;
    zeta_callback_f *subscribers_cbs;
    zeta_channel_e id;
};
typedef struct zeta_channel zeta_channel_t;

/**
 * Returns the channel size.
 *
 * @param id channel ID.
 * @param error variable to handle possible errors.
 *
 * @return channel size.
 */
size_t zeta_channel_size(zeta_channel_e id, int *error);

/**
 * Returns the channel name
 *
 * @param id id channel id
 *
 * @return channel name
 */
const char *zeta_channel_name(zeta_channel_e id, int *error);

/**
 * Gets the channel value.
 *
 * @param id channel ID.
 * @param channel_value handle the channel value.
 * @param size channel value size.
 *
 * @return error code.
 */
int zeta_channel_get(zeta_channel_e id, u8_t *channel_value, size_t size);

/**
 * Gets the channel value private.
 *
 * @param id channel ID.
 * @param channel_value handle the channel value.
 * @param size channel value size.
 *
 * @return error code.
 */
/* int zeta_channel_get_private(zeta_channel_e id, u8_t *channel_value, size_t size); */

/**
 * Sets the channel value.
 *
 * @param id channel ID.
 * @param channel_value channel value that must to be setted.
 * @param size channel value size.
 *
 * @return error code.
 */
int zeta_channel_set(zeta_channel_e id, u8_t *channel_value, size_t size);


/**
 * Sets the channel value private.
 *
 * @param id channel ID.
 * @param channel_value channel value that must to be setted.
 * @param size channel value size.
 *
 * @return error code.
 */
/* int zeta_channel_set_private(zeta_channel_e id, u8_t *channel_value, size_t size); */


#endif
