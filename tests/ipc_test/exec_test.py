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


run("west build -b hifive1_revb", shell=True)

with Popen(["renode", "renode_setup.resc", "--disable-xwt"]) as renode:
    sleep(10)
    with Popen(["zeta", "isc", "./zeta.yaml", "/tmp/uart", "115200"],
               stdout=DEVNULL) as zeta:
        with Popen(["python3", "sunlight_model.py"],
                   stdout=DEVNULL) as sunlight:
            c = run("python3 pub_count.py".split())
            sunlight.kill()
            zeta.kill()
            kill(renode.pid)
            renode.kill()
            sys.exit(c.returncode)
