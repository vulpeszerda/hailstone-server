REDIS_INFO = {
    'host': 'hailstone.io',
    'password': 'qkznlqjffp'
}
# Used to filter vmnames from redis keys.
REDIS_KEY_PREFIX = 'hailstonevm:'

VM_PREFIX = 'shadyvm'
SCRIPT_ROOT = '/home/daftshady/hailstone/hailstone-vm/script/'
RUN_SCRIPT = SCRIPT_ROOT + 'startvm.sh'
RESTORE_SCRIPT = SCRIPT_ROOT + 'restore-snapshot.sh'
STOP_SCRIPT = SCRIPT_ROOT + 'stopvm.sh'
RUN_APK_SCRIPT = SCRIPT_ROOT + 'run-apk.sh'

APP_PACKAGES = [
    'com.google.android.youtube',
    'com.aol.mobile.techcrunch',
    'flipboard.app',
    'com.hoteltonight.android.prod',
    'com.airbnb.android',
    'com.rovio.angrybirds',
    'com.ketchapp.stickhero',
    'com.thefancy.app',
    'com.vimeo.android.videoapp',
    'com.etsy.android'
]
