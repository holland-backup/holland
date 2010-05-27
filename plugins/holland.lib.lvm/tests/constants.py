import tempfile

LOOP_DEV = '/dev/loop0'
IMG_FILE = '/tmp/hl_lvm.img'
IMG_SIZE = 128*1024**2
TEST_VG = 'holland'
TEST_LV = 'test_lv'
MNT_DIR = tempfile.mkdtemp()
