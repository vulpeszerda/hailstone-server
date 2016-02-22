import re
import os
import time
import redis
import shlex
import subprocess
from config import REDIS_INFO, VM_PREFIX, REDIS_KEY_PREFIX, STOP_SCRIPT

redis_conn = redis.StrictRedis(**REDIS_INFO)
DEVNULL = open(os.devnull, 'wb')
while True:
    all_ = subprocess.Popen(
        shlex.split('vboxmanage list vms'), stdout=subprocess.PIPE).communicate()[0]
    all_vms = [
        x for x in re.findall(r'\"(.*)\"', all_) if x.startswith(VM_PREFIX)]

    for vm_name in all_vms:
        state = redis_conn.get(REDIS_KEY_PREFIX + vm_name)
        if not state:
            # Stop it.
            subprocess.Popen(
                shlex.split(STOP_SCRIPT + ' ' + vm_name.replace(VM_PREFIX, '')),
                stderr=DEVNULL)

    time.sleep(90)
