'''
Module to test the IPC running on a computer like we do in real world
'''
import sys
from subprocess import DEVNULL, Popen, run
from time import sleep

import psutil


def kill(proc_pid):
    '''
    Funtion to kill all children of a process
    '''
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


run("echo ok && west build -b hifive1_revb".split())

with Popen(["renode", "renode_setup.resc", "--disable-xwt"],
           stdout=DEVNULL) as renode:
    sleep(4)
    with Popen(["zeta", "isc", "./zeta.yaml", "/tmp/uart", "115200"],
               stdout=DEVNULL) as zeta:
        with Popen(["python3", "sunlight_model.py"],
                   stdout=DEVNULL) as sunlight:
            with Popen(["python3", "pub_count.py"],
                       stdout=DEVNULL) as pub_count:
                sleep(6)
                sunlight.kill()
                zeta.kill()
                kill(renode.pid)
                renode.kill()
                c = pub_count.poll()
                sys.exit(c)
