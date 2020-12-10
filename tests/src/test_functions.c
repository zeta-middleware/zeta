#include <string.h>
#include <ztest.h>

#include "zephyr/types.h"
#include "zeta.h"
#include "zeta_unit_tests.h"
#include "ztest_assert.h"

K_SEM_DEFINE(ztest_sem, 0, 1);
K_SEM_DEFINE(zt_core_pend_evt, 0, 1);
K_SEM_DEFINE(zt_app_pend_evt, 0, 1);

u8_t sensor_a_hit = 0;
u8_t sensor_b_hit = 0;
u8_t sensor_c_hit = 0;
zt_channel_e zt_core_evt_id;

void PONG_task(void)
{
    int error      = 0;
    int count      = 0;
    u16_t expected = 0;
    while (1) {
        zt_data_t *data = ZT_DATA_U16(0);
        k_sem_take(&zt_core_pend_evt, K_FOREVER);
        if (zt_core_evt_id == ZT_CH02_CHANNEL) {
            error = zt_chan_read(ZT_CH02_CHANNEL, data);
            if (count == 0) {
                expected = 0xbbaa;
                count++;
            } else {
                expected = 0x01;
            }
            zassert_equal(data->u16.value, expected,
                          "CH02 channel was not publish correctly %x!\n",
                          data->u16.value);
        }
    }
}

void PONG_service_callback(zt_channel_e id)
{
    if (id == ZT_CH05_CHANNEL) {
        sensor_c_hit++;
    }
    zt_core_evt_id = id;
    k_sem_give(&zt_core_pend_evt);
}


void PING_task(void)
{
    zt_data_t *data = ZT_DATA_U8(0);
    int error       = 0;

    /* Testing invalid calls to CH01 channel */
    error = zt_chan_read(ZT_CHANNEL_COUNT, data);
    zassert_equal(error, -ENODATA,
                  "Get function is allowing read data from a non existent channel!\n");
    zt_data_t *g0 = ZT_DATA_U8(0);
    error         = zt_chan_read(ZT_CHANNEL_COUNT, g0);
    zassert_equal(error, -ENODATA,
                  "Get function is allowing read data from a non existent channel!\n");

    error = zt_chan_read(ZT_CH01_CHANNEL, ZT_DATA_BYTES(40, 0));
    zassert_equal(error, -EINVAL,
                  "Get function either isn't checking data size or is checking wrong, "
                  "error code: %d!\n",
                  error);

    zt_data_t *g1 = ZT_DATA_U64(0);
    error         = zt_chan_read(ZT_CH01_CHANNEL, g1);
    zassert_equal(error, -EINVAL,
                  "Get function either isn't checking data size or is checking wrong, "
                  "error code: %d!\n",
                  error);

    error = zt_chan_read(ZT_CH01_CHANNEL, NULL);
    zassert_equal(error, -EFAULT,
                  "Get function is allowing the call with data parameter NULL!\n");

    /* Testing invalid publish calls to CH02 channel*/
    error = zt_chan_pub(ZT_CHANNEL_COUNT, data);
    zassert_equal(error, -ENODATA,
                  "Set function is allowing publish data from a non existent channel!\n");
    zt_data_t *d0 = ZT_DATA_U8(0);
    error         = zt_chan_pub(ZT_CHANNEL_COUNT, d0);
    zassert_equal(error, -ENODATA,
                  "Set function is allowing publish data from a non existent channel!\n");
    error = zt_chan_pub(ZT_CH02_CHANNEL, NULL);
    zassert_equal(error, -EFAULT,
                  "Set function is allowing the call with data paramemter NULL!\n");
    error = zt_chan_pub(ZT_CH02_CHANNEL, data);
    zassert_equal(error, -EINVAL,
                  "Set function either isn't checking data size or is checking wrong, "
                  "error code: %d!\n",
                  error);
    error = zt_chan_pub(ZT_CH01_CHANNEL, ZT_DATA_U8(0));
    zassert_equal(error, -EPERM,
                  "Publish function is not checking the readonly filed before publish, "
                  "error code: %d!\n",
                  error);
    zt_data_t *d1 = ZT_DATA_U64(0);
    error         = zt_chan_pub(ZT_CH02_CHANNEL, d1);
    zassert_equal(error, -EINVAL,
                  "Set function either isn't checking data size or is checking wrong, "
                  "error code: %d!\n",
                  error);

    /* Testing valid publish call to CH02 channel */
    error = zt_chan_pub(ZT_CH02_CHANNEL, ZT_DATA_U16(0xbbaa));
    zassert_equal(error, 0, "Error executing a valid publish call!\n");
    /* zassert_equal(running_urgent_routine, 1, */
    /*               "CH02 pos publish function didn't run properly!\n"); */
    zt_data_t *d3 = ZT_DATA_U16(0);
    zt_chan_read(ZT_CH02_CHANNEL, d3);
    zassert_equal(d3->u16.value, 0xbbaa, "CH02 (%x) isn't the expected value 0xbbaa",
                  d3->u16.value);
    d3->u16.value = 1;
    error         = zt_chan_pub(ZT_CH02_CHANNEL, d3);
    zassert_equal(error, 0, "Error executing a valid publish call!\n");
    zt_chan_read(ZT_CH02_CHANNEL, d3);
    zassert_equal(d3->u16.value, 1, "CH02 (%d) isn't the expected value 1",
                  d3->u16.value);

    /* Testing react_on field on CH03 creation */
    zt_data_t *ch03 = ZT_DATA_U64(0);
    zt_chan_read(ZT_CH03_CHANNEL, ch03);
    zassert_equal(ch03->u64.value, 0, "Error old value is wrong: %x", ch03->u64.value);
    ch03->u64.value = 0xff;
    error           = zt_chan_pub(ZT_CH03_CHANNEL, ch03);
    zassert_equal(error, 0, "Error executing a valid publish call!\n");
    zt_chan_read(ZT_CH03_CHANNEL, ch03);
    zassert_equal(ch03->u64.value, 0xff, "Error old value is wrong: %x", ch03->u64.value);
    zassert_equal(sensor_a_hit, 1,
                  "PONG2 callback was not called with a valid call(value different from "
                  "existent) %d\n",
                  sensor_a_hit);
    error = zt_chan_pub(ZT_CH03_CHANNEL, ch03);
    zassert_equal(error, 0, "Error executing a valid publish call!\n");
    zassert_equal(sensor_a_hit, 1,
                  "PONG2 callback was called on a publish procedure without changes on "
                  "channel value!\n");

    /* Testing react_on field on CH04 creation  */
    error = zt_chan_pub(ZT_CH04_CHANNEL, ZT_DATA_BYTES(128, 1));
    zassert_equal(error, 0, "Error executing a valid publish call!\n");
    zassert_equal(sensor_b_hit, 1, "PONG2 callback was not called with a valid call\n");
    zt_chan_pub(ZT_CH04_CHANNEL, ZT_DATA_BYTES(128, 1));
    zassert_equal(sensor_b_hit, 2,
                  "PONG2 callback was not called on a channel that react on update!\n");

    /* Testing calling multiple callbacks on CH05 */
    error = zt_chan_pub(ZT_CH05_CHANNEL, ZT_DATA_BYTES(255, 0));
    zassert_equal(error, 0, "Error executing a valid publish call! %d\n", error);
    zassert_equal(sensor_c_hit, 2,
                  "PONG or PONG2 callback was not called with a valid call\n");
    zt_chan_pub(ZT_CH05_CHANNEL, ZT_DATA_BYTES(255, 1));
    zassert_equal(
        sensor_c_hit, 4,
        "PONG or PONG2 callback was not called on a channel that react on update!\n");


    /* Testing using channal messages definitions */
    zt_data_t *mch01 =
        ZT_DATA_REQ(.id = 10, .flag = {.write = 1},
                    .data = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16});
    zt_chan_pub(ZT_MCH01_CHANNEL, mch01);
    zt_data_t *dr = ZT_DATA_REQ(0);
    zt_chan_read(ZT_MCH01_CHANNEL, dr);

    zassert_equal(dr->req.value.id, mch01->req.value.id, NULL);
    zassert_true(dr->req.value.flag.write, "Error executing reading message! Line %d\n",
                 __LINE__);
    zassert_false(dr->req.value.flag.read, "Error executing reading message! Line %d\n",
                  __LINE__);
    zassert_false(dr->req.value.flag.erase, "Error executing reading message! Line %d\n",
                  __LINE__);
    zassert_false(dr->req.value.flag.update, "Error executing reading message! Line %d\n",
                  __LINE__);
    zassert_true(0 == memcmp(dr->req.value.data, mch01->req.value.data, 32), NULL);

    zt_data_t *mch02 = ZT_DATA_RESP(.bits = 3);
    zassert_true(mch02->resp.value.result.ok, NULL);
    zassert_true(mch02->resp.value.result.fail, NULL);
    zt_chan_pub(ZT_MCH02_CHANNEL, mch02);
    mch02->resp.value.result.fail = 0;
    zt_data_t *mch02_r            = ZT_DATA_RESP(0);
    zt_chan_read(ZT_MCH02_CHANNEL, mch02_r);
    zassert_true(mch02->resp.value.result.ok, NULL);
    zassert_false(mch02->resp.value.result.fail, NULL);

    zt_data_t *mch03 = ZT_DATA_ARR(0);

    zassert_true(
        zt_chan_pub(ZT_MCH03_CHANNEL, ZT_DATA_ARR(0, 1, 2, 3, 4, 5, 6, 7, 8)) == 0,
        "Error executing reading message! Line %d, index %d\n", __LINE__);
    zassert_true(zt_chan_read(ZT_MCH03_CHANNEL, mch03) == 0,
                 "Error executing reading message! Line %d, index %d\n", __LINE__);
    ;
    zt_data_t *mch03_r = ZT_DATA_ARR(0, 1, 2, 3, 4, 5, 6, 7, 8);
    //@TODO: warning developers to see size as byte count and not items count. It can be
    // confusing.
    for (int i = 0; i < (mch03->arr.size / sizeof(u32_t)); ++i) {
        zassert_true(mch03->arr.value[i] == mch03_r->arr.value[i],
                     "Error executing reading message! Line %d, index %d -> 0x%02X\n",
                     __LINE__, i, mch03->arr.value[10]);
    }
    zassert_true(
        zt_chan_pub(ZT_MCH04_CHANNEL, ZT_DATA_UNI(.kind = {.a = 0xDC, .b = 0xFE})) == 0,
        NULL);

    zt_data_t *mch04 = ZT_DATA_UNI(0);
    zassert_true(zt_chan_read(ZT_MCH04_CHANNEL, mch04) == 0, NULL);
    zassert_true(mch04->uni.value.kind.a == 0xDC, NULL);
    zassert_true(mch04->uni.value.kind.b == 0xFE, NULL);

    zt_data_t *mch05 = ZT_DATA_FLAGS(0);

    zassert_true(zt_chan_pub(ZT_MCH05_CHANNEL,
                             ZT_DATA_FLAGS(.b0 = 0x7F, .b1 = 0x0FFFFF, .b2 = 0x1F))
                     == 0,
                 NULL);
    zassert_true(zt_chan_read(ZT_MCH05_CHANNEL, mch05) == 0, NULL);
    zassert_true(mch05->flags.value.b0 == 0x7F, NULL);
    zassert_true(mch05->flags.value.b1 == 0x0FFFFF, NULL);
    zassert_true(mch05->flags.value.b2 == 0x1F, NULL);

    zt_data_t *mch06 = ZT_DATA_COMPLEX(.data = {0});
    zassert_true(zt_chan_pub(ZT_MCH06_CHANNEL,
                             ZT_DATA_COMPLEX(.data = {1,  2,  3,  4,  5,  6,  7,  8,
                                                      9,  10, 11, 12, 13, 14, 15, 16,
                                                      17, 18, 19, 20, 21, 22, 23, 24}))
                     == 0,
                 NULL);
    zassert_true(zt_chan_read(ZT_MCH06_CHANNEL, mch06) == 0, NULL);

    zassert_true(mch06->complex.value.sample.acc.x == 0x04030201, NULL);
    zassert_true(mch06->complex.value.sample.acc.y == 0x08070605, NULL);
    zassert_true(mch06->complex.value.sample.acc.z == 0x0c0b0a09, NULL);
    zassert_true(mch06->complex.value.sample.gyro.x == 0x100f0e0d, NULL);
    zassert_true(mch06->complex.value.sample.gyro.y == 0x14131211, NULL);
    zassert_true(mch06->complex.value.sample.gyro.z == 0x18171615, NULL);

    k_sleep(K_MSEC(100));
    k_sem_give(&ztest_sem);
}


void PING_service_callback(zt_channel_e id)
{
}

void PONG2_service_callback(zt_channel_e id)
{
    if (id == ZT_CH03_CHANNEL) {
        sensor_a_hit++;
    } else if (id == ZT_CH04_CHANNEL) {
        sensor_b_hit++;
    } else if (id == ZT_CH05_CHANNEL) {
        sensor_c_hit++;
    }
}

void PONG2_task(void)
{
}

ZT_SERVICE_DECLARE(PING, PING_task, PING_service_callback);
ZT_SERVICE_DECLARE(PONG, PONG_task, PONG_service_callback);
ZT_SERVICE_DECLARE(PONG2, PONG2_task, PONG2_service_callback);
