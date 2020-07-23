#include <string.h>
#include <zephyr.h>
#include <ztest.h>

#include "autoconf.h"
#include "zeta.h"
#include "zeta_unit_tests.h"

void test_data()
{
    zt_data_t *data0 = ZT_DATA_S8(-1);
    zassert_equal(data0->s8.size, sizeof(s8_t),
                  "[%s] zt_data size %d is wrong. It must be 1!\n", __FUNCTION__,
                  data0->s8.size);
    zt_data_t *data1 = ZT_DATA_U8(-1);
    zassert_equal(data1->u8.size, sizeof(u8_t),
                  "[%s] zt_data size %d is wrong. It must be 1!\n", __FUNCTION__,
                  data1->u8.size);
    zt_data_t *data2 = ZT_DATA_S16(-1);
    zassert_equal(data2->s16.size, sizeof(s16_t),
                  "[%s] zt_data size %d is wrong. It must be 2!\n", __FUNCTION__,
                  data2->s16.size);
    zt_data_t *data3 = ZT_DATA_U16(-1);
    zassert_equal(data3->u16.size, sizeof(u16_t),
                  "[%s] zt_data size %d is wrong. It must be 2!\n", __FUNCTION__,
                  data3->u16.size);
    zt_data_t *data4 = ZT_DATA_S32(-1);
    zassert_equal(data4->s32.size, sizeof(s32_t),
                  "[%s] zt_data size %d is wrong. It must be 4!\n", __FUNCTION__,
                  data4->s32.size);
    zt_data_t *data5 = ZT_DATA_U32(-1);
    zassert_equal(data5->u32.size, sizeof(u32_t),
                  "[%s] zt_data size %d is wrong. It must be 4!\n", __FUNCTION__,
                  data5->s32.size);
    zt_data_t *data6 = ZT_DATA_S64(-1);
    zassert_equal(data6->s64.size, sizeof(s64_t),
                  "[%s] zt_data size %d is wrong. It must be 8!\n", __FUNCTION__,
                  data6->s64.size);
    zt_data_t *data7 = ZT_DATA_BYTES(64, 0);
    zassert_equal(data7->bytes.size, 64,
                  "[%s] zt_data size %d is wrong. It must be 64!\n", __FUNCTION__,
                  data7->bytes.size);

    zt_data_t *data8 =
        ZT_DATA_BYTES(16, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf);
    zassert_equal(data8->bytes.size, 16,
                  "[%s] zt_data size %d is wrong. It must be 20!\n", __FUNCTION__,
                  data8->bytes.size);
    for (int i = 0; i < data8->bytes.size; i++) {
        zassert_equal(
            data8->bytes.value[i], i,
            "[%s] at index %d zt_data value is wrong 0x%x. It must be 0xff !\n ",
            __FUNCTION__, i, data8->bytes.value[i]);
    }
    zassert_equal(data8->s8.value, 0x00,
                  "[%s] zt_data value is wrong %02x. It must be 0!\n", __FUNCTION__,
                  data8->s8.value);
    zassert_equal(data8->u8.value, 0x00,
                  "[%s] zt_data value is wrong %02x. It must be 0x00!\n", __FUNCTION__,
                  data8->u8.value);
    zassert_equal(data8->s16.value, 0x0100,
                  "[%s] zt_data value is wrong %04x. It must be -1!\n", __FUNCTION__,
                  data8->s16.value);
    zassert_equal(data8->u16.value, 0x0100,
                  "[%s] zt_data value is wrong %04x. It must be -1!\n", __FUNCTION__,
                  data8->u16.value);
    zassert_equal(data8->s32.value, 0x03020100,
                  "[%s] zt_data value is wrong %08x. It must be -1!\n", __FUNCTION__,
                  data8->s32.value);
    zassert_equal(data8->u32.value, 0x03020100,
                  "[%s] zt_data value is wrong %08x. It must be -1!\n", __FUNCTION__,
                  data8->u32.value);
    zassert_equal(data8->s64.value, 0x0706050403020100,
                  "[%s] zt_data value is wrong %016x. It must be -1!\n", __FUNCTION__,
                  data8->s64.value);
    zassert_equal(data8->u64.value, 0x0706050403020100,
                  "[%s] zt_data value is wrong %016x. It must be -1!\n", __FUNCTION__,
                  data8->u64.value);

    zt_data_t *data = ZT_DATA_U64(-1);
    zassert_equal(data->s8.size, sizeof(u64_t),
                  "[%s] zt_data size %d is wrong. It must be 8!\n", __FUNCTION__,
                  data->s8.size);
    zassert_equal(data->s8.value, -1, "[%s] zt_data value is wrong %d. It must be -1!\n",
                  __FUNCTION__, data->s8.value);
    zassert_equal(data->u8.value, 255, "[%s] zt_data value is wrong %d. It must be -1!\n",
                  __FUNCTION__, data->u8.value);
    zassert_equal(data->s16.value, -1, "[%s] zt_data value is wrong %d. It must be -1!\n",
                  __FUNCTION__, data->s16.value);
    zassert_equal(data->u16.value, 65535,
                  "[%s] zt_data value is wrong %d. It must be -1!\n", __FUNCTION__,
                  data->u16.value);
    zassert_equal(data->s32.value, -1, "[%s] zt_data value is wrong %d. It must be -1!\n",
                  __FUNCTION__, data->s32.value);
    zassert_equal(data->u32.value, 4294967295,
                  "[%s] zt_data value is wrong %d. It must be -1!\n", __FUNCTION__,
                  data->u32.value);
    zassert_equal(data->s64.value, -1, "[%s] zt_data value is wrong %d. It must be -1!\n",
                  __FUNCTION__, data->s64.value);
    zassert_equal(data->u64.value, 18446744073709551615U,
                  "[%s] zt_data value is wrong %llu. It must be -1!\n", __FUNCTION__,
                  data->u64.value);
    for (int i = 0; i < data->bytes.size; i++) {
        zassert_equal(
            data->bytes.value[i], 0xff,
            "[%s] at index %d zt_data value is wrong 0x%x. It must be 0xff !\n ",
            __FUNCTION__, i, data->bytes.value[i]);
    }
}

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

    /* Checking CH01 call */
    error = 1;
    name  = zt_channel_name(ZT_CH01_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_name is not setting error to 0 in a valid call!\n",
                  __FUNCTION__);
    zassert_true(!strcmp(name, "CH01"),
                 "[%s] channel #%d was created with a wrong name: %s\n", __FUNCTION__,
                 ZT_CH01_CHANNEL, name);

    /* Checking CH02 call */
    error = 1;
    name  = zt_channel_name(ZT_CH02_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_name is not setting error to 0 in a valid call!\n",
                  __FUNCTION__);
    zassert_true(!strcmp(name, "CH02"),
                 "[%s] channel #%d was created with a wrong name: %s\n", __FUNCTION__,
                 ZT_CH02_CHANNEL, name);
    /* Checking CH03 call */
    error = 1;
    name  = zt_channel_name(ZT_CH03_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_name is not setting error to 0 in a valid call!\n",
                  __FUNCTION__);
    zassert_true(!strcmp(name, "CH03"),
                 "[%s] channel #%d was created with a wrong name: %s\n", __FUNCTION__,
                 ZT_CH03_CHANNEL, name);
    /* Checking CH04 call */
    error = 1;
    name  = zt_channel_name(ZT_CH04_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_name is not setting error to 0 in a valid call!\n",
                  __FUNCTION__);
    zassert_true(!strcmp(name, "CH04"),
                 "[%s] channel #%d was created with a wrong name: %s\n", __FUNCTION__,
                 ZT_CH04_CHANNEL, name);
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

    /* Checking CH01 size*/
    sz = zt_channel_size(ZT_CH01_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 1, "[%s] zt_channel_size returned a wrong size value: %d\n",
                  __FUNCTION__, sz);
    /* Checking CH02 size*/
    sz = zt_channel_size(ZT_CH02_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 2, "[%s] zt_channel_size returned a wrong size value: %d\n",
                  __FUNCTION__, sz);

    /* Checking CH03 size*/
    sz = zt_channel_size(ZT_CH03_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 8, "[%s] zt_channel_size returned a wrong size value: %d\n",
                  __FUNCTION__, sz);
    /* Checking CH04 size*/
    sz = zt_channel_size(ZT_CH04_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 128, "[%s] zt_channel_size returned a wrong size value: %d\n",
                  __FUNCTION__, sz);
}

void test_channels_messages(void)
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

    /* Checking CH01 size*/
    sz = zt_channel_size(ZT_CH01_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 1, "[%s] zt_channel_size returned a wrong size value: %d\n",
                  __FUNCTION__, sz);
    /* Checking CH02 size*/
    sz = zt_channel_size(ZT_CH02_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 2, "[%s] zt_channel_size returned a wrong size value: %d\n",
                  __FUNCTION__, sz);

    /* Checking CH03 size*/
    sz = zt_channel_size(ZT_CH03_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 8, "[%s] zt_channel_size returned a wrong size value: %d\n",
                  __FUNCTION__, sz);
    /* Checking CH04 size*/
    sz = zt_channel_size(ZT_CH04_CHANNEL, &error);
    zassert_equal(error, 0,
                  "[%s] zt_channel_size is setting error to %d in a valid call!\n",
                  __FUNCTION__, error);
    zassert_equal(sz, 128, "[%s] zt_channel_size returned a wrong size value: %d\n",
                  __FUNCTION__, sz);
}

void test_channels_routine(void)
{
    k_sem_take(&ztest_sem, K_FOREVER);
}

void test_main(void)
{
    ztest_test_suite(ZT_CHECK_CHANNELS_GENERATION, ztest_unit_test(test_data),
                     ztest_unit_test(test_channels_name),
                     ztest_unit_test(test_channels_size),
                     ztest_unit_test(test_channels_routine));

    ztest_run_test_suite(ZT_CHECK_CHANNELS_GENERATION);
}
