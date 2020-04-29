/**
 * @file net.c
 * @brief The NET service is used to send commands to CORE and make a fake schedule of
 * sending data to the cloud.
 * @author Rodrigo Peixoto
 * @version 0.1
 * @date 2020-04-28
 */
#include <zephyr.h>
#include "zeta.h"

#define ZT_REF(x) (u8_t *) &x, sizeof(x)

/**
 * @brief This is the function used by Zeta to tell the NET that one(s) of the channels
 * which it is subscribed has changed. This callback will be called passing the channel's
 * id in it.
 *
 * @param id
 */
void NET_service_callback(zeta_channel_e id)
{
    switch (id) {
    case ZETA_LOAD_CHANNEL: {
        printk("[NET]: Schedule to send status to the cloud\n");
    } break;
    default:
        printk("[NET]: Undesired event %d\n", id);
    }
}

/**
 * @brief This is the task loop responsible to run the NET thread functionality.
 */
void NET_task()
{
    u8_t manual_load_control[2] = {0x00, 0x01};
    while (1) {
        manual_load_control[0] = 1;
        zeta_channel_set(ZETA_MANUAL_LOAD_CONTROL_CHANNEL, ZT_REF(manual_load_control));
        k_sleep(K_SECONDS(5));
        manual_load_control[0] = 0;
        zeta_channel_set(ZETA_MANUAL_LOAD_CONTROL_CHANNEL, ZT_REF(manual_load_control));
        k_sleep(K_SECONDS(10));
    }
}