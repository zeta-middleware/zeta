#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_SEM_DEFINE(NET_callback_sem, 0, 1);


/**
 * @brief This is the function used by Zeta to tell the NET that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing the
 * channel's id in it.
 *
 * @param id
 */
void NET_service_callback(zt_channel_e id)
{
    k_sem_give(&NET_callback_sem);
}

/**
 * @brief This is the task loop responsible to run the NET thread
 * functionality.
 */
void NET_task()
{
    LOG_DBG("NET Service has started...[OK]");
    while (1) {
        k_sem_take(&NET_callback_sem, K_FOREVER);
    }
}

ZT_SERVICE_INIT(NET, NET_task, NET_service_callback);
