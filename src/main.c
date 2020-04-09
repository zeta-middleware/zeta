/*
 * Copyright (c) 2012-2014 Wind River Systems, Inc.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr.h>

#include "autoconf.h"
#include "pdb.h"
#include "pdb_threads.h"

int pdb_validator_different_of_zero(u8_t *data, size_t size)
{
    return 1;
}

void HAL_task(void)
{
    u8_t data = 1;
    while (1) {
        pdb_channel_set(PDB_SENSOR_VAL_CHANNEL, (u8_t *) &data, sizeof(data));
        k_sleep(K_SECONDS(3));
        data = (data + 1 <= 10) ? data + 1 : 1;
    }
}

void CORE_task(void)
{
}

void APP_task(void)
{
    u8_t fv[4] = {0};
    printk("Hello APP task!\n");
    pdb_channel_get(PDB_FIRMWARE_VERSION_CHANNEL, fv, sizeof(fv));
    printk("Firmware version 0x%02X%02X%02X%02X\n", fv[0], fv[1], fv[2], fv[3]);
    while (1) {
        k_sleep(K_SECONDS(1));
    }
}

void CORE_service_callback(pdb_channel_e id)
{
    u8_t data    = 0;
    u8_t power   = 2;
    u16_t result = 1;
    switch (id) {
    case PDB_SENSOR_VAL_CHANNEL:
        pdb_channel_get(id, (u8_t *) &data, sizeof(data));
        printk("[CORE_service_callback] Getting data value %02X\n", data);
        for (u8_t i = 1; i <= data; ++i) {
            result *= power;
        }
        pdb_channel_set(PDB_POWER_VAL_CHANNEL, (u8_t *) &result, sizeof(result));
        break;
    default:
        printk("[CORE_service_callback] receiving an unexpected id channel\n");
        break;
    }
}

void HAL_service_callback(pdb_channel_e id)
{
}

void APP_service_callback(pdb_channel_e id)
{
    u16_t data;
    switch (id) {
    case PDB_POWER_VAL_CHANNEL:
        pdb_channel_get(id, (u8_t *) &data, sizeof(data));
        printk("[APP_service_callback] Power val is: %04X\n", data);
        break;
    default:
        printk("[APP_service_callback] receiving an unexpected id channel\n");
    }
}

void main(void)
{
    printk("******** PDB test! *******\n");
}
