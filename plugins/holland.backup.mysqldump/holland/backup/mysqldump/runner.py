import time
import logging
from subprocess import Popen, PIPE, list2cmdline
from holland.core import BackupError

LOG = logging.getLogger(__name__)

class ProcessError(Exception):
    pass

class ProcessQueue(object):
    def __init__(self, max=1):
        self.queue = []
        self.max = max

    def _wait_free(self):
        for proc in self.queue[:]:
            if proc.poll() is not None:
                self._handle(proc)
        time.sleep(0.5)

    def _handle(self, proc):
        self.queue.remove(proc)
        LOG.debug("removed %s from queue", proc)
        proc.wait()

    def add(self, process):
        while len(self.queue) >= self.max:
            # wait for process to die
            LOG.debug("Waiting for a free process slot")
            self._wait_free()
        LOG.debug("OK len(self.queue) = %d", len(self.queue))
        self.queue.append(process)

    def wait(self):
        # wait on all processes in the queue
        queue = self.queue
        while queue:
            pid = queue.pop()
            pid.wait()
            if pid.returncode != 0:
                self.terminate()
                raise BackupError("mysqldump exited with non-zero status: %d" %
                                  pid.returncode)

    def terminate(self):
        # termiante all queued processes
        queue = self.queue
        while queue:
            pid = queue.pop()
            os.kill(pid.pid, signal.SIGTERM)
            pid.wait()

class MySQLBackup(object):
    def __init__(self, options, open_sql_file, lock_method=None):
        self.options = options
        self.open_sql_file = open_sql_file
        self.lock_method = lock_method

    def _lock_method(self, databases):
        if self.lock_method:
            return self.lock_method
        else:
            if databases.is_transactional:
                return '--single-transaction'
            else:
                return '--lock-tables'

    def run_all(self, databases):
        options = self.options + [
            self._lock_method(databases)
        ] + [ db.name for db in databases if not db.excluded ]

        fileobj = self.open_sql_file('all_databases.sql', 'w')
        MySQLDump(options, fileobj).run()

    def run_each(self, databases, parallelism=1):
        databases = [db for db in databases if not db.excluded]
        if not databases:
            raise BackupError("No databases to backup")
        if parallelism > 1:
            databases = list(databases)
            databases.sort(lambda x,y: cmp(y.size, x.size))
        queue = ProcessQueue(parallelism)
        for database in databases:
            options = self.options[:]
            options += [
                self._lock_method(database),
                database.name
            ]
            fileobj = self.open_sql_file(database.name, 'w')
            mysqldump = MySQLDump(options, fileobj)
            queue.add(mysqldump)
            mysqldump.run_async()
        queue.wait()

class MySQLDump(object):
    def __init__(self, argv, fileobj):
        self.argv = argv
        self.fileobj = fileobj
        self.pid = None

    def _start(self):
        if self.pid:
            raise ValueError("Already started this mysqldump")
        self.pid = Popen([arg.encode('utf8') for arg in self.argv],
                         stdout=self.fileobj.fileno(),
                         stderr=PIPE,
                         close_fds=True)
        LOG.info("mysqldump(%s[%d])::", self.argv[-1], self.pid.pid)
        LOG.info("  %s", list2cmdline(self.argv))

    def run(self):
        # run and wait for a result
        self._start()
        return self.wait()


    def run_async(self):
        # fork and return immediately
        # must poll() or wait() on object
        self._start()

    def wait(self):
        LOG.debug("Waiting on %s", self)
        status = self.pid.wait()
        LOG.debug("OKAY %s finished with status %d", self, status)
        LOG.debug("closing fileobj")
        self.fileobj.close()
        LOG.debug("okay fileobj closed")
        LOG.info("* mysqldump(%s[%d]) complete", self.argv[-1], self.pid.pid)
        if status != 0:
            for line in self.pid.stderr:
                LOG.error("mysqldump(%s[%d]):: %s", self.argv[-1], self.pid.pid,
                          line.rstrip())
            raise ProcessError("mysqldump exited with non-zero status: %d" %
                               status)

    def poll(self):
        if self.pid is None:
            raise ValueError("Incorrect API utilization - no pid assigned")
        return self.pid.poll()

    #@property
    def returncode(self):
        return self.pid.returncode
    returncode = property(returncode)

    def __str__(self):
        return "MySQLDump([%d] %s)" % (self.pid.pid, list2cmdline(self.argv))
