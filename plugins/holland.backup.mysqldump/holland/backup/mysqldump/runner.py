"""Run mysqldump, Run"""

import errno
import select
import logging
from subprocess import Popen, PIPE, list2cmdline

LOG = logging.getLogger(__name__)

class ProcessError(Exception):
    """Raised after an error during process execution"""

class ProcessQueue(object):
    """Manage a queue of running processes"""

    def __init__(self, max=1):
        self.queue = {}
        self.poller = select.poll()
        self.max = max

    def wait(self):
        """Wait for at least one process to finish

        This queue uses multiplexed IO via select.poll()
        on the stdin of each subprocess to detect when a
        process is ripe for collecting.
        """
        LOG.debug("Waiting for at least one process to complete")
        while True:
            try:
                count = 0
                for fd, event in self.poller.poll():
                    LOG.debug("fd=%d seems to have completed", fd)
                    try:
                        process = self.queue.pop(fd)
                    except KeyError:
                        LOG.error("Internal error. Attempted to dequeue a fd we were not tracking: %d", fd)
                        continue
                    yield self.dequeue(process)
                    assert process.poll() is not None
                    count += 1
                if not count:
                    LOG.error("No processes dequeued")
                break
            except select.error, exc:
                # retry after EINTR
                if exc[0] == errno.EINTR:
                    LOG.debug("Resuming from EINTR")
                    continue
                raise

    def dequeue(self, proc):
        """Remove a process from the queue"""
        LOG.debug("dequeing process %r", proc)
        self.poller.unregister(proc.stdin.fileno())
        LOG.debug("unregistered fd %d", proc.stdin.fileno())
        proc.wait()
        return proc

    def add(self, process):
        """Add a new process to this queue"""
        LOG.debug("process = %r", process)
        while len(self.queue) >= self.max:
            # wait for process to die
            LOG.debug("Waiting for a free process slot")
            for child in self.wait():
                yield child
        LOG.debug("OK len(self.queue) = %d", len(self.queue))
        LOG.debug("process = %r", process)
        process.start()
        self.queue[process.stdin.fileno()] = process
        LOG.debug("registering process with fileno %d", process.stdin.fileno())
        self.poller.register(process.stdin.fileno(), select.POLLIN)
        LOG.debug("%d : %r", process.stdin.fileno(), process)

    def waitall(self):
        """Wait for all remaining processes in the queue to finish"""
        LOG.debug("Waiting for all processes")
        queue = self.queue
        while queue:
            for process in self.wait():
                LOG.debug("Yielding %r", process)
                yield process

    def terminate(self):
        """Send SIGTERM to all processes in the queue"""
        # termiante all queued processes
        queue = self.queue
        while queue:
            pid = queue.pop()
            self.poller.unregister(pid.pid)
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
            if all([db.is_transactional for db in databases]):
                return '--single-transaction'
            else:
                return '--lock-tables'

    def run_all(self, databases):
        options = self.options + [
            self._lock_method(databases),
        ]

        _databases = [db for db in databases if not db.excluded]
        if not _databases:
            raise ProcessError("No databases to backup")
        if _databases == databases:
            options.append('--all-databases')
        else:
            if len(_databases) > 1:
                options.append("--databases")
            options.extend([ db.name for db in _databases ])
        fileobj = self.open_sql_file('all_databases.sql', 'w')
        MySQLDump(options, fileobj).run()

    def run_each(self, databases, parallelism=1):
        databases = [db for db in databases if not db.excluded]
        if not databases:
            raise ProcessError("No databases to backup")
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
            for process in queue.add(mysqldump):
                if process.returncode != 0:
                    LOG.error("mysqldump[%d] exited with non-zero status",
                              process.pid)
                    LOG.info("Terminating remaining processes")
                    queue.terminate()
        for process in queue.waitall():
            LOG.info("mysqldump[%d] exited with status %d",
                     process.pid, process.returncode)

class MySQLDump(object):
    def __init__(self, argv, fileobj):
        self.argv = argv
        self.fileobj = fileobj
        self.process = None

    def start(self):
        if self.process:
            raise ValueError("Already started this mysqldump")
        self.process = Popen([arg.encode('utf8') for arg in self.argv],
                             stdin=PIPE,
                             stdout=self.fileobj.fileno(),
                             stderr=PIPE,
                             close_fds=True)
        LOG.info("mysqldump(%s[%d])::", self.argv[-1], self.process.pid)
        LOG.info("  %s", list2cmdline(self.argv))

    def run(self):
        # run and wait for a result
        self.start()
        return self.wait()

    def wait(self):
        LOG.debug("Waiting on --->%s<---", self)
        self.process.stdin.close()
        status = self.process.wait()
        LOG.debug("OKAY %s finished with status %d", self, status)
        LOG.debug("closing fileobj")
        self.fileobj.close()
        LOG.debug("okay fileobj closed")
        LOG.info("* mysqldump(%s[%d]) complete", self.argv[-1], self.process.pid)
        if status != 0:
            for line in self.process.stderr:
                LOG.error("mysqldump(%s[%d]):: %s", self.argv[-1], self.process.pid,
                          line.rstrip())
            raise ProcessError("mysqldump exited with non-zero status: %d" %
                               status)

    def poll(self):
        if self.process is None:
            raise ValueError("Incorrect API utilization - no process active")
        return self.process.poll()

    #@property
    def pid(self):
        if not self.process:
            return -1
        return self.process.pid
    pid = property(pid)

    #@property
    def returncode(self):
        return self.process.returncode
    returncode = property(returncode)

    #@property
    def stdin(self):
        return self.process.stdin
    stdin = property(stdin)

    def __repr__(self):
        return "MySQLDump([%d] %s)" % (self.pid, list2cmdline(self.argv))
