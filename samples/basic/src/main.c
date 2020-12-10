/*
 * Copyright (c) 2012-2014 Wind River Systems, Inc.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr.h>

#include "autoconf.h"
#include "kernel.h"
#include "sys/printk.h"
#include "zeta.h"

K_SEM_DEFINE(zt_core_pend_evt, 0, 1);
K_SEM_DEFINE(zt_app_pend_evt, 0, 1);

zt_channel_e zt_core_evt_id;
zt_channel_e zt_app_evt_id;

void HAL_task(void *p1, void *p2, void *p3)
{
    zt_data_t *data = ZT_DATA_U8(1);
    while (1) {
        printk("******** sensor *******\n");
        zt_chan_pub(ZT_SENSOR_VAL_CHANNEL, data);
        k_sleep(K_SECONDS(3));
        data->u8.value = (data->u8.value + 1 <= 15) ? data->u8.value + 1 : 1;
    }
}

void CORE_task(void *p1, void *p2, void *p3)
{
    zt_data_t *data = ZT_DATA_U8(1);
    u8_t power      = 2;

    printk("******** CORE task ready *******\n");
    while (1) {
        zt_data_t *result = ZT_DATA_U16(1);
        k_sem_take(&zt_core_pend_evt, K_FOREVER);
        switch (zt_core_evt_id) {
        case ZT_SENSOR_VAL_CHANNEL:
            zt_chan_read(zt_core_evt_id, data);
            printk("[CORE_service_callback] Getting data value %02X\n", data->u8.value);
            for (u8_t i = 1; i <= data->u8.value; ++i) {
                result->u16.value = result->u16.value * power;
            }
            zt_chan_pub(ZT_POWER_VAL_CHANNEL, result);
            break;
        default:
            printk("[CORE_service_callback] receiving an unexpected id channel\n");
            break;
        }
    }
}

void APP_task(void *p1, void *p2, void *p3)
{
    zt_data_t *fv = ZT_DATA_BYTES(4, 0);
    printk("Hello APP task!\n");
    zt_chan_read(ZT_FIRMWARE_VERSION_CHANNEL, fv);
    printk("Firmware version 0x%02X%02X%02X%02X\n", fv->bytes.value[0],
           fv->bytes.value[1], fv->bytes.value[2], fv->bytes.value[3]);
    zt_data_t *data = ZT_DATA_U16(0);
    while (1) {
        k_sem_take(&zt_app_pend_evt, K_FOREVER);
        switch (zt_app_evt_id) {
        case ZT_POWER_VAL_CHANNEL:
            zt_chan_read(zt_app_evt_id, data);
            printk("[APP_service_callback] Power val is: %04X\n", data->u16.value);
            break;
        default:
            printk("[APP_service_callback] receiving an unexpected id channel\n");
        }
    }
}

void CORE_service_callback(zt_channel_e id)
{
    zt_core_evt_id = id;
    k_sem_give(&zt_core_pend_evt);
}

void HAL_service_callback(zt_channel_e id)
{
}

void APP_service_callback(zt_channel_e id)
{
    zt_app_evt_id = id;
    k_sem_give(&zt_app_pend_evt);
}

void main(void)
{
    while (1) {
        printk("******** ZETA BASIC SAMPLE! *******\n");
        k_msleep(5000);
    }
}

ZT_SERVICE_DECLARE(CORE, CORE_task, CORE_service_callback);
ZT_SERVICE_DECLARE(HAL, HAL_task, HAL_service_callback);
ZT_SERVICE_DECLARE(APP, APP_task, APP_service_callback);
