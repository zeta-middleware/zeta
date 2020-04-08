/**
 * @file   pdb_threads.template.c
 * @author Lucas Peixoto <lucaspeixotoac@gmail.com>
 *
 * @brief
 *
 *
 */

#include "pdb.h"
#include "pdb_threads.h"


/* BEGIN CORE THREAD DEFINE */
K_THREAD_DEFINE(CORE_thread_id,
                512,
                CORE_task,
                NULL, NULL, NULL,
                5,
                0,
                K_NO_WAIT
                );
/* END CORE THREAD DEFINE */                

/* BEGIN HAL THREAD DEFINE */
K_THREAD_DEFINE(HAL_thread_id,
                1024,
                HAL_task,
                NULL, NULL, NULL,
                2,
                0,
                K_NO_WAIT
                );
/* END HAL THREAD DEFINE */                

/* BEGIN APP THREAD DEFINE */
K_THREAD_DEFINE(APP_thread_id,
                2048,
                APP_task,
                NULL, NULL, NULL,
                1,
                0,
                K_NO_WAIT
                );
/* END APP THREAD DEFINE */                

