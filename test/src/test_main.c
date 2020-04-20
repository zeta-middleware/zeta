#include <string.h>
#include <zephyr.h>
#include <ztest.h>

#include "autoconf.h"
#include "zeta.h"


void test_channels_name(void)
{
    int error        = 0;
    const char *name = NULL;

    /* Checking an invalid call */
    name = zeta_channel_name(ZETA_CHANNEL_COUNT, &error);
    zassert_equal(error, -EINVAL, "[%s] zeta_channel_name is allowing an invalid channel id!\n",
                  __FUNCTION__);
    zassert_equal(name, NULL,
                  "[%s] zeta_channel_name is not returning NULL pointer in an invalid call!\n",
                  __FUNCTION__);
    /* Checking FIRMWARE_VERSION call */
    error = 1;
    name  = zeta_channel_name(ZETA_FIRMWARE_VERSION_CHANNEL, &error);
    zassert_equal(error, 0, "[%s] zeta_channel_name is not setting error to 0 in a valid call!\n",
                  __FUNCTION__);
    zassert_true(!strcmp(name, "FIRMWARE_VERSION"),
                 "[%s] channel #%d was created with a wrong name: %s\n", __FUNCTION__,
                 ZETA_FIRMWARE_VERSION_CHANNEL, name);

    /* Checking COUNT_REACH_LIMIT call */
    error = 1;
    name  = zeta_channel_name(ZETA_COUNT_REACH_LIMIT_CHANNEL, &error);
    zassert_equal(error, 0, "[%s] zeta_channel_name is not setting error to 0 in a valid call!\n",
                  __FUNCTION__);
    zassert_true(!strcmp(name, "COUNT_REACH_LIMIT"),
                 "[%s] channel #%d was created with a wrong name: %s\n", __FUNCTION__,
                 ZETA_COUNT_REACH_LIMIT_CHANNEL, name);

    /* Checking PMS_SENSOR_VAL call */
    error = 1;
    name  = zeta_channel_name(ZETA_PMS_SENSOR_VAL_CHANNEL, &error);
    zassert_equal(error, 0, "[%s] zeta_channel_name is not setting error to 0 in a valid call!\n",
                  __FUNCTION__);
    zassert_true(!strcmp(name, "PMS_SENSOR_VAL"),
                 "[%s] channel #%d was created with a wrong name: %s\n", __FUNCTION__,
                 ZETA_PMS_SENSOR_VAL_CHANNEL, name);

    /* Checking POWER_VAL call */
    error = 1;
    name  = zeta_channel_name(ZETA_POWER_VAL_CHANNEL, &error);
    zassert_equal(error, 0, "[%s] zeta_channel_name is not setting error to 0 in a valid call!\n",
                  __FUNCTION__);
    zassert_true(!strcmp(name, "POWER_VAL"), "[%s] channel #%d was created with a wrong name: %s\n",
                 __FUNCTION__, ZETA_POWER_VAL_CHANNEL, name);
}

void test_properties_set(void)
{
    /* u32_t new_firmware_version = 0xABCDED0F; */
    /* u8_t value                 = 0; */
    /* int error                  = 0; */

    /* /\* Testing if set functions was correct assigned *\/ */
    /* error = zeta_property_set(ZETA_FIRMWARE_VERSION_PROPERTY,
     * ZETA_VALUE_REF(new_firmware_version));
     */
    /* zassert_equal(error, -ENODEV, */
    /*               "FIRMWARE_VERSION property was defined with a non null set pointer!"); */

    /* error = zeta_property_set(ZETA_PERSISTENT_VAL_PROPERTY, ZETA_VALUE_REF(value)); */
    /* zassert_equal(error, -EINVAL, */
    /*               "PERSISTENT_VAL property is allowing set a value zero to property: %d!",
     * error); */
    /* value = 0xF1; */
    /* error = zeta_property_set(ZETA_PERSISTENT_VAL_PROPERTY, ZETA_VALUE_REF(value)); */
    /* zassert_equal(error, 0, "PERSISTENT_VAL property is not setting a valid value(%X), error:
     * %d", */
    /*               value, error); */

    /* error = zeta_property_set(ZETA_SET_GET_PROPERTY, ZETA_VALUE_REF(value)); */
    /* zassert_equal(error, 0, "SET_GET property is not setting a valid value(%X), error: %d",
     * value, */
    /*               error); */
    /* error = zeta_property_set(ZETA_ECHO_HAL_PROPERTY, ZETA_VALUE_REF(value)); */
    /* zassert_equal(error, 0, "ECHO_HAL property is not setting a valid value(%X), error: %d",
     * value, */
    /*               error); */
}

void test_properties_get(void)
{
    /* u8_t firmware_version[4] = {0}; */
    /* u8_t value               = 0; */
    /* int error                = 0; */

    /* error = */
    /*     zeta_property_get(ZETA_FIRMWARE_VERSION_PROPERTY, firmware_version,
     * sizeof(firmware_version)); */
    /* zassert_false(error, */
    /*               "ZETA is not allowing get value from property FIRMWARE_VERSION, error code:
     * %d!", */
    /*               error); */
    /* zassert_equal(0xF1, firmware_version[0], */
    /*               "FIRMWARE_VERSION property must to has 0xF1 as the value of the first byte, "
     */
    /*               "value found %02X!", */
    /*               firmware_version[0]); */
    /* zassert_equal(0xF2, firmware_version[1], */
    /*               "FIRMWARE_VERSION property must to has 0xF2 as the value of the second byte, "
     */
    /*               "value found %02X!", */
    /*               firmware_version[1]); */
    /* zassert_equal(0xF3, firmware_version[2], */
    /*               "FIRMWARE_VERSION property must to has 0xF3 as the value of the third byte, "
     */
    /*               "value found %02X!", */
    /*               firmware_version[2]); */
    /* zassert_equal(0xF4, firmware_version[3], */
    /*               "FIRMWARE_VERSION property must to has 0xF4 as the value of the fourth byte, "
     */
    /*               "value found %02X!", */
    /*               firmware_version[3]); */

    /* error = zeta_property_get(ZETA_PERSISTENT_VAL_PROPERTY, ZETA_VALUE_REF(value)); */
    /* zassert_equal(0xF1, value, */
    /*               "PERSISTENT_VAL property must to has 0xF1 as the value, value found %02X!", */
    /*               value); */

    /* error = zeta_property_get(ZETA_SET_GET_PROPERTY, ZETA_VALUE_REF(value)); */
    /* zassert_equal(0xF3, value, "SET_GET property must to has 0xF3 as the value, value found
     * %02X!", */
    /*               value); */
}

void test_channels_size(void)
{
    size_t sz = 0;
    int error = 0;

    /* Checking an invalid call */
    sz = zeta_channel_size(ZETA_CHANNEL_COUNT, &error);
    zassert_equal(error, -EINVAL, "[%s] zeta_channel_size is not setting error to -EINVAL!\n",
                  __FUNCTION__);
    zassert_equal(sz, 0, "[%s] zeta_channel_size is not returning 0 in an invalid call!\n",
                  __FUNCTION__);

    /* Checking FIRMWARE_VERSION size*/
    sz = zeta_channel_size(ZETA_FIRMWARE_VERSION_CHANNEL, &error);
    zassert_equal(error, 0, "[%s] zeta_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 4, "[%s] zeta_channel_size returned a wrong size value: %d\n", __FUNCTION__,
                  sz);

    /* Checking COUNT_REACH_LIMIT size*/
    sz = zeta_channel_size(ZETA_COUNT_REACH_LIMIT_CHANNEL, &error);
    zassert_equal(error, 0, "[%s] zeta_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 1, "[%s] zeta_channel_size returned a wrong size value: %d\n", __FUNCTION__,
                  sz);

    /* Checking POWER_VAL size*/
    sz = zeta_channel_size(ZETA_POWER_VAL_CHANNEL, &error);
    zassert_equal(error, 0, "[%s] zeta_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 2, "[%s] zeta_channel_size returned a wrong size value: %d\n", __FUNCTION__,
                  sz);

    /* Checking PMS_SENSOR_VAL size*/
    sz = zeta_channel_size(ZETA_PMS_SENSOR_VAL_CHANNEL, &error);
    zassert_equal(error, 0, "[%s] zeta_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 1, "[%s] zeta_channel_size returned a wrong size value: %d\n", __FUNCTION__,
                  sz);
}

int pre_get_pms_wakeup(zeta_channel_e id, u8_t *channel_value, size_t size)
{
    return 0;
}

int pos_get_pms_sleep(zeta_channel_e id, u8_t *channel_value, size_t size)
{
    return 0;
}

void test_channels_get(void)
{
    u8_t data = 0;
    zeta_channel_get(ZETA_PMS_SENSOR_VAL_CHANNEL, &data, sizeof(data));
}

void test_main(void)
{
    ztest_test_suite(ZETA_CHECK_CHANNELS_GENERATION, ztest_unit_test(test_channels_name),
                     ztest_unit_test(test_channels_size), ztest_unit_test(test_channels_get));

    ztest_run_test_suite(ZETA_CHECK_CHANNELS_GENERATION);
}
