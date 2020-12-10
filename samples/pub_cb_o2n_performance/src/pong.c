#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>
#include "sys/printk.h"

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_SEM_DEFINE(PONG_callback_sem, 0, 1);

extern u32_t total_cycles;
extern u32_t start_cycles;

/**
 * @brief This is the function used by Zeta to tell the PONG that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing the
 * channel's id in it.
 *
 * @param id
 */
void PONG_service_callback(zt_channel_e id)
{
    total_cycles += (k_cycle_get_32() - start_cycles);
    k_sem_give(&PONG_callback_sem);
}

/**
 * @brief This is the task loop responsible to run the PONG thread
 * functionality.
 */
void PONG_task()
{
    LOG_DBG("PONG Service has started...[OK]");
    while (1) {
        k_sem_take(&PONG_callback_sem, K_FOREVER);
        zt_chan_pub(ZT_PONG_CHANNEL, ZT_DATA_U32(0x0F0F0F0F));
    }
}

ZT_SERVICE_DECLARE(PONG, PONG_task, PONG_service_callback);
