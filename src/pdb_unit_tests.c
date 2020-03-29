#include "autoconf.h"
#ifdef CONFIG_ZTEST

#include "pdb_unit_tests.h"
#include "pdb.h"
#include <string.h>

int set_plus_1(pdb_property_e id, u8_t *property_value, size_t size) {
    u8_t new_value = *property_value + 1;
    pdb_property_set_private(id, &new_value, size);

    return 0;
}

int get_plus_1(pdb_property_e id, u8_t *property_value, size_t size) {
    pdb_property_get_private(id, property_value, size);
    *property_value += 1;

    return 0;
}

void test_properties_name(void) {
    pdb_property_t *p = NULL;

    p = pdb_property_get_ref(PDB_FIRMWARE_VERSION_PROPERTY);
    zassert_true(!strcmp("FIRMWARE_VERSION", p->name), "Firmware version property name is wrong: %s", p->name);

    p = pdb_property_get_ref(PDB_PERSISTENT_VAL_PROPERTY);
    zassert_true(!strcmp("PERSISTENT_VAL", p->name), "PERSISTENT_VAL property name is wrong: %s", p->name);

    p = pdb_property_get_ref(PDB_ECHO_HAL_PROPERTY);
    zassert_true(!strcmp("ECHO_HAL", p->name), "ECHO_HAL property name is wrong: %s", p->name);

    p = pdb_property_get_ref(PDB_SET_GET_PROPERTY);
    zassert_true(!strcmp("SET_GET", p->name), "SET_GET property name is wrong: %s", p->name);
}

void test_properties_set(void) {
    u32_t new_firmware_version = 0xABCDED0F;
    u8_t value = 0;
    int error = 0;
    
    error = pdb_property_set(PDB_FIRMWARE_VERSION_PROPERTY, PDB_VALUE_REF(new_firmware_version));
    zassert_equal(error, -ENODEV, "FIRMWARE_VERSION property was defined with a non null set pointer!");

    error = pdb_property_set(PDB_PERSISTENT_VAL_PROPERTY, PDB_VALUE_REF(value));
    zassert_equal(error, -EINVAL, "PERSISTENT_VAL property is allowing set a value zero to property: %d!", error);
    value = 0xF1;
    error = pdb_property_set(PDB_PERSISTENT_VAL_PROPERTY, PDB_VALUE_REF(value));
    zassert_equal(error, 0, "PERSISTENT_VAL property is not setting a valid value(%d), error: %d", value, error);    
}

void test_properties_get(void) {
    zassert_true(1, "nao foi 1");
}

void test_properties_size(void) {
    zassert_equal(4, pdb_property_get_size(PDB_FIRMWARE_VERSION_PROPERTY, NULL), "FIRMWARE_VERSION size is different of 4: %d", pdb_property_get_size(PDB_FIRMWARE_VERSION_PROPERTY, NULL));
    zassert_equal(1, pdb_property_get_size(PDB_PERSISTENT_VAL_PROPERTY, NULL), "PERSISTENT_VAL size is different of 1: %d", pdb_property_get_size(PDB_PERSISTENT_VAL_PROPERTY, NULL));
    zassert_equal(1, pdb_property_get_size(PDB_ECHO_HAL_PROPERTY, NULL), "ECHO_HAL size is different of 1: %d", pdb_property_get_size(PDB_ECHO_HAL_PROPERTY, NULL));
    zassert_equal(1, pdb_property_get_size(PDB_SET_GET_PROPERTY, NULL), "SET_GET size is different of 1: %d", pdb_property_get_size(PDB_SET_GET_PROPERTY, NULL));
}

void test_properties_validate(void) {
    
}


#endif
