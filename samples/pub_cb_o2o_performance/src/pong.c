#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>
#include "sys/printk.h"

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_SEM_DEFINE(PONG_callback_sem, 0, 1);

extern u32_t end_cycles;
static zt_channel_e current_ping = 0;

/**
 * @brief This is the function used by Zeta to tell the PONG that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing the
 * channel's id in it.
 *
 * @param id
 */
void PONG_service_callback(zt_channel_e id)
{
    current_ping = id;
    end_cycles   = k_cycle_get_32();
    k_sem_give(&PONG_callback_sem);
}

/**
 * @brief This is the task loop responsible to run the PONG thread
 * functionality.
 */
void PONG_task()
{
    LOG_DBG("PONG Service has started...[OK]");
    zt_data_t *pong_data[9] = {
        ZT_DATA_U8(0),        ZT_DATA_U16(0),        ZT_DATA_U32(0),
        ZT_DATA_U64(0),       ZT_DATA_BYTES(16, 0),  ZT_DATA_BYTES(32, 0),
        ZT_DATA_BYTES(64, 0), ZT_DATA_BYTES(128, 0), ZT_DATA_BYTES(255, 0),
    };
    int rc = 0;
    while (1) {
        k_sem_take(&PONG_callback_sem, K_FOREVER);

        rc = zt_chan_read(current_ping, pong_data[(current_ping - 1) >> 1]);
        if (rc) {
            printk("1Error %d; current_ping %d; index %d, size %d. pong_data->size %d\n",
                   rc, current_ping, (current_ping - 1) >> 1,
                   zt_channel_size(current_ping + 1, NULL),
                   pong_data[(current_ping - 1) >> 1]->bytes.size);
        }
        rc = zt_chan_pub(current_ping + 1, pong_data[(current_ping - 1) >> 1]);
        if (rc) {
            printk("2Error %d; current_ping %d; index %d, size %d\n", rc, current_ping,
                   (current_ping - 1) >> 1, zt_channel_size(current_ping + 1, NULL));
        }
    }
}

ZT_SERVICE_INIT(PONG, PONG_task, PONG_service_callback);
