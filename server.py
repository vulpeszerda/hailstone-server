import re
import redis
import shlex
import tornado.process
import subprocess
import tornado.ioloop
import tornado.web
from tornado.gen import coroutine, Return
from tornado.process import Subprocess
from tornado.concurrent import Future
from tornado.gen import Task, Return, coroutine
from tornado.ioloop import IOLoop
from subprocess import call
from config import (
    REDIS_INFO, REDIS_KEY_PREFIX, VM_PREFIX, SCRIPT_ROOT,
    RUN_SCRIPT, RESTORE_SCRIPT, STOP_SCRIPT, RUN_APK_SCRIPT,
    APP_PACKAGES
)


global_redis_conn = redis.StrictRedis(**REDIS_INFO)
def set_on(vm_name):
    global_redis_conn.setex(REDIS_KEY_PREFIX + vm_name, 60, 1)


def set_off(vm_name):
    global_redis_conn.delete(REDIS_KEY_PREFIX + vm_name)


@coroutine
def call_subprocess(cmd, stdin_data=None, stdin_async=True):
    stdin = Subprocess.STREAM if stdin_async else subprocess.PIPE
    sub_process = Subprocess(shlex.split(cmd),
                             stdin=stdin,
                             stdout=Subprocess.STREAM,
                             stderr=Subprocess.STREAM,)

    if stdin_data:
        if stdin_async:
            yield Task(sub_process.stdin.write, stdin_data)
        else:
            sub_process.stdin.write(stdin_data)

    if stdin_async or stdin_data:
        sub_process.stdin.close()

    result, error = yield [Task(sub_process.stdout.read_until_close),
                           Task(sub_process.stderr.read_until_close),]

    raise Return((result, error))


class AcquireHandler(tornado.web.RequestHandler):
    @coroutine
    def get(self):
        # Fetch available vms.
        all_, e = yield call_subprocess('vboxmanage list vms')
        regex = r'\"(.*)\"'
        all_vms = [
            x for x in re.findall(regex, all_) if x.startswith(VM_PREFIX)]
        running_, e = yield call_subprocess('vboxmanage list runningvms')
        running_vms = [
            x for x in re.findall(regex, running_) if x.startswith(VM_PREFIX)]
        available_vms = list(set(all_vms) - set(running_vms))

        try:
            # Filter vrde port.
            vm_name = available_vms[0]
            info, e = yield call_subprocess(
                'vboxmanage showvminfo ' + vm_name)
            port = re.findall(
                r'VRDE property: TCP/Ports.*\"([0-9]*)\"', info)[0]
        except IndexError:
            self.set_status(400)
            self.write('There is no available vm')
            self.finish()
            return

        set_on(vm_name)
        self.write(vm_name + ',' + port)
        vm_idx = vm_name.replace(VM_PREFIX, '')

        snapshots = [
            'bd6d4b04-f05d-4efa-ba93-b6e314c4755b',
            '5997d88b-2c17-467b-a5be-e3f3c08c3519',
            '6cfc6323-9d26-410c-85b1-192f99c26500'
        ]

        result, e = yield call_subprocess(
            RESTORE_SCRIPT + ' ' + vm_idx + ' ' + snapshots[int(vm_idx)])

        # NOTE that this prcoess will not be flushed automatically.
        # Should fix it to prevent potential memory leak.
        call([RUN_SCRIPT, vm_idx])
        self.finish()


class ReleaseHandler(tornado.web.RequestHandler):
    @coroutine
    def get(self):
        # Stop vm.
        vm_name = self.get_argument('name')
        regex = r'\"(.*)\"'
        running_, e = yield call_subprocess('vboxmanage list runningvms')
        running_vms = [
            x for x in re.findall(regex, running_) if x.startswith(VM_PREFIX)]
        if vm_name not in running_vms:
            self.set_status(400)
            self.write('%s is not running' % vm_name)
            return

        result, e = yield call_subprocess(
            STOP_SCRIPT + ' ' + vm_name.replace(VM_PREFIX, ''))

        set_off(vm_name)
        self.write('VM %s is stopped successfully' % vm_name)
        self.finish()


class PingHandler(tornado.web.RequestHandler):
    @coroutine
    def get(self):
        set_on(self.get_argument('name'))
        self.write('success')


class ExecuteHandler(tornado.web.RequestHandler):
    @coroutine
    def get(self):
        vm_name = self.get_argument('name')
        app_idx = self.get_argument('idx')
        try:
            cmd = RUN_APK_SCRIPT + ' ' + \
                vm_name.replace(VM_PREFIX, '') + ' ' + APP_PACKAGES[int(app_idx)]
        except (IndexError, ValueError):
            self.set_status(400)
            self.write('Invalid access')
            return

        result, e = yield call_subprocess(cmd)

        self.write('App has been executed')
        self.finish()


if __name__ == "__main__":
    application = tornado.web.Application([
        (r'/vm/acquire/?', AcquireHandler),
        (r'/vm/release/?', ReleaseHandler),
        (r'/vm/execute/?', ExecuteHandler),
        (r'/vm/ping/?', PingHandler)
    ])
    application.listen(3800)
    tornado.ioloop.IOLoop.instance().start()
