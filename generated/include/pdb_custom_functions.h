/**
 * @file   pdb_custom_functions.template.h
 * @author Lucas Peixoto <lucaspeixotoac@gmail.com>
 *
 * @brief
 *
 *
 */

#ifndef PDB_CUSTOM_FUNCTIONS_TEMPLATE_H_
#define PDB_CUSTOM_FUNCTIONS_TEMPLATE_H_

#include "pdb.h"


/* BEGIN FIRMWARE_VERSION CHANNEL FUNCTIONS */

/* END FIRMWARE_VERSION CHANNEL FUNCTIONS */

/* BEGIN PERSISTENT_VAL CHANNEL FUNCTIONS */

int pdb_validator_different_of_zero(u8_t *data, size_t size);

/* END PERSISTENT_VAL CHANNEL FUNCTIONS */

/* BEGIN ECHO_HAL CHANNEL FUNCTIONS */

/* END ECHO_HAL CHANNEL FUNCTIONS */

/* BEGIN SET_GET CHANNEL FUNCTIONS */

int get_plus_1(pdb_channel_e id);

/* END SET_GET CHANNEL FUNCTIONS */


#endif
