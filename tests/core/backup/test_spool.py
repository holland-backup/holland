import sys
import time
import tempfile
from itertools import tee, izip
from nose.tools import *
from holland.core.backup.spool import *

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

spooldir = None

backupsets = {
        'default' : 3,
        'mysql-lvm' : 2,
}


def setup():
    global spooldir
    spooldir = tempfile.mkdtemp()
    print >>sys.stderr, "Created temporary spool path for testing %s" % \
    spooldir
    _build_spool()

def _build_spool():
    spool = BackupSpool(spooldir)
    for name, numstores in backupsets.iteritems():
        for _ in xrange(numstores):
            spool.add_store(name)
            time.sleep(1)

def teardown():
    shutil.rmtree(spooldir)
    print >>sys.stderr, "Removed temporary spool path %s on cleanup" % spooldir

def test_backups():
    spool = BackupSpool(spooldir)

    for name, numstores in backupsets.iteritems():
        assert_equal(len(spool.list_backups(name)), numstores,
        "%s has only %d stores, but expected %d" %
            (name, len(spool.list_backups(name)), numstores))

def test_backup_ordering():
    spool = BackupSpool(spooldir)

    for name, _ in backupsets.iteritems():
        for backupa, backupb in pairwise(spool.list_backups(name)):
            assert_true(backupa < backupb,
                        "Expected backup %s < %s but this was not the case" %
                        (backupa.path, backupb.path))

def test_backup_ordering_internal():
    spool = BackupSpool(spooldir)

    for name, _ in backupsets.iteritems():
        for backupa, backupb in pairwise(spool.list_backups(name)):
            assert_equal(backupa, backupb.previous())

def test_backupstore_previous_of_first_is_none():

    spool = BackupSpool(spooldir)

    for name, _ in backupsets.iteritems():
        first_backup = spool.list_backups(name)[0]
        assert_equal(first_backup.previous(), None)

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
    spool.purge_backupset(name)
    assert_false(spool.list_backups(name))

def test_backupset_purge_with_retention():
    _build_spool()
    spool = BackupSpool(spooldir)

    backups = spool.list_backups('default')
    assert_true(len(backups), 3)
    spool.purge_backupset('default', retention_count=1)
    assert_true(len(spool.list_backups('default')), 1)

    _build_spool()
    backups = spool.list_backups('default')
    spool.purge_backupset('default', retention_count=len(backups) + 1)
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
    spool.purge_backupset('default') # now clear them out
    backup = backups[0] # take a previously deleted backup
    assert_false(backup.latest()) # this should be None
