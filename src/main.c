/*
 * Copyright (c) 2012-2014 Wind River Systems, Inc.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "autoconf.h"

#ifdef CONFIG_ZTEST
#include "pdb_unit_tests.h"
#endif

#include <pdb.h>
#include <zephyr.h>

int set_special_firmware_version(pdb_property_e id, u8_t *property_value, size_t size)
{
    return 0;
}

int get_special_load(pdb_property_e id, u8_t *property_value, size_t size)
{
    return 0;
}

int check_load_value(u8_t *property_value, size_t size)
{
    return 0;
}

int core_event_callback(pdb_event_t *event)
{
    return 0;
}

#ifdef CONFIG_ZTEST
void test_main(void)
{
    ztest_test_suite(PDB_PROPERTIES_CREATION, ztest_unit_test(test_properties_name),
                     ztest_unit_test(test_properties_size), ztest_unit_test(test_properties_set),
                     ztest_unit_test(test_properties_get));

    ztest_test_suite(PDB_CORRECTNESS, ztest_unit_test(test_set));

    ztest_run_test_suite(PDB_PROPERTIES_CREATION);
    ztest_run_test_suite(PDB_CORRECTNESS);
}
#else
void main(void)
{
    int err = 0;
    printk("Hello World! %d %d\n", pdb_property_size(PDB_FIRMWARE_VERSION_PROPERTY, &err),
           PDB_LOAD_PROPERTY);
}
#endif
