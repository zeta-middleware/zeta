#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

static u8_t get_sensor_a(void)
{
    static u8_t data_a = 20;

    data_a++;
    if (data_a > 40) {
        data_a = 20;
    }

    return data_a;
}

static u8_t get_sensor_b(void)
{
    static u8_t data_b = 90;

    data_b--;
    if (data_b < 40) {
        data_b = 90;
    }

    return data_b;
}

static u32_t get_sensor_c(void)
{
    static u32_t data_c = 101325;

    data_c += 27;
    if (data_c > 102000) {
        data_c = 101325;
    }

    return data_c;
}

void BOARD_task()
{
    LOG_DBG("BOARD Service has started...[OK]");
    int err = 0;
    zt_data_t *data_a;
    zt_data_t *data_b;
    zt_data_t *data_c;
    while (1) {
        {
            data_a = ZT_DATA_U8(get_sensor_a());
            err    = zt_channel_data_publish(ZT_SENSOR_A_CHANNEL, data_a);

            data_b = ZT_DATA_U8(get_sensor_b());
            zt_channel_data_publish(ZT_SENSOR_B_CHANNEL, data_b);

            data_c = ZT_DATA_U32(get_sensor_c());
            zt_channel_data_publish(ZT_SENSOR_C_CHANNEL, data_c);
        }
        k_sleep(K_SECONDS(10));
    }
}

ZT_SERVICE_INIT(BOARD, BOARD_task, NULL);
