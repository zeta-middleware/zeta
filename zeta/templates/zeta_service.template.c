#include <zephyr.h>
#include "zeta.h"
#include "zeta_callbacks.h"

K_SEM_DEFINE(${service_name}_event_sem, 0, 1);

/**
 * @brief This is the function used by Zeta to tell the ${service_name} that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing the
 * channel's id in it.
 *
 * @param id
 */
void ${service_name}_service_callback(zt_channel_e id)
{
    k_sem_give(&${service_name}_event_sem);
}

/**
 * @brief This is the task loop responsible to run the ${service_name} thread
 * functionality.
 */
void ${service_name}_task()
{
    // setup code
    while (1) {
        k_sem_take(&${service_name}_event_sem, K_FOREVER);
        // Thread loop code
    }
}

