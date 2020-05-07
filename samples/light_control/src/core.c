/**
 * @file core.c
 * @brief The CORE service is used to control the load status based on the light level
 * channel value.
 * @author Rodrigo Peixoto
 * @version 0.1
 * @date 2020-04-28
 */

#include <zephyr.h>
#include "zeta.h"

#define ZT_REF(x) (u8_t *) &x, sizeof(x)

K_SEM_DEFINE(core_event_sem, 0, 1);


/**
 * @brief This is the function used by Zeta to tell the CORE that one(s) of the channels
 * which it is subscribed has changed. This callback will be called passing the channel's
 * id in it.
 *
 * @param id
 */
void CORE_service_callback(zt_channel_e id)
{
    k_sem_give(&core_event_sem);
}

struct version {
    u16_t build;
    u8_t minor;
    u8_t major;
};


/**
 * @brief This is the task loop responsible to run the CORE thread functionality.
 */
void CORE_task()
{
    printk("Hello CORE!\n");
    u8_t version[4] = {0};
    zt_channel_get(ZT_FIRMWARE_VERSION_CHANNEL, ZT_REF(version));
    struct version *v = (struct version *) version;
    printk("Firmware version: %d.%d.%d\n", v->major, v->minor, v->build);
    u8_t light_level = 0;
    u8_t load        = 0;
    u8_t mc[2]       = {0};
    while (1) {
        k_sem_take(&core_event_sem, K_FOREVER);
        zt_channel_get(ZT_MANUAL_LOAD_CONTROL_CHANNEL, ZT_REF(mc));
        if (mc[0] == 1) {
            load = mc[1];
            printk("[CORE]: Manual load control -> Load = %s\n", load ? "on" : "off");
        } else {
            zt_channel_get(ZT_LIGHT_LEVEL_CHANNEL, ZT_REF(light_level));
            load = light_level < 96;
            printk("[CORE]: Light level is %03u -> Load = %s\n", light_level,
                   load ? "on" : "off");
        }
        zt_channel_set(ZT_LOAD_CHANNEL, ZT_REF(load));
    }
}

ZT_SERVICE_INIT(CORE, CORE_task, CORE_service_callback);
