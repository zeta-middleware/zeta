#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_SEM_DEFINE(CORE_callback_sem, 0, 1);


/**
 * @brief This is the function used by Zeta to tell the CORE that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing the
 * channel's id in it.
 *
 * @param id
 */
void CORE_service_callback(zt_channel_e id)
{
    k_sem_give(&CORE_callback_sem);
}

/**
 * @brief This is the task loop responsible to run the CORE thread
 * functionality.
 */
void CORE_task()
{
    LOG_DBG("CORE Service has started...[OK]");
    zt_data_t *version = ZT_DATA_U8(0);
    zt_chan_read(ZT_FIRMWARE_VERSION_CHANNEL, version);
    printk("Version %d\n", version->u8.value);
    zt_data_t *u8 = ZT_DATA_U8(0);
    while (1) {
        for (int i = 0; i < 10; i++) {
            ++u8->u8.value;
            u32_t cyc = k_cycle_get_32();
            LOG_WRN("CORE publishing cycles: %u", cyc);
            zt_chan_pub(ZT_VOLATILE_CHANNEL, u8);
        }
        k_sleep(K_SECONDS(2));
    }
}

ZT_SERVICE_INIT(CORE, CORE_task, CORE_service_callback);
