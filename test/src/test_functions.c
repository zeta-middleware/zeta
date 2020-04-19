#include "pdb.h"

K_SEM_DEFINE(pms_get_interval_sem, 0, 1);

struct k_timer pms_sleep_timer;
void pms_sleep_timer_function(struct k_timer *timer_id)
{
    k_sem_give(&pms_get_interval_sem);
}

int pos_set_reach_limit(pdb_channel_e id, u8_t *channel_value, size_t size)
{
    return 0;
}
int pre_set_power_calibrate(pdb_channel_e id, u8_t *channel_value, size_t size)
{
    return 0;
}

int power_validate_different_of_zero(u8_t *data, size_t size)
{
    return 0;
}

void HAL_task(void)
{
}

void CORE_task(void)
{
}

void APP_task(void)
{
}

void CORE_service_callback(pdb_channel_e id)
{
}

void HAL_service_callback(pdb_channel_e id)
{
}

void APP_service_callback(pdb_channel_e id)
{
}
