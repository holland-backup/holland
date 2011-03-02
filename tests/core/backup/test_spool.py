import sys
import time
import errno
import tempfile
from itertools import izip
from nose.tools import *
from holland.core.util.path import disk_free
from holland.core.backup.spool import *

try:
    assert_true
except NameError:
    def assert_true(expr, message=''):
        if not expr:
            raise AssertionError(message)

    def assert_false(expr, message=''):
        if expr:
            raise AssertionError(message)

try:
    from itertools import tee
except ImportError:
    # less efficient implementation for py2.3
    def tee(iterable, n=2):
        it = iter(iterable)
        deques = [list() for i in range(n)]
        def gen(mydeque):
            while True:
                if not mydeque:             # when the local deque is empty
                    newval = it.next()      # fetch a new value and
                    for d in deques:        # load it to all the deques
                        d.append(newval)
                yield mydeque.pop(0)
        return tuple([gen(d) for d in deques])

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    try:
        b.next()
    except StopIteration:
        pass
    return izip(a, b)

spooldir = None

backupsets = {
        'default' : 3,
        'mysql-lvm' : 2,
}


def setup():
    global spooldir
    spooldir = tempfile.mkdtemp()
    spooldir
    _build_spool()

def _build_spool():
    spool = BackupSpool(spooldir)
    for name, numstores in backupsets.iteritems():
        for _ in xrange(numstores):
            spool.add_store(name)
            time.sleep(1.5)
        backups = spool.list_backups(name)
        bdir = os.path.dirname(backups[0].path)
        try:
            os.unlink(os.path.join(bdir, 'oldest'))
        except OSError, exc:
            if exc.errno != errno.ENOENT:
                raise
        try:
            os.unlink(os.path.join(bdir, 'newest'))
        except OSError, exc:
            if exc.errno != errno.ENOENT:
                raise

        os.symlink(backups[0].path, os.path.join(bdir, 'oldest'))
        os.symlink(backups[-1].path, os.path.join(bdir, 'newest'))

def teardown():
    shutil.rmtree(spooldir)

def test_backups():
    spool = BackupSpool(spooldir)

    for name, numstores in backupsets.iteritems():
        assert_equal(len(spool.list_backups(name)), numstores,
        "%s has only %d stores, but expected %d" %
            (name, len(spool.list_backups(name)), numstores))

def test_str_and_repr():
    spool = BackupSpool(spooldir)
    # just test that str(spool) does something sane
    ok_(isinstance(spool.__str__(), basestring))
    for name, _ in backupsets.iteritems():
        for backup in spool.list_backups(name):
            ok_(isinstance(backup, BackupStore))
            ok_(isinstance(backup.__str__(), basestring))

def test_ignore_plain_file():
    "Test that list_backups() doesn't treat a file like a backup store"
    spool = BackupSpool(spooldir)
    # just test that str(spool) does something sane
    ok_(isinstance(spool.__str__(), basestring))
    for name, _ in backupsets.iteritems():
        path = os.path.join(spooldir, name, 'foo.txt')
        open(path, 'w').close() # touch a file
        for backup in spool.list_backups(name):
            ok_(os.path.isdir(backup.path))

#XXX: what about two backups created simultaneously?
def test_backup_ordering():
    "Test each backup precedes the next"
    spool = BackupSpool(spooldir)

    for name, _ in backupsets.iteritems():
        for backupa, backupb in pairwise(spool.list_backups(name)):
            assert_true(backupa < backupb,
                        "Expected backup %s < %s but this was not the case" %
                        (backupa.path, backupb.path))

def test_relative_backup_ordering():
    "Test that each backup is a previous backup of the next"
    spool = BackupSpool(spooldir)

    for name, _ in backupsets.iteritems():
        for backupa, backupb in pairwise(spool.list_backups(name)):
            assert_equal(backupa, backupb.previous())

def test_backupstore_previous_of_first_is_none():

    spool = BackupSpool(spooldir)

    for name, _ in backupsets.iteritems():
        first_backup = spool.list_backups(name)[0]
        assert_equal(first_backup.previous(), None)

def test_backupstore_capacity():
    spool = BackupSpool(spooldir)

    for name, _ in backupsets.iteritems():
        first_backup = spool.list_backups(name)[0]
        assert_equal(first_backup.spool_capacity(),
                     disk_free(first_backup.path))
        # no spool will likely have a yottabyte free.  if so, we can simply
        # check capacity() + 1 byte :P
        assert_raises(SpoolError, first_backup.check_space, 1024**8)

def test_backupstore_latest():
    spool = BackupSpool(spooldir)

    for name, _ in backupsets.iteritems():
        first_backup = spool.list_backups(name)[0]
        last_backup = spool.list_backups(name)[-1]
        assert_equal(last_backup, first_backup.latest())

def test_backupstore_w_nullspool():
    spool = BackupSpool(spooldir)
    for name, _ in backupsets.iteritems():
        for backup in spool.list_backups(name):
            backup.spool = None
            assert_false(backup.previous())
            assert_false(backup.latest())

def test_backupsets():
    spool = BackupSpool(spooldir)
    assert_equals(len(spool.list_backupsets()), len(backupsets),
                 "Expected %d backupsts but only found %d" %
                 (len(backupsets), len(spool.list_backupsets())))

def test_backupsets_ordering():
    spool = BackupSpool(spooldir)

    for seta, setb in pairwise(spool.list_backupsets()):
        assert_true(seta < setb, "%s >= %s?" % (seta, setb))

def test_spool_iteration():
    spool = BackupSpool(spooldir)
    test_backupsets = {}
    for backup in spool:
        name = backup.name
        test_backupsets.setdefault(name, 0)
        test_backupsets[name] += 1

    assert_equals(test_backupsets, backupsets)

def test_backupset_purge():
    spool = BackupSpool(spooldir)

    name = spool.list_backupsets()[0]

    assert_true(spool.list_backups(name))
    original_backups = spool.list_backups(name)
    backups, kept, purged = spool.purge(name)
    assert_false(spool.list_backups(name))
    assert_false(kept)
    assert_equals(purged, original_backups)

def test_backupset_purge_with_retention():
    _build_spool()
    spool = BackupSpool(spooldir)

    backups = spool.list_backups('default')
    assert_true(len(backups), 3)
    backups, kept, purged = spool.purge('default', retention_count=1)
    # check that purge did not lie about kept backups
    assert_equals(len(kept), 1)
    assert_equals(kept, spool.list_backups('default'))
    assert_true(len(spool.list_backups('default')), 1)

    _build_spool()
    backups = spool.list_backups('default')
    backups, kept, purged = spool.purge('default',
                                        retention_count=len(backups) + 1)
    # purged should be empty
    assert_false(purged)
    # kept backups should be identical all backups
    assert_equals(kept, backups)
    assert_true(len(spool.list_backups('default')), len(backups))

def test_backupstore_purged():
    _build_spool()
    spool = BackupSpool(spooldir)

    backup = spool.list_backups('default')[0]
    assert_true(backup.timestamp) # should be non-zero
    backup.purge()
    assert_false(backup.timestamp) # should be zero

def test_backupstore_purged_latest_is_none():
    _build_spool()
    spool = BackupSpool(spooldir)

    backups = spool.list_backups('default')
    assert_true(backups) # we should have > 0 backups
    spool.purge('default') # now clear them out
    backup = backups[0] # take a previously deleted backup
    assert_false(backup.latest()) # this should be None
