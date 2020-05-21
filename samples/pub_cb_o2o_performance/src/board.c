#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_SEM_DEFINE(BOARD_callback_sem, 0, 1);


/**
 * @brief This is the function used by Zeta to tell the BOARD that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing the
 * channel's id in it.
 *
 * @param id
 */
void BOARD_service_callback(zt_channel_e id)
{
    u32_t cyc = k_cycle_get_32();
    LOG_WRN("BOARD callback cycles: %u", cyc);
    k_sem_give(&BOARD_callback_sem);
}

/**
 * @brief This is the task loop responsible to run the BOARD thread
 * functionality.
 */
void BOARD_task()
{
    LOG_DBG("BOARD Service has started...[OK]");
    while (1) {
        k_sem_take(&BOARD_callback_sem, K_FOREVER);
    }
}

ZT_SERVICE_INIT(BOARD, BOARD_task, BOARD_service_callback);
