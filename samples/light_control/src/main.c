/**
 * @file main.c
 * @brief Main thread is just an execution countdown in this sample.
 * @author Rodrigo Peixoto
 * @version 0.1
 * @date 2020-04-28
 */

#include <sys/printk.h>
#include <zephyr.h>
#include "kernel.h"
#include "zeta.h"

extern void posix_exit(int error);

/**
 * @brief The main thread stops the execution after 120 seconds of operation.
 */
void main(void)
{
    while (1) {
        printk("Started the main thread running on a %s board.\n", CONFIG_BOARD);
        k_msleep(5000);
    }
}
