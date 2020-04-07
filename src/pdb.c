#include "pdb.h"

#include <fs/nvs.h>
#include <string.h>
#include <zephyr.h>

/* #TODO: Remover código legado da estratégia dos includes */
#include "devicetree_fixups.h"
#include "pdb_callbacks.h"
#include "pdb_observers.h"
#include "pdb_validators.h"

int pdb_thread(void);

#define NVS_SECTOR_SIZE DT_FLASH_ERASE_BLOCK_SIZE  // 4096
#define NVS_SECTOR_COUNT 4
#define NVS_STORAGE_OFFSET DT_FLASH_AREA_STORAGE_OFFSET

static struct nvs_fs pdb_fs = {
    .sector_size  = NVS_SECTOR_SIZE,
    .sector_count = NVS_SECTOR_COUNT,
    .offset       = NVS_STORAGE_OFFSET,
};

K_SEM_DEFINE(pdb_property_sema, 1, 1);

K_THREAD_DEFINE(pdb_thread_id, PDB_THREAD_SIZE, pdb_thread, NULL, NULL, NULL, PDB_THREAD_PRIORITY,
                0, K_NO_WAIT);


/* #define PDB_PROPERTIES_INITIAL_VALUE(_name, _size, ...) \ */
/*     u8_t _name##_initial_value[_size] = {__VA_ARGS__}; */

/* #include "pdb_properties_initial_value.def" */


/* Defining PDB_PROPERTY_CREATE for properties generating */
/* #define PDB_PROPERTY_CREATE(_name, _bytes, _validate, _get, _set, _in_flash, _observers, _id,
 * ...) \ */
/*     {.name      = (const char *) #_name, \ */
/*      .validate  = _validate, \ */
/*      .get       = _get, \ */
/*      .set       = _set, \ */
/*      .size      = sizeof(u8_t) * _bytes, \ */
/*      .in_flash  = _in_flash, \ */
/*      .changed   = 0, \ */
/*      .observers = _observers, \ */
/*      .id        = PDB_##_name##_PROPERTY}, */

static pdb_property_t __pdb_properties[PDB_PROPERTY_COUNT] = {
    /* #include "pdb_properties.def" */
};

static pdb_property_t *pdb_property_get_ref(pdb_property_e id)
{
    if (id < PDB_PROPERTY_COUNT) {
        return &__pdb_properties[id];
    } else {
        return NULL;
    }
}

size_t pdb_property_size(pdb_property_e id, int *error)
{
    size_t size       = 0;
    pdb_property_t *p = pdb_property_get_ref(id);
    if (p) {
        size = (size_t) p->size;
    } else {
        if (error) {
            *error = -EINVAL;
        }
    }
    return size;
}

int pdb_property_get(pdb_property_e id, u8_t *property_value, size_t size)
{
    int error                = 0;
    pdb_property_t *property = pdb_property_get_ref(id);
    if (property && property->get) {
        error = property->get(id, property_value, size);
        if (error) {
            printk("Current property get: %d, error code: %d\n", id, error);
        }
    } else {
        printk("The property #%d does not have a get implementation.\n", id);
    }
    return error;
}

int pdb_property_get_private(pdb_property_e id, u8_t *property_value, size_t size)
{
    int ret = 0;
    if (id < PDB_PROPERTY_COUNT) {
        pdb_property_t *current_property = &__pdb_properties[id];
        if (current_property->size == size) {
            if (k_sem_take(&pdb_property_sema, K_MSEC(200))) {
                printk("Could not get the property. Property is busy\n");
                ret = -EBUSY;
            } else {
                memcpy(property_value, current_property->data, current_property->size);
                k_sem_give(&pdb_property_sema);
            }
        } else {
            ret = -EINVAL;
        }
    } else {
        ret = -ENODATA;
    }
    return ret;
}

int pdb_property_set(pdb_property_e id, u8_t *property_value, size_t size)
{
    /* #TODO: Adicionar pre-set e pos-set */
    int error                = 0;
    int valid                = 1;
    pdb_property_t *property = pdb_property_get_ref(id);

    PDB_ASSERT_VAL(property, NULL, -ENODEV, "The property %d was not found!\n", id);
    PDB_ASSERT_VAL(property->set, NULL, -EPERM, "The property %d is read only!\n", id);
    if (property->validate) {
        valid = property->validate(property_value, size);
    }
    PDB_ASSERT(valid, -EINVAL, "The value doesn't satisfy valid function of property %d!\n", id);
    PDB_ASSERT(property->pre_set(), -EINVAL, "Error on pre_set function of property %d!\n", id);
    error = property->set(id, property_value, size);
    if (error) {
        printk("Current property set: %d, error code: %d!\n", id, error);
    }
    PDB_ASSERT(property->pos_set(), -EINVAL, "Error on pre_set function of property %d!\n", id);
    return error;
}

int pdb_property_set_private(pdb_property_e id, u8_t *property_value, size_t size)
{
    int ret = 0;
    if (id < PDB_PROPERTY_COUNT) {
        pdb_property_t *current_property = &__pdb_properties[id];
        if (current_property->size == size) {
            if (k_sem_take(&pdb_property_sema, K_MSEC(200))) {
                printk("Could not set the property. Property is busy\n");
                ret = -EBUSY;
            } else {
                if (memcmp(current_property->data, property_value, size)) {
                    memcpy(current_property->data, property_value, current_property->size);
                    if (current_property->changed < 255) {
                        current_property->changed++;
                    }
                    k_sem_give(&pdb_property_sema);
                } else {
                    k_sem_give(&pdb_property_sema);
                }
            }
        } else {
            ret = -EINVAL;
        }
    } else {
        ret = -ENODATA;
    }
    return ret;
}

static void __pdb_recover_data_from_flash(void)
{
    int rc = 0;
    printk("Start...\n");
    if (k_sem_take(&pdb_property_sema, K_SECONDS(5)) != 0) {
        printk("Could not set the property. Property is busy\n");
    } else {
        for (u16_t id = 0; id < PDB_PROPERTY_COUNT; ++id) {
            if (__pdb_properties[id].in_flash) {
                rc = nvs_read(&pdb_fs, id, __pdb_properties[id].data, __pdb_properties[id].size);
                if (rc > 0) { /* item was found, show it */
                    printk("Id: %d, value:", id);
                    for (size_t i = 0; i < __pdb_properties[id].size; i++) {
                        printk(" %02X", __pdb_properties[id].data[i]);
                    }
                    printk("|");
                    for (size_t i = 0; i < __pdb_properties[id].size; i++) {
                        if (32 <= __pdb_properties[id].data[i]
                            && __pdb_properties[id].data[i] <= 126) {
                            printk("%c", __pdb_properties[id].data[i]);
                        } else {
                            printk(".");
                        }
                    }
                    printk("\n");
                } else { /* item was not found, add it */
                    printk("No values found for property #%d\n", id);
                }
            }
        }
        k_sem_give(&pdb_property_sema);
    }
}

static void __pdb_persist_data_on_flash(void)
{
    int bytes_written = 0;
    for (u16_t id = 0; id < PDB_PROPERTY_COUNT; ++id) {
        if (__pdb_properties[id].in_flash) {
            if (__pdb_properties[id].changed) {
                // printk("Store changes for property: %d", id);
                bytes_written =
                    nvs_write(&pdb_fs, id, __pdb_properties[id].data, __pdb_properties[id].size);
                if (bytes_written > 0) { /* item was found and updated*/
                    __pdb_properties[id].changed = 0;
                    printk("Property #%d value updated on the flash\n", id);
                } else if (bytes_written == 0) {
                    // printk("Property #%d value is already on the flash.", id);
                } else { /* item was not found, add it */
                    printk("Property #%d could not be stored\n", id);
                }
            }
        } else {
            __pdb_properties[id].changed = 0;
        }
    }
}

/* #define PDB_PROPERTIES_INITIAL_VALUE(_name, _size, ...) \ */
/*     __pdb_properties[PDB_##_name##_PROPERTY].data = _name##_initial_value; */

/* #define PDB_PROPERTY_CREATE(_name, _bytes, _validate, _get, _set, _in_flash, _observers, _id,
 * ...) \ */
/* struct k_msgq *_name##_event_queues[]           = {__VA_ARGS__, NULL};                         \
 */
/* __pdb_properties[PDB_##_name##_PROPERTY].queues = (struct k_msgq **) _name##_event_queues; */

int pdb_thread(void)
{
    /* #include "pdb_properties.def" */
    /* #include "pdb_properties_initial_value.def" */
    /* #TODO: Alterar o funcionamento da thread do pdb */
    int error = nvs_init(&pdb_fs, DT_FLASH_DEV_NAME);
    if (error) {
        printk("Flash Init failed\n");
    } else {
        printk("NVS started...[OK]\n");
    }
    __pdb_recover_data_from_flash();

    while (1) {
        k_sleep(K_SECONDS(10));
        __pdb_persist_data_on_flash();
    }
    return 0;
}

const char *pdb_property_name(pdb_property_e id)
{
    pdb_property_t *p = pdb_property_get_ref(id);

    if (p) {
        return p->name;
    }

    return (const char *) p;
}
