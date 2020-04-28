/**
 * @file peripheral.c
 * @brief The PERIPHERAL service is used to abstract hardware handling
 * @author Rodrigo Peixoto
 * @version 0.1
 * @date 2020-04-28
 */
#include <zephyr.h>
#include "zeta_callbacks.h"

#define ZT_REF(x) (u8_t *) &x, sizeof(x)

u8_t light_level_sensor_fetch()
{
    return k_uptime_get();
}

/**
 * @brief This is the function used by Zeta to tell the PERIPHERAL that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing the
 * channel's id in it.
 *
 * @param id
 */
void PERIPHERAL_service_callback(zeta_channel_e id)
{
    switch (id) {
    case ZETA_LOAD_CHANNEL: {
        u8_t load = 0;
        zeta_channel_get(ZETA_LOAD_CHANNEL, ZT_REF(load));
        printk("[PERIPHERAL]: The load is turning %s\n", load ? "on" : "off");
    } break;
    default:
        printk("Unknown id");
    }
}

/**
 * @brief This is the task loop responsible to run the PERIPHERAL thread functionality.
 */
void PERIPHERAL_task()
{
    printk("Hello PERIPHERAL!\n");
    u8_t light_level = 0;
    while (1) {
        light_level = light_level_sensor_fetch();
        zeta_channel_set(ZETA_LIGHT_LEVEL_CHANNEL, ZT_REF(light_level));
        k_sleep(K_SECONDS(2));
    }
}
