#include <fs/nvs.h>
#include <string.h>
#include <zephyr.h>

#include "pdb.h"

#include "devicetree_fixups.h"
#include "pdb_threads.h"
#include "pdb_custom_functions.h"
#include "pdb_callbacks.h"

int pdb_thread(void);

#define NVS_SECTOR_SIZE DT_FLASH_ERASE_BLOCK_SIZE
#define NVS_SECTOR_COUNT 4
#define NVS_STORAGE_OFFSET DT_FLASH_AREA_STORAGE_OFFSET


/* BEGIN INITIALIZING CHANNEL SEMAPHORES */

K_SEM_DEFINE(pdb_FIRMWARE_VERSION_channel_sem, 1, 1);

K_SEM_DEFINE(pdb_PERSISTENT_VAL_channel_sem, 1, 1);

K_SEM_DEFINE(pdb_ECHO_HAL_channel_sem, 1, 1);

K_SEM_DEFINE(pdb_SET_GET_channel_sem, 1, 1);

/* END INITIALIZING CHANNEL SEMAPHORES */


K_THREAD_DEFINE(pdb_thread_id, PDB_THREAD_SIZE, pdb_thread, NULL, NULL, NULL,
                    PDB_THREAD_PRIORITY, 0, K_NO_WAIT);



/* BEGIN PDB_FIRMWARE_VERSION_CHANNEL INIT ARRAYS */
u8_t FIRMWARE_VERSION_data[] = {0xF1, 0xF2, 0xF3, 0xF4};

/* END PDB_FIRMWARE_VERSION_CHANNEL INIT ARRAYS */

/* BEGIN PDB_PERSISTENT_VAL_CHANNEL INIT ARRAYS */
u8_t PERSISTENT_VAL_data[] = {0xFF};

/* END PDB_PERSISTENT_VAL_CHANNEL INIT ARRAYS */

/* BEGIN PDB_ECHO_HAL_CHANNEL INIT ARRAYS */
u8_t ECHO_HAL_data[] = {0xFF};
pdb_callback_f ECHO_HAL_subscribers[] = { CORE_service_callback, HAL_service_callback, NULL };
/* END PDB_ECHO_HAL_CHANNEL INIT ARRAYS */

/* BEGIN PDB_SET_GET_CHANNEL INIT ARRAYS */
u8_t SET_GET_data[] = {0xFF};

/* END PDB_SET_GET_CHANNEL INIT ARRAYS */


static struct nvs_fs pdb_fs = {
    .sector_size  = NVS_SECTOR_SIZE,
    .sector_count = NVS_SECTOR_COUNT,
    .offset       = NVS_STORAGE_OFFSET,
};


static pdb_channel_t __pdb_channels[PDB_CHANNEL_COUNT] = {
    
    {
        .name = "PDB_FIRMWARE_VERSION_CHANNEL",       
        .validate = NULL,
        .pre_get = NULL,
        .get = pdb_channel_get_private,
        .pre_set = NULL,
        .set = pdb_channel_set_private,
        .pos_set = NULL,
        .size = 4,
        .persistent = 0,
        .changed = 0,
        .sem = &pdb_FIRMWARE_VERSION_channel_sem,
        .subscribers_cbs = NULL,
        .id = PDB_FIRMWARE_VERSION_CHANNEL,
        .data = FIRMWARE_VERSION_data
    },

    {
        .name = "PDB_PERSISTENT_VAL_CHANNEL",       
        .validate = pdb_validator_different_of_zero,
        .pre_get = NULL,
        .get = pdb_channel_get_private,
        .pre_set = NULL,
        .set = pdb_channel_set_private,
        .pos_set = NULL,
        .size = 1,
        .persistent = 1,
        .changed = 0,
        .sem = &pdb_PERSISTENT_VAL_channel_sem,
        .subscribers_cbs = NULL,
        .id = PDB_PERSISTENT_VAL_CHANNEL,
        .data = PERSISTENT_VAL_data
    },

    {
        .name = "PDB_ECHO_HAL_CHANNEL",       
        .validate = NULL,
        .pre_get = NULL,
        .get = pdb_channel_get_private,
        .pre_set = NULL,
        .set = pdb_channel_set_private,
        .pos_set = NULL,
        .size = 1,
        .persistent = 0,
        .changed = 0,
        .sem = &pdb_ECHO_HAL_channel_sem,
        .subscribers_cbs = ECHO_HAL_subscribers,
        .id = PDB_ECHO_HAL_CHANNEL,
        .data = ECHO_HAL_data
    },

    {
        .name = "PDB_SET_GET_CHANNEL",       
        .validate = NULL,
        .pre_get = get_plus_1,
        .get = pdb_channel_get_private,
        .pre_set = NULL,
        .set = pdb_channel_set_private,
        .pos_set = NULL,
        .size = 1,
        .persistent = 0,
        .changed = 0,
        .sem = &pdb_SET_GET_channel_sem,
        .subscribers_cbs = NULL,
        .id = PDB_SET_GET_CHANNEL,
        .data = SET_GET_data
    },

};                


static pdb_channel_t *pdb_channel_get_ref(pdb_channel_e id)
{
    if (id < PDB_CHANNEL_COUNT) {
        return &__pdb_channels[id];
    } else {
        return NULL;
    }
}

size_t pdb_channel_size(pdb_channel_e id, int *error)
{
    size_t size      = 0;
    pdb_channel_t *p = pdb_channel_get_ref(id);
    if (p) {
        size = (size_t) p->size;
    } else {
        if (error) {
            *error = -EINVAL;
        }
    }
    return size;
}

int pdb_channel_get(pdb_channel_e id, u8_t *channel_value, size_t size)
{
    int error              = 0;
    pdb_channel_t *channel = pdb_channel_get_ref(id);
    PDB_CHECK(channel, -ENODEV, "The channel %d was not found!\n", id);
    PDB_CHECK(channel->get, -EPERM, "The channel %d does not have get implementation!\n", id);
    PDB_CHECK(channel->pre_get(id), -EIO, "Error in pre-get function of channel %d\n", id);
    error = channel->get(id, channel_value, size);
    if (error) {
        printk("Current channel get: %d, error code: %d\n", id, error);
    }
    return error;
}

int pdb_channel_get_private(pdb_channel_e id, u8_t *channel_value, size_t size)
{
    int ret = 0;
    if (id < PDB_CHANNEL_COUNT) {
        pdb_channel_t *current_channel = &__pdb_channels[id];
        if (current_channel->size == size) {
            if (k_sem_take(current_channel->sem, K_MSEC(200))) {
                printk("Could not get the channel. Channel is busy\n");
                ret = -EBUSY;
            } else {
                memcpy(channel_value, current_channel->data, current_channel->size);
                k_sem_give(current_channel->sem);
            }
        } else {
            ret = -EINVAL;
        }
    } else {
        ret = -ENODATA;
    }
    return ret;
}

int pdb_channel_set(pdb_channel_e id, u8_t *channel_value, size_t size)
{
    int error              = 0;
    int valid              = 1;
    pdb_channel_t *channel = pdb_channel_get_ref(id);
    const k_tid_t *p_id;

    for(p_id = channel->publishers_id ; *p_id != NULL ; ++p_id) {
        if (*p_id == k_current_get()) {
            break;
        }
    }

    PDB_CHECK(p_id, -EPERM, "The current thread has not the permission to change channel %d!\n", id);
    PDB_CHECK_VAL(channel, NULL, -ENODEV, "The channel %d was not found!\n", id);
    PDB_CHECK_VAL(channel->set, NULL, -EPERM, "The channel %d is read only!\n", id);
    if (channel->validate) {
        valid = channel->validate(channel_value, size);
    }
    PDB_CHECK(valid, -EINVAL, "The value doesn't satisfy valid function of channel %d!\n", id);
    PDB_CHECK(channel->pre_set(id), -EINVAL, "Error on pre_set function of channel %d!\n", id);
    error = channel->set(id, channel_value, size);
    if (error) {
        printk("Current channel set: %d, error code: %d!\n", id, error);
    }
    PDB_CHECK(channel->pos_set(id), -EINVAL, "Error on pre_set function of channel %d!\n", id);
    return error;
}

int pdb_channel_set_private(pdb_channel_e id, u8_t *channel_value, size_t size)
{
    int ret = 0;
    if (id < PDB_CHANNEL_COUNT) {
        pdb_channel_t *current_channel = &__pdb_channels[id];
        if (current_channel->size == size) {
            if (k_sem_take(current_channel->sem, K_MSEC(200))) {
                printk("Could not set the channel. Channel is busy\n");
                ret = -EBUSY;
            } else {
                if (memcmp(current_channel->data, channel_value, size)) {
                    memcpy(current_channel->data, channel_value, current_channel->size);
                    if (current_channel->changed < 255) {
                        current_channel->changed++;
                    }
                    k_sem_give(current_channel->sem);
                } else {
                    k_sem_give(current_channel->sem);
                }
            }
        } else {
            ret = -EINVAL;
        }
    } else {
        ret = -ENODATA;
    }
    return ret;
}

static void __pdb_recover_data_from_flash(void)
{
    int rc = 0;
    printk("Start...\n");
    for (u16_t id = 0; id < PDB_CHANNEL_COUNT; ++id) {
        if (__pdb_channels[id].persistent) {
            if (!k_sem_take(__pdb_channels[id].sem, K_SECONDS(5))) {
                rc = nvs_read(&pdb_fs, id, __pdb_channels[id].data, __pdb_channels[id].size);
                if (rc > 0) { /* item was found, show it */
                    printk("Id: %d, value:", id);
                    for (size_t i = 0; i < __pdb_channels[id].size; i++) {
                        printk(" %02X", __pdb_channels[id].data[i]);
                    }
                    printk("|");
                    for (size_t i = 0; i < __pdb_channels[id].size; i++) {
                        if (32 <= __pdb_channels[id].data[i]
                            && __pdb_channels[id].data[i] <= 126) {
                            printk("%c", __pdb_channels[id].data[i]);
                        } else {
                            printk(".");
                        }
                    }
                    printk("\n");
                } else { /* item was not found, add it */
                    printk("No values found for channel #%d\n", id);
                }
                k_sem_give(__pdb_channels[id].sem);
            }
            else {
                printk("Could not recover the channel. Channel is busy\n");                 }
        }
    }
}

static void __pdb_persist_data_on_flash(void)
{
    int bytes_written = 0;
    for (u16_t id = 0; id < PDB_CHANNEL_COUNT; ++id) {
        if (__pdb_channels[id].persistent) {
            if (__pdb_channels[id].changed) {
                // printk("Store changes for channel: %d", id);
                bytes_written =
                    nvs_write(&pdb_fs, id, __pdb_channels[id].data, __pdb_channels[id].size);
                if (bytes_written > 0) { /* item was found and updated*/
                    __pdb_channels[id].changed = 0;
                    printk("Channel #%d value updated on the flash\n", id);
                } else if (bytes_written == 0) {
                    // printk("Channel #%d value is already on the flash.", id);
                } else { /* item was not found, add it */
                    printk("Channel #%d could not be stored\n", id);
                }
            }
        } else {
            __pdb_channels[id].changed = 0;
        }
    }
}

int pdb_thread(void)
{
    /* #TODO: Alterar o funcionamento da thread do pdb */
    
/* BEGIN SET CHANNEL PUBLISHERS */

    const k_tid_t FIRMWARE_VERSION_publishers[] = {NULL};
    __pdb_channels[PDB_FIRMWARE_VERSION_CHANNEL].publishers_id = FIRMWARE_VERSION_publishers;

    const k_tid_t PERSISTENT_VAL_publishers[] = { CORE_thread_id, HAL_thread_id, NULL };;
    __pdb_channels[PDB_PERSISTENT_VAL_CHANNEL].publishers_id = PERSISTENT_VAL_publishers;

    const k_tid_t ECHO_HAL_publishers[] = { HAL_thread_id, APP_thread_id, CORE_thread_id, NULL };;
    __pdb_channels[PDB_ECHO_HAL_CHANNEL].publishers_id = ECHO_HAL_publishers;

    const k_tid_t SET_GET_publishers[] = { CORE_thread_id, APP_thread_id, NULL };;
    __pdb_channels[PDB_SET_GET_CHANNEL].publishers_id = SET_GET_publishers;

/* END SET CHANNEL PUBLISHERS */

    int error = nvs_init(&pdb_fs, DT_FLASH_DEV_NAME);
    if (error) {
        printk("Flash Init failed\n");
    } else {
        printk("NVS started...[OK]\n");
    }
    __pdb_recover_data_from_flash();

    while (1) {
        k_sleep(K_SECONDS(10));
        __pdb_persist_data_on_flash();
    }
    return 0;
}

const char *pdb_channel_name(pdb_channel_e id)
{
    pdb_channel_t *p = pdb_channel_get_ref(id);

    if (p) {
        return p->name;
    }

    return (const char *) p;
}
