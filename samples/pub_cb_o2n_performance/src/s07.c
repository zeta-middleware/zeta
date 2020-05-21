#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_SEM_DEFINE(S07_callback_sem, 0, 1);

extern u32_t total_cycles;
extern u32_t start_cycles;

/**
 * @brief This is the function used by Zeta to tell the S07 that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing the
 * channel's id in it.
 *
 * @param id
 */
void S07_service_callback(zt_channel_e id)
{
    total_cycles += (k_cycle_get_32() - start_cycles);
    k_sem_give(&S07_callback_sem);
}

/**
 * @brief This is the task loop responsible to run the S07 thread
 * functionality.
 */
void S07_task()
{
    LOG_DBG("S07 Service has started...[OK]");
    while (1) {
        k_sem_take(&S07_callback_sem, K_FOREVER);
    }
}

ZT_SERVICE_INIT(S07, S07_task, S07_service_callback);
