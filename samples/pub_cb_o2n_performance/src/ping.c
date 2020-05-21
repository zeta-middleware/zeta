#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>
#include "kernel.h"
#include "sys/printk.h"
#include "zephyr/types.h"

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_SEM_DEFINE(PING_callback_sem, 0, 1);


u32_t end_cycles   = 0;
u32_t total_cycles = 0;
u32_t start_cycles = 0;
/**
 * @brief This is the function used by Zeta to tell the PING that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing the
 * channel's id in it.
 *
 * @param id
 */
void PING_service_callback(zt_channel_e id)
{
    k_sem_give(&PING_callback_sem);
}

/**
 * @brief This is the task loop responsible to run the PING thread
 * functionality.
 */
void PING_task()
{
    LOG_DBG("PING Service has started...[OK]");
    u8_t current_channel     = ZT_C01_CHANNEL;
    u8_t number_of_callbacks = 1;
    zt_data_t *ping_data     = ZT_DATA_U32(0xF0F0F0F0);
    total_cycles             = 0;
    start_cycles             = k_cycle_get_32();
    zt_chan_pub(current_channel, ping_data);
    int count = 1000;
    while (1) {
        k_sem_take(&PING_callback_sem, K_FOREVER);
        /* printk("\rCount = %04d", count); */
        if (count == 0) {
            count               = 1001;
            number_of_callbacks = current_channel - ZT_PONG_CHANNEL;
            printk("[%u bytes]Total cycles = %u\n", number_of_callbacks, total_cycles);
            printk("[%u bytes]Total in us = %llu\n", number_of_callbacks,
                   k_cyc_to_us_floor64(total_cycles));
            printk("[%u bytes]Mean in us = %llu\n", number_of_callbacks,
                   k_cyc_to_us_floor64(total_cycles) / (number_of_callbacks * 1000));
            total_cycles = 0;
            if (current_channel < ZT_C10_CHANNEL) {
                ++current_channel;
            } else {
                printk("END of test\n");
                while (1) {
                    k_sleep(K_SECONDS(1));
                }
            }
        }
        --count;
        /*  Start another interaction */
        start_cycles = k_cycle_get_32();
        zt_chan_pub(current_channel, ping_data);
    }
}

ZT_SERVICE_INIT(PING, PING_task, PING_service_callback);
