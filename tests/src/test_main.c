#include <string.h>
#include <zephyr.h>
#include <ztest.h>

#include "autoconf.h"
#include "zeta.h"
#include "zeta_threads.h"
#include "zeta_unit_tests.h"

void test_channels_name(void)
{
    int error        = 0;
    const char *name = NULL;

    /* Checking an invalid call */
    name = zt_channel_name(ZT_CHANNEL_COUNT, &error);
    zassert_equal(error, -EINVAL,
                  "[%s] zt_channel_name is allowing an invalid channel id!\n",
                  __FUNCTION__);
    zassert_equal(
        name, NULL,
        "[%s] zt_channel_name is not returning NULL pointer in an invalid call!\n",
        __FUNCTION__);
    /* Checking FIRMWARE_VERSION call */
    error = 1;
    name  = zt_channel_name(ZT_FIRMWARE_VERSION_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_name is not setting error to 0 in a valid call!\n",
                  __FUNCTION__);
    zassert_true(!strcmp(name, "FIRMWARE_VERSION"),
                 "[%s] channel #%d was created with a wrong name: %s\n", __FUNCTION__,
                 ZT_FIRMWARE_VERSION_CHANNEL, name);

    /* Checking DATA_VAL call */
    error = 1;
    name  = zt_channel_name(ZT_DATA_VAL_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_name is not setting error to 0 in a valid call!\n",
                  __FUNCTION__);
    zassert_true(!strcmp(name, "DATA_VAL"),
                 "[%s] channel #%d was created with a wrong name: %s\n", __FUNCTION__,
                 ZT_DATA_VAL_CHANNEL, name);

    /* Checking POWER_VAL call */
    error = 1;
    name  = zt_channel_name(ZT_POWER_VAL_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_name is not setting error to 0 in a valid call!\n",
                  __FUNCTION__);
    zassert_true(!strcmp(name, "POWER_VAL"),
                 "[%s] channel #%d was created with a wrong name: %s\n", __FUNCTION__,
                 ZT_POWER_VAL_CHANNEL, name);
}

void test_channels_size(void)
{
    size_t sz = 0;
    int error = 0;

    /* Checking an invalid call */
    sz = zt_channel_size(ZT_CHANNEL_COUNT, &error);
    zassert_equal(error, -EINVAL,
                  "[%s] zt_channel_size is not setting error to -EINVAL!\n",
                  __FUNCTION__);
    zassert_equal(sz, 0, "[%s] zt_channel_size is not returning 0 in an invalid call!\n",
                  __FUNCTION__);

    /* Checking FIRMWARE_VERSION size*/
    sz = zt_channel_size(ZT_FIRMWARE_VERSION_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 4, "[%s] zt_channel_size returned a wrong size value: %d\n",
                  __FUNCTION__, sz);

    /* Checking POWER_VAL size*/
    sz = zt_channel_size(ZT_POWER_VAL_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 2, "[%s] zt_channel_size returned a wrong size value: %d\n",
                  __FUNCTION__, sz);

    /* Checking DATA_VAL size*/
    sz = zt_channel_size(ZT_DATA_VAL_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 1, "[%s] zt_channel_size returned a wrong size value: %d\n",
                  __FUNCTION__, sz);
}

void test_channels_routine(void)
{
    k_sem_take(&ztest_sem, K_FOREVER);
    /* zassert_true(count_data_get > 0, "Data count should be different of 0!\n"); */
    /* zassert_equal(HAL_thread_id, get_data_last_thread, */
    /*               "The last thread that get DATA_VAL channel should be the HAL
     * thread!\n"); */
}

void test_main(void)
{
    ztest_test_suite(ZT_CHECK_CHANNELS_GENERATION, ztest_unit_test(test_channels_name),
                     ztest_unit_test(test_channels_size),
                     ztest_unit_test(test_channels_routine));

    ztest_run_test_suite(ZT_CHECK_CHANNELS_GENERATION);
}
