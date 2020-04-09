/**
 * @file   pdb_threads.template.h
 * @author Lucas Peixoto <lucaspeixotoac@gmail.com>
 *
 *
 *
 */


#ifndef PDB_THREADS_H_
#define PDB_THREADS_H_

#include "pdb.h"


/* BEGIN CORE SECTION */
void CORE_task(void);
extern const k_tid_t CORE_thread_id;
#define CORE_TASK_PRIORITY 5
#define CORE_STACK_SIZE 512
/* END CORE SECTION */

/* BEGIN HAL SECTION */
void HAL_task(void);
extern const k_tid_t HAL_thread_id;
#define HAL_TASK_PRIORITY 2
#define HAL_STACK_SIZE 1024
/* END HAL SECTION */

/* BEGIN APP SECTION */
void APP_task(void);
extern const k_tid_t APP_thread_id;
#define APP_TASK_PRIORITY 1
#define APP_STACK_SIZE 2048
/* END APP SECTION */



#endif
