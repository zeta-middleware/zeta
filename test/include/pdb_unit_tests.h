#ifndef PDB_UNIT_TESTES_H_
#define PDB_UNIT_TESTES_H_
#include "autoconf.h"
#ifdef CONFIG_ZTEST

#include <ztest.h>

void test_properties_name(void);
void test_properties_set(void);
void test_properties_get(void);
void test_properties_size(void);
void test_properties_validate(void);
void test_set(void);


#endif
#endif
