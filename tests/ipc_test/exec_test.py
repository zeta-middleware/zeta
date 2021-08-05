import sys
from subprocess import DEVNULL, Popen
from time import sleep

import psutil


def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


renode = Popen(["renode", "renode_setup.resc", "--disable-xwt"],
               stdout=DEVNULL)
sleep(4)
zeta = Popen(["zeta", "isc", "./zeta.yaml", "/tmp/uart", "115200"],
             stdout=DEVNULL)
sunlight = Popen(["python3", "sunlight_model.py"], stdout=DEVNULL)
pub_count = Popen(["python3", "pub_count.py"], stdout=DEVNULL)
sleep(6)
sunlight.kill()
zeta.kill()
kill(renode.pid)
renode.kill()
c = pub_count.poll()
sys.exit(c)
