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
/* u8_t count_data_read        = 0; */
/* u8_t running_urgent_routine = 0; */
/* k_tid_t read_data_last_thread; */
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

    /* Calculating power_val variable */
    /* u16_t power_val = 1; */
    /* u8_t power      = 2; */
    /* for (u8_t i = 1; i <= data; ++i) { */
    /*     power_val *= power; */
    /* } */

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
    zt_chan_read(ZT_CH03_CHANNEL, ch03);
    zassert_equal(ch03->u64.value, 0xff, "Error old value is wrong: %x", ch03->u64.value);
    zassert_equal(error, 0, "Error executing a valid publish call!\n");
    zassert_equal(sensor_a_hit, 1,
                  "PONG2 callback was not called with a valid call(value different from "
                  "existent) %d\n",
                  sensor_a_hit);
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

ZT_SERVICE_INIT(PING, PING_task, PING_service_callback);
ZT_SERVICE_INIT(PONG, PONG_task, PONG_service_callback);
ZT_SERVICE_INIT(PONG2, PONG2_task, PONG2_service_callback);
