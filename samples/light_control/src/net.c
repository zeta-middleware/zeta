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

/**
 * @brief This is the function used by Zeta to tell the NET that one(s) of the channels
 * which it is subscribed has changed. This callback will be called passing the channel's
 * id in it.
 *
 * @param id
 */
void NET_service_callback(zt_channel_e id)
{
    switch (id) {
    case ZT_LOAD_CHANNEL: {
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
    zt_data_t *manual_load_control = ZT_DATA_BYTES(2, 0x00, 0x01);
    printk("Hello NET\n");
    while (1) {
        manual_load_control->bytes.value[0] = 1;
        printk("on\n");
        zt_chan_pub(ZT_MANUAL_LOAD_CONTROL_CHANNEL, manual_load_control);
        k_sleep(K_SECONDS(5));
        printk("off\n");
        manual_load_control->bytes.value[0] = 0;
        zt_chan_pub(ZT_MANUAL_LOAD_CONTROL_CHANNEL, manual_load_control);
        k_sleep(K_SECONDS(10));
    }
}

ZT_SERVICE_INIT(NET, NET_task, NET_service_callback);
