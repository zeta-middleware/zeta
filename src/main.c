/*
 * Copyright (c) 2012-2014 Wind River Systems, Inc.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr.h>
#include <misc/printk.h>
#include <pdb.h>

int main(void)
{
    int err = 0;
    printk("Hello World! %d %d\n", pdb_property_get_size(PDB_FIRMWARE_VERSION_PROPERTY, &err), PDB_LOAD_PROPERTY);
    return 0;
}
