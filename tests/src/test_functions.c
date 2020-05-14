#include <ztest.h>

#include "zeta.h"
#include "zeta_unit_tests.h"

K_SEM_DEFINE(ztest_sem, 0, 1);
K_SEM_DEFINE(zt_core_pend_evt, 0, 1);
K_SEM_DEFINE(zt_app_pend_evt, 0, 1);

u8_t sensor_a_hit           = 0;
u8_t sensor_b_hit           = 0;
u8_t count_data_read        = 0;
u8_t running_urgent_routine = 0;
k_tid_t read_data_last_thread;
zt_channel_e zt_core_evt_id;


int pre_publish_power(zt_channel_e id, u8_t *channel_value, size_t size)
{
    *channel_value = *channel_value + 28;
    return 0;
}

int pos_publish_power(zt_channel_e id, u8_t *channel_value, size_t size)
{
    running_urgent_routine = (*channel_value > 30);
    return 0;
}

int power_validate_different_zero(u8_t *data, size_t size)
{
    u16_t *power_val = (u16_t *) data;
    return *power_val != 0x0000;
}

int pre_read_data_val(zt_channel_e id, u8_t *channel_value, size_t size)
{
    count_data_read++;
    return 0;
}

int pos_read_data_val(zt_channel_e id, u8_t *channel_value, size_t size)
{
    read_data_last_thread = k_current_get();
    static u8_t data      = 0;
    data                  = (data < 10) ? data + 1 : data;
    *channel_value        = data;
    return 0;
}

void CORE_task(void)
{
    int error = 0;
    while (1) {
        u16_t data = 0;
        k_sem_take(&zt_core_pend_evt, K_FOREVER);
        switch (zt_core_evt_id) {
        case ZT_POWER_VAL_CHANNEL:
            error = zt_channel_read(ZT_POWER_VAL_CHANNEL, (u8_t *) &data, sizeof(data));
            if (running_urgent_routine) {
                zassert_equal(data, 30,
                              "POWER_VAL channel was not publish correctly %d!\n", data);
            } else {
                zassert_equal(data, 29,
                              "POWER_VAL channel was not publish correctly %d!\n", data);
            }
            break;
        default:
            break;
        }
    }
}

void CORE_service_callback(zt_channel_e id)
{
    zt_core_evt_id = id;
    k_sem_give(&zt_core_pend_evt);
}


void HAL_task(void)
{
    u8_t data = 0;
    int error = 0;

    /* Testing invalid calls to DATA_VAL channel */
    error = zt_channel_read(ZT_CHANNEL_COUNT, &data, sizeof(data));
    zassert_equal(error, -ENODATA,
                  "Get function is allowing read data from a non existent channel!\n");
    zt_data_t *g0 = ZT_DATA_U8(0);
    error         = zt_channel_data_read(ZT_CHANNEL_COUNT, g0);
    zassert_equal(error, -ENODATA,
                  "Get function is allowing read data from a non existent channel!\n");


    error = zt_channel_read(ZT_DATA_VAL_CHANNEL, &data, 40);
    zassert_equal(error, -EINVAL,
                  "Get function either isn't checking data size or is checking wrong, "
                  "error code: %d!\n",
                  error);
    zt_data_t *g1 = ZT_DATA_U64(0);
    error         = zt_channel_data_read(ZT_DATA_VAL_CHANNEL, g1);
    zassert_equal(error, -EINVAL,
                  "Get function either isn't checking data size or is checking wrong, "
                  "error code: %d!\n",
                  error);

    error = zt_channel_read(ZT_DATA_VAL_CHANNEL, NULL, sizeof(data));
    zassert_equal(error, -EFAULT,
                  "Get function is allowing the call with data parameter NULL!\n");

    /* Testing valid read call to DATA_VAL channel */
    error = zt_channel_read(ZT_DATA_VAL_CHANNEL, &data, sizeof(data));
    zassert_false(error, "Error executing a valid publish call!\n");
    zassert_true(count_data_read, "DATA_VAL pre read function is not working properly\n");
    zassert_equal(data, 1, "DATA_VAL pre read function is not working properly\n");
    zt_data_t *g2 = ZT_DATA_U8(0);
    error         = zt_channel_data_read(ZT_DATA_VAL_CHANNEL, g2);
    zassert_false(error, "Error executing a valid publish call!\n");
    zassert_equal(count_data_read, 2,
                  "DATA_VAL pre read function is not working properly\n");
    zassert_equal(g2->u8.value, 2,
                  "DATA_VAL pre read function is not working properly\n");

    /* Calculating power_val variable */
    u16_t power_val = 1;
    u8_t power      = 2;
    for (u8_t i = 1; i <= data; ++i) {
        power_val *= power;
    }

    /* Testing invalid publish calls to POWER_VAL channel*/
    error = zt_channel_publish(ZT_CHANNEL_COUNT, &data, sizeof(data));
    zassert_equal(error, -ENODATA,
                  "Set function is allowing publish data from a non existent channel!\n");
    zt_data_t *d0 = ZT_DATA_U8(0);
    error         = zt_channel_data_publish(ZT_CHANNEL_COUNT, d0);
    zassert_equal(error, -ENODATA,
                  "Set function is allowing publish data from a non existent channel!\n");


    error = zt_channel_publish(ZT_POWER_VAL_CHANNEL, NULL, 2);
    zassert_equal(error, -EFAULT,
                  "Set function is allowing the call with data paramemter NULL!\n");


    error = zt_channel_publish(ZT_POWER_VAL_CHANNEL, (u8_t *) &power_val, 1);
    zassert_equal(error, -EINVAL,
                  "Set function either isn't checking data size or is checking wrong, "
                  "error code: %d!\n",
                  error);
    zt_data_t *d1 = ZT_DATA_U8(power_val);
    error         = zt_channel_data_publish(ZT_POWER_VAL_CHANNEL, d1);
    zassert_equal(error, -EINVAL,
                  "Set function either isn't checking data size or is checking wrong, "
                  "error code: %d!\n",
                  error);

    u8_t empty_data[2] = {0};
    error = zt_channel_publish(ZT_POWER_VAL_CHANNEL, empty_data, sizeof(empty_data));
    zassert_equal(error, -EAGAIN,
                  "Set function is allowing publish a value that doesn't is valid to "
                  "POWER_VAL channel!\n");
    zt_data_t *d2 = ZT_DATA_U16(0);
    error         = zt_channel_data_publish(ZT_POWER_VAL_CHANNEL, d2);
    zassert_equal(error, -EAGAIN,
                  "Set function is allowing publish a value that doesn't is valid to "
                  "POWER_VAL channel!\n");

    /* Testing valid publish call to POWER_VAL channel */
    power_val = 50;
    error =
        zt_channel_publish(ZT_POWER_VAL_CHANNEL, (u8_t *) &power_val, sizeof(power_val));
    zassert_equal(error, 0, "Error executing a valid publish call!\n");
    zassert_equal(running_urgent_routine, 1,
                  "POWER_VAL pos publish function didn't run properly!\n");
    zt_data_t *d3 = ZT_DATA_U16(0);
    zt_channel_data_read(ZT_POWER_VAL_CHANNEL, d3);
    zassert_equal(d3->u16.value, 78, "POWER_VAL (%d) isn't the expected value 78",
                  d3->u16.value);
    d3->u16.value = 1;
    error         = zt_channel_data_publish(ZT_POWER_VAL_CHANNEL, d3);
    zassert_equal(error, 0, "Error executing a valid publish call!\n");
    zassert_equal(running_urgent_routine, 0,
                  "POWER_VAL pos publish function didn't run properly!\n");

    /* Testing react_on field on SENSOR_A_CHANGE creation */
    data  = 1;
    error = zt_channel_publish(ZT_SENSOR_A_CHANGE_CHANNEL, (u8_t *) &data, sizeof(u8_t));
    zassert_equal(error, 0, "Error executing a valid publish call!\n");
    zassert_equal(
        sensor_a_hit, 1,
        "APP callback was not called with a valid call(value different from existent)\n");
    zt_channel_publish(ZT_SENSOR_A_CHANGE_CHANNEL, (u8_t *) &data, sizeof(u8_t));
    zassert_equal(sensor_a_hit, 1,
                  "APP callback was called on a publish procedure without changes on "
                  "channel value!\n");

    /* Testing react_on field on SENSOR_B_UPDATE creation  */
    error = zt_channel_publish(ZT_SENSOR_B_UPDATE_CHANNEL, (u8_t *) &data, sizeof(u8_t));
    zassert_equal(error, 0, "Error executing a valid publish call!\n");
    zassert_equal(sensor_b_hit, 1, "APP callback was not called with a valid call\n");
    zt_channel_publish(ZT_SENSOR_B_UPDATE_CHANNEL, (u8_t *) &data, sizeof(u8_t));
    zassert_equal(sensor_b_hit, 2,
                  "APP callback was not called on a channel that react on update!\n");

    k_sleep(K_MSEC(100));
    k_sem_give(&ztest_sem);
}

void APP_task(void)
{
}

void HAL_service_callback(zt_channel_e id)
{
}

void APP_service_callback(zt_channel_e id)
{
    if (id == ZT_SENSOR_A_CHANGE_CHANNEL) {
        sensor_a_hit++;
    } else if (id == ZT_SENSOR_B_UPDATE_CHANNEL) {
        sensor_b_hit++;
    }
}

ZT_SERVICE_INIT(HAL, HAL_task, HAL_service_callback);
ZT_SERVICE_INIT(CORE, CORE_task, CORE_service_callback);
ZT_SERVICE_INIT(APP, APP_task, APP_service_callback);
