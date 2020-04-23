#include <ztest.h>

#include "zeta.h"
#include "zeta_unit_tests.h"

K_SEM_DEFINE(ztest_sem, 0, 1);
K_SEM_DEFINE(zeta_core_pend_evt, 0, 1);

u8_t count_data_get         = 0;
u8_t running_urgent_routine = 0;
k_tid_t get_data_last_thread;
zeta_channel_e zeta_core_evt_id;


int pre_set_power(zeta_channel_e id, u8_t *channel_value, size_t size)
{
    *channel_value = *channel_value + 28;
    return 0;
}

int pos_set_power(zeta_channel_e id, u8_t *channel_value, size_t size)
{
    if (*channel_value > 20) {
        running_urgent_routine = 1;
    }
    return 0;
}

int power_validate_different_zero(u8_t *data, size_t size)
{
    u16_t *power_val = (u16_t *) data;
    return *power_val != 0x0000;
}

int pre_get_data_val(zeta_channel_e id, u8_t *channel_value, size_t size)
{
    count_data_get++;
    return 0;
}

int pos_get_data_val(zeta_channel_e id, u8_t *channel_value, size_t size)
{
    get_data_last_thread = k_current_get();
    static u8_t data     = 0;
    data                 = (data < 10) ? data + 1 : data;
    *channel_value       = data;
    return 0;
}

void CORE_task(void)
{
    int error = 0;
    while (1) {
        u16_t data = 0;
        k_sem_take(&zeta_core_pend_evt, K_FOREVER);
        switch (zeta_core_evt_id) {
        case ZETA_POWER_VAL_CHANNEL:
            error = zeta_channel_get(ZETA_POWER_VAL_CHANNEL, (u8_t *) &data, sizeof(data));
            zassert_equal(data, 30, "POWER_VAL channel was not set correctly %d!\n", data);
            k_sem_give(&ztest_sem);
            break;
        default:
            break;
        }
    }
}

void CORE_service_callback(zeta_channel_e id)
{
    zeta_core_evt_id = id;
    k_sem_give(&zeta_core_pend_evt);
}


void HAL_task(void)
{
    u8_t data = 0;
    int error = 0;

    /* Testing invalid calls to DATA_VAL channel */
    error = zeta_channel_get(ZETA_CHANNEL_COUNT, &data, sizeof(data));
    zassert_equal(error, -ENODATA,
                  "Get function is allowing get data from a non existent channel!\n");
    error = zeta_channel_get(ZETA_DATA_VAL_CHANNEL, &data, 40);
    zassert_equal(
        error, -EINVAL,
        "Get function either isn't checking data size or is checking wrong, error code: %d!\n",
        error);
    error = zeta_channel_get(ZETA_DATA_VAL_CHANNEL, NULL, sizeof(data));
    zassert_equal(error, -EFAULT, "Get function is allowing the call with data parameter NULL!\n");
    /* Testing valid get call to DATA_VAL channel */
    error = zeta_channel_get(ZETA_DATA_VAL_CHANNEL, &data, sizeof(data));
    zassert_false(error, "Error executing a valid set call!\n");
    zassert_true(count_data_get, "DATA_VAL pre get function is not working properly\n");

    /* Calculating power_val variable */
    u16_t power_val = 1;
    u8_t power      = 2;
    for (u8_t i = 1; i <= data; ++i) {
        power_val *= power;
    }

    /* Testing invalid set calls to POWER_VAL channel*/
    error = zeta_channel_set(ZETA_CHANNEL_COUNT, &data, sizeof(data));
    zassert_equal(error, -ENODATA,
                  "Set function is allowing set data from a non existent channel!\n");
    error = zeta_channel_set(ZETA_POWER_VAL_CHANNEL, NULL, 2);
    zassert_equal(error, -EFAULT, "Set function is allowing the call with data paramemter NULL!\n");
    error = zeta_channel_set(ZETA_POWER_VAL_CHANNEL, (u8_t *) &power_val, 1);
    zassert_equal(
        error, -EINVAL,
        "Set function either isn't checking data size or is checking wrong, error code: %d!\n",
        error);
    u8_t empty_data[2] = {0};
    error              = zeta_channel_set(ZETA_POWER_VAL_CHANNEL, empty_data, sizeof(empty_data));
    zassert_equal(
        error, -EAGAIN,
        "Set function is allowing set a value that doesn't is valid to POWER_VAL channel!\n");

    /* Testing valid set call to POWER_VAL channel */
    error = zeta_channel_set(ZETA_POWER_VAL_CHANNEL, (u8_t *) &power_val, sizeof(power_val));
    zassert_false(error, "Error executing a valid set call!\n");
    zassert_equal(running_urgent_routine, 1, "POWER_VAL pos set function didn't run properly!\n");
}

void APP_task(void)
{
}

void HAL_service_callback(zeta_channel_e id)
{
}

void APP_service_callback(zeta_channel_e id)
{
}
