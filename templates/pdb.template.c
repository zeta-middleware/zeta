/**
 * @file   pdb.template.c
 * @author Lucas Peixoto <lucaspeixotoac@gmail.com>
 * 
 * 
 */

/* #TODO: Padronizar os prints do sistema. */
#include <fs/nvs.h>
#include <string.h>
#include <zephyr.h>

#include "pdb.h"

#include "devicetree_fixups.h"
#include "pdb_threads.h"
#include "pdb_custom_functions.h"
#include "pdb_callbacks.h"

#define NVS_SECTOR_SIZE $nvs_sector_size
#define NVS_SECTOR_COUNT $nvs_sector_count
#define NVS_STORAGE_OFFSET $nvs_storage_offset

$channels_sems


void pdb_thread(void);
void pdb_thread_nvs(void);
static int pdb_channel_get_private(pdb_channel_e id, u8_t *channel_value, size_t size);
static int pdb_channel_set_private(pdb_channel_e id, u8_t *channel_value, size_t size);

K_THREAD_DEFINE(pdb_thread_id, PDB_THREAD_NVS_STACK_SIZE, pdb_thread, NULL, NULL, NULL,
                    PDB_THREAD_PRIORITY, 0, K_NO_WAIT);

K_THREAD_DEFINE(pdb_thread_nvs_id, PDB_THREAD_NVS_STACK_SIZE, pdb_thread_nvs, NULL, NULL, NULL,
                    PDB_THREAD_PRIORITY, 0, K_NO_WAIT);
K_MSGQ_DEFINE(pdb_channels_changed_msgq, sizeof(u8_t), 30, 4);

$arrays_init

static struct nvs_fs pdb_fs = {
    .sector_size  = NVS_SECTOR_SIZE,
    .sector_count = NVS_SECTOR_COUNT,
    .offset       = NVS_STORAGE_OFFSET,
};

$channels_creation

const char *pdb_channel_name(pdb_channel_e id, int *error)
{
    if (id < PDB_CHANNEL_COUNT) {
        pdb_channel_t *p = &__pdb_channels[id];
        return p->name;
    }
    else {
        if (error) {
            *error = -EINVAL;
        }
        return NULL;
    }
}

size_t pdb_channel_size(pdb_channel_e id, int *error)
{
    if (id < PDB_CHANNEL_COUNT) {
        pdb_channel_t *p = &__pdb_channels[id];
        return (size_t) p->size;
    }
    else {
        printk("The channel #%d was not found!\n", id);
        if (error) {
            *error = -EINVAL;
        }
        return 0;
    }
}

/* #TODO: Deixar de utilizar o channel_get_ref */
int pdb_channel_get(pdb_channel_e id, u8_t *channel_value, size_t size)
{
    if (id < PDB_CHANNEL_COUNT) {
        int error              = 0;
        pdb_channel_t *channel = &__pdb_channels[id];
        PDB_CHECK_VAL(channel->get, NULL, -EPERM, "channel #%d does not have get implementation!\n", id);
        if (channel->pre_get) {
            error = channel->pre_get(id, channel_value, size);
        }
        PDB_CHECK(error, error, "Error in pre-get function of channel #%d\n", id);
        error = channel->get(id, channel_value, size);
        PDB_CHECK(error, error, "Current channel #%d, error code: %d\n", id, error)
            return error;
    }
    else {
        printk("The channel #%d was not found!\n", id); 
        return -ENODATA; 
    }
}

static int pdb_channel_get_private(pdb_channel_e id, u8_t *channel_value, size_t size)
{
    int ret = 0;
    pdb_channel_t *channel = &__pdb_channels[id];
    if (channel->size == size) {
        if (k_sem_take(channel->sem, K_MSEC(200))) {
            printk("Could not get the channel. Channel is busy\n");
            ret = -EBUSY;
        } else {
            memcpy(channel_value, channel->data, channel->size);
            k_sem_give(channel->sem);
        }
    } else {
        ret = -EINVAL;
    }
    return ret;
}

int pdb_channel_set(pdb_channel_e id, u8_t *channel_value, size_t size)
{
    if (id < PDB_CHANNEL_COUNT) {
        int error              = 0;
        int valid              = 1;
        pdb_channel_t *channel = &__pdb_channels[id];
        const k_tid_t *pub_id;

        for(pub_id = channel->publishers_id ; *pub_id != NULL ; ++pub_id) {
            if (*pub_id == k_current_get()) {
                break;
            }
        }
        PDB_CHECK_VAL(*pub_id, NULL,-EPERM, "The current thread has not the permission to change channel #%d!\n", id);
        PDB_CHECK_VAL(channel->set, NULL, -EPERM, "The channel #%d is read only!\n", id);
        if (channel->validate) {
            valid = channel->validate(channel_value, size);
        }
        PDB_CHECK(!valid, -EINVAL, "The value doesn't satisfy valid function of channel #%d!\n", id);
        if (channel->pre_set) {
            error = channel->pre_set(id, channel_value, size);
        }
        PDB_CHECK(error, error, "Error on pre_set function of channel #%d!\n", id);
        error = channel->set(id, channel_value, size);
        PDB_CHECK(error, error, "Current channel #%d, error code: %d!\n", id, error);
        if (channel->pos_set) {
            error = channel->pos_set(id, channel_value, size);
        }
        PDB_CHECK(error, error, "Error on pos_set function of channel #%d!\n", id);
        return error;
    }
    else {
        printk("The channel #%d was not found!\n", id); 
        return -ENODATA;
    }
}

static int pdb_channel_set_private(pdb_channel_e id, u8_t *channel_value, size_t size)
{
    int ret = 0;
    pdb_channel_t *channel = &__pdb_channels[id];
    if (channel->size == size) {
        if (k_sem_take(channel->sem, K_MSEC(200))) {
            printk("Could not set the channel. Channel is busy\n");
            ret = -EBUSY;
        } else {
            if (memcmp(channel->data, channel_value, size)) {
                memcpy(channel->data, channel_value, channel->size);
                channel->opt.field.pend_callback = 1;
                if (k_msgq_put(&pdb_channels_changed_msgq, (u8_t *) &id, K_MSEC(500))) {
                    printk("[Channel #%d] Error sending channels change message to PDB thread!\n", id);
                }
                channel->opt.field.pend_persistent = (channel->persistent) ? 1:0;
                k_sem_give(channel->sem);
            } else {
                k_sem_give(channel->sem);
            }
        }
    } else {
        ret = -EINVAL;
    }
    return ret;
}

static void __pdb_recover_data_from_flash(void)
{
    int rc = 0;
    printk("[ ] Recovering data from flash\n");
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
                printk("Could not recover the channel. Channel is busy\n");
            }
        }
    }
    printk("[X] Recovering data from flash\n");
}

static void __pdb_persist_data_on_flash(void)
{
    int bytes_written = 0;
    for (u16_t id = 0; id < PDB_CHANNEL_COUNT; ++id) {
        if (__pdb_channels[id].persistent && __pdb_channels[id].opt.field.pend_persistent) {
            // printk("Store changes for channel #%d", id);
            bytes_written =
                nvs_write(&pdb_fs, id, __pdb_channels[id].data, __pdb_channels[id].size);
            if (bytes_written > 0) { /* item was found and updated*/
                __pdb_channels[id].opt.field.pend_persistent = 0;
                printk("channel #%d value updated on the flash\n", id);
            } else if (bytes_written == 0) {
                /* printk("channel #%d value is already on the flash.", id); */
            } else { /* item was not found, add it */
                printk("channel #%d could not be stored\n", id);
            }
        } 
    }
}

void pdb_thread(void)
{
    /* #TODO: Alterar o funcionamento da thread do pdb */
    $set_publishers


/* #TODO: alterar o k_sleep por um semáforo */
    u8_t id = 0;
    while (1) {
        k_msgq_get(&pdb_channels_changed_msgq, &id, K_FOREVER);
        if (id < PDB_CHANNEL_COUNT) {
            if (__pdb_channels[id].opt.field.pend_callback) {
                for(pdb_callback_f *f = __pdb_channels[id].subscribers_cbs ; *f != NULL ; ++f) {
                    (*f)(id);
                }
                __pdb_channels[id].opt.field.pend_callback = 0;                
            }
            else {
                printk("[PDB-THREAD]: Received pend_callback from a channel(#%d) without changes!\n", id);
            }
        }
        else {
            printk("[PDB-THREAD]: Received an invalid ID channel #%d\n", id);
        }
    }
}

void pdb_thread_nvs(void) {
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
}
