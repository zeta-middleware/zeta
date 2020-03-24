/*
 * Copyright (c) 2012-2014 Wind River Systems, Inc.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr.h>
#include <misc/printk.h>
#include <pdb.h>

int set_special_firmware_version(pdb_property_e id, u8_t *property_value, size_t size) {
    return 0;
}

int get_special_load(pdb_property_e id, u8_t *property_value, size_t size) {
    return 0;
}

int check_load_value(u8_t *property_value, size_t size) {
    return 0;
}

int core_event_callback(pdb_event_t *event) {
    return 0;
}

int main(void)
{
    int err = 0;
    printk("Hello World! %d %d\n", pdb_property_get_size(PDB_FIRMWARE_VERSION_PROPERTY, &err), PDB_LOAD_PROPERTY);
    return 0;
}
