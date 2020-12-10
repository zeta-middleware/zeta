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
    zt_data_t *version = ZT_DATA_BYTES(4, 0);
    zt_chan_read(ZT_FIRMWARE_VERSION_CHANNEL, version);
    struct version *v = (struct version *) version->bytes.value;
    printk("Firmware version: %d.%d.%d\n", v->major, v->minor, v->build);
    zt_data_t *load        = ZT_DATA_U8(0);
    zt_data_t *light_level = ZT_DATA_U8(0);
    zt_data_t *mc          = ZT_DATA_U16(0);
    while (1) {
        k_sem_take(&core_event_sem, K_FOREVER);
        zt_chan_read(ZT_MANUAL_LOAD_CONTROL_CHANNEL, mc);
        if (mc->bytes.value[0] == 1) {
            load->u8.value = mc->bytes.value[1];
            printk("[CORE]: Manual load control -> Load = %s\n",
                   load->u8.value ? "on" : "off");
        } else {
            zt_chan_read(ZT_LIGHT_LEVEL_CHANNEL, light_level);
            load->u8.value = light_level->u8.value < 96;
            printk("[CORE]: Light level is %03u -> Load = %s\n", light_level->u8.value,
                   load->u8.value ? "on" : "off");
        }
        zt_chan_pub(ZT_LOAD_CHANNEL, load);
    }
}

ZT_SERVICE_DECLARE(CORE, CORE_task, CORE_service_callback);
