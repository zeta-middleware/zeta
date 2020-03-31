#include "autoconf.h"
#ifdef CONFIG_ZTEST

#include <string.h>

#include "pdb.h"
#include "pdb_unit_tests.h"

int set_plus_1(pdb_property_e id, u8_t *property_value, size_t size)
{
    u8_t new_value = *property_value + 1;
    pdb_property_set_private(id, &new_value, size);

    return 0;
}

int get_plus_1(pdb_property_e id, u8_t *property_value, size_t size)
{
    pdb_property_get_private(id, property_value, size);
    *property_value = *property_value + 1;

    return 0;
}

void test_properties_name(void)
{
    zassert_true(!strcmp("FIRMWARE_VERSION", pdb_property_name(PDB_FIRMWARE_VERSION_PROPERTY)),
                 "Firmware version property name is wrong: %s",
                 pdb_property_name(PDB_FIRMWARE_VERSION_PROPERTY));

    zassert_true(!strcmp("PERSISTENT_VAL", pdb_property_name(PDB_PERSISTENT_VAL_PROPERTY)),
                 "PERSISTENT_VAL property name is wrong: %s",
                 pdb_property_name(PDB_PERSISTENT_VAL_PROPERTY));

    zassert_true(!strcmp("ECHO_HAL", pdb_property_name(PDB_ECHO_HAL_PROPERTY)),
                 "ECHO_HAL property name is wrong: %s", pdb_property_name(PDB_ECHO_HAL_PROPERTY));

    zassert_true(!strcmp("SET_GET", pdb_property_name(PDB_SET_GET_PROPERTY)),
                 "SET_GET property name is wrong: %s", pdb_property_name(PDB_SET_GET_PROPERTY));
}

void test_properties_set(void)
{
    u32_t new_firmware_version = 0xABCDED0F;
    u8_t value                 = 0;
    int error                  = 0;

    /* Testing if set functions was correct assigned */
    error = pdb_property_set(PDB_FIRMWARE_VERSION_PROPERTY, PDB_VALUE_REF(new_firmware_version));
    zassert_equal(error, -ENODEV,
                  "FIRMWARE_VERSION property was defined with a non null set pointer!");

    error = pdb_property_set(PDB_PERSISTENT_VAL_PROPERTY, PDB_VALUE_REF(value));
    zassert_equal(error, -EINVAL,
                  "PERSISTENT_VAL property is allowing set a value zero to property: %d!", error);
    value = 0xF1;
    error = pdb_property_set(PDB_PERSISTENT_VAL_PROPERTY, PDB_VALUE_REF(value));
    zassert_equal(error, 0, "PERSISTENT_VAL property is not setting a valid value(%X), error: %d",
                  value, error);

    error = pdb_property_set(PDB_SET_GET_PROPERTY, PDB_VALUE_REF(value));
    zassert_equal(error, 0, "SET_GET property is not setting a valid value(%X), error: %d", value,
                  error);
    error = pdb_property_set(PDB_ECHO_HAL_PROPERTY, PDB_VALUE_REF(value));
    zassert_equal(error, 0, "ECHO_HAL property is not setting a valid value(%X), error: %d", value,
                  error);
}

void test_properties_get(void)
{
    u8_t firmware_version[4] = {0};
    u8_t value               = 0;
    int error                = 0;

    error =
        pdb_property_get(PDB_FIRMWARE_VERSION_PROPERTY, firmware_version, sizeof(firmware_version));
    zassert_false(error,
                  "PDB is not allowing get value from property FIRMWARE_VERSION, error code: %d!",
                  error);
    zassert_equal(0xF1, firmware_version[0],
                  "FIRMWARE_VERSION property must to has 0xF1 as the value of the first byte, "
                  "value found %02X!",
                  firmware_version[0]);
    zassert_equal(0xF2, firmware_version[1],
                  "FIRMWARE_VERSION property must to has 0xF2 as the value of the second byte, "
                  "value found %02X!",
                  firmware_version[1]);
    zassert_equal(0xF3, firmware_version[2],
                  "FIRMWARE_VERSION property must to has 0xF3 as the value of the third byte, "
                  "value found %02X!",
                  firmware_version[2]);
    zassert_equal(0xF4, firmware_version[3],
                  "FIRMWARE_VERSION property must to has 0xF4 as the value of the fourth byte, "
                  "value found %02X!",
                  firmware_version[3]);

    error = pdb_property_get(PDB_PERSISTENT_VAL_PROPERTY, PDB_VALUE_REF(value));
    zassert_equal(0xF1, value,
                  "PERSISTENT_VAL property must to has 0xF1 as the value, value found %02X!",
                  value);

    error = pdb_property_get(PDB_SET_GET_PROPERTY, PDB_VALUE_REF(value));
    zassert_equal(0xF3, value, "SET_GET property must to has 0xF3 as the value, value found %02X!",
                  value);
}

void test_properties_size(void)
{
    zassert_equal(4, pdb_property_size(PDB_FIRMWARE_VERSION_PROPERTY, NULL),
                  "FIRMWARE_VERSION size is different of 4: %d",
                  pdb_property_size(PDB_FIRMWARE_VERSION_PROPERTY, NULL));
    zassert_equal(1, pdb_property_size(PDB_PERSISTENT_VAL_PROPERTY, NULL),
                  "PERSISTENT_VAL size is different of 1: %d",
                  pdb_property_size(PDB_PERSISTENT_VAL_PROPERTY, NULL));
    zassert_equal(1, pdb_property_size(PDB_ECHO_HAL_PROPERTY, NULL),
                  "ECHO_HAL size is different of 1: %d",
                  pdb_property_size(PDB_ECHO_HAL_PROPERTY, NULL));
    zassert_equal(1, pdb_property_size(PDB_SET_GET_PROPERTY, NULL),
                  "SET_GET size is different of 1: %d",
                  pdb_property_size(PDB_SET_GET_PROPERTY, NULL));
}

void test_set(void)
{
    u8_t value = 0x44;

    /* Testing pdb_property_set correctness  */
    zassert_true(pdb_property_set(PDB_PROPERTY_COUNT, PDB_VALUE_REF(value)),
                 "PDB is allowing set a value to an invalid property!");

    zassert_true(pdb_property_set(PDB_ECHO_HAL_PROPERTY, &value, sizeof(value) + 1),
                 "PDB is allowing set a value with wrong size!");
}


#endif
