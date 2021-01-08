#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>
#include "kernel.h"
#include "sys/printk.h"
#include "zephyr/types.h"

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_SEM_DEFINE(PING_callback_sem, 0, 1);


u32_t end_cycles = 0;
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
    u8_t current_channel    = 0;
    zt_data_t *ping_data[9] = {ZT_DATA_U8(0),
                               ZT_DATA_U16(ZT_PING_DATA_2_CHANNEL),
                               ZT_DATA_U32(ZT_PING_DATA_4_CHANNEL),
                               ZT_DATA_U64(ZT_PING_DATA_8_CHANNEL),
                               ZT_DATA_BYTES(16, ZT_PING_DATA_16_CHANNEL),
                               ZT_DATA_BYTES(32, ZT_PING_DATA_32_CHANNEL),
                               ZT_DATA_BYTES(64, ZT_PING_DATA_64_CHANNEL),
                               ZT_DATA_BYTES(128, ZT_PING_DATA_128_CHANNEL),
                               ZT_DATA_BYTES(255, ZT_PING_DATA_255_CHANNEL)};

    u32_t total_cycles = 0;
    u32_t start_cycles = k_cycle_get_32();
    zt_chan_pub(ZT_PING_DATA_1_CHANNEL, ping_data[current_channel >> 1]);
    int count = 1000;
    while (1) {
        k_sem_take(&PING_callback_sem, K_FOREVER);
        // end_cycles = k_cycle_get_32();
        total_cycles += (end_cycles - start_cycles);
        /* printk("\rCount = %04d", count); */
        if (count == 0) {
            count = 1001;
            printk("[%u bytes]Total cycles = %u\n", 1 << current_channel, total_cycles);
            printk("[%u bytes]Total in us = %llu\n", 1 << current_channel,
                   k_cyc_to_us_floor64(total_cycles));
            printk("[%u bytes]Mean in us = %llu\n", 1 << current_channel,
                   k_cyc_to_us_floor64(total_cycles) / 1000);
            total_cycles = 0;
            if (current_channel < 11) {
                ++current_channel;
            } else {
                printk("END of test\n");
                k_sleep(K_SECONDS(1000));
            }
        }
        --count;
        /*  Start another interaction */
        start_cycles = k_cycle_get_32();
        zt_chan_pub(1 + (current_channel << 1), ping_data[current_channel]);
    }
}

ZT_SERVICE_INIT(PING, PING_task, PING_service_callback);
