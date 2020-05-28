#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_SEM_DEFINE(S10_callback_sem, 0, 1);

extern u32_t total_cycles;
extern u32_t start_cycles;

/**
 * @brief This is the function used by Zeta to tell the S10 that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing the
 * channel's id in it.
 *
 * @param id
 */
void S10_service_callback(zt_channel_e id)
{
    total_cycles += (k_cycle_get_32() - start_cycles);
    k_sem_give(&S10_callback_sem);
}

/**
 * @brief This is the task loop responsible to run the S10 thread
 * functionality.
 */
void S10_task()
{
    LOG_DBG("S10 Service has started...[OK]");
    while (1) {
        k_sem_take(&S10_callback_sem, K_FOREVER);
    }
}

ZT_SERVICE_INIT(S10, S10_task, S10_service_callback);
