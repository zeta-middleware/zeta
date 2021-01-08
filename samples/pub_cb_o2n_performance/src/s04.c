#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_SEM_DEFINE(S04_callback_sem, 0, 1);

extern uint32_t total_cycles;
extern uint32_t start_cycles;

/**
 * @brief This is the function used by Zeta to tell the S04 that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing the
 * channel's id in it.
 *
 * @param id
 */
void S04_service_callback(zt_channel_e id)
{
    total_cycles += (k_cycle_get_32() - start_cycles);
    k_sem_give(&S04_callback_sem);
}

/**
 * @brief This is the task loop responsible to run the S04 thread
 * functionality.
 */
void S04_task()
{
    LOG_DBG("S04 Service has started...[OK]");
    while (1) {
        k_sem_take(&S04_callback_sem, K_FOREVER);
    }
}

ZT_SERVICE_DECLARE(S04, S04_task, S04_service_callback);
