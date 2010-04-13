import os
import sys
import stat
import select
import time
from holland.core.util.path import format_bytes

def format_time(seconds, precision=2):
  units = [
    (('week', 'weeks'), 604800),
    (('day', 'days'), 86400),
    (('hour', 'hours'), 3600),
    (('minute', 'minutes'), 60),
    (('second', 'seconds'), 1)
  ]
  result = []
  for names, value in units:
    n, seconds = divmod(seconds, value)
    if n > 0:
      result.append('%d %s' % (n, names[n > 1]))
  return ', '.join(result)

def terminal_width():
    """Return estimated terminal width."""
    width = 0
    try:
        import struct, fcntl, termios
        s = struct.pack('HHHH', 0, 0, 0, 0)
        x = fcntl.ioctl(1, termios.TIOCGWINSZ, s)
        width = struct.unpack('HHHH', x)[1]
    except IOError:
        pass
    if width <= 0:
        try:
            width = int(os.environ['COLUMNS'])
        except:
            pass
    if width <= 0:
        width = 80

    return width

class Plumber(object):
    BLOCKSZ = 1024*1024  # 1M buffer size?
    def __init__(self, istream, ostream, timeout=1.0,callback=None):
        self.istream = istream.fileno()
        st = os.fstat(self.istream)
        if stat.S_ISREG(st.st_mode):
            self.size = st.st_size
        else:
            self.size = -1
        self.ostream = ostream.fileno()
        # track partial writes
        self.buffer = ''
        # flag when we're done
        self.ieof = False # istream is empty
        self.oeof = False # ostream is closed
        self.timeout = timeout
        self.callback = callback
        self.input_bytes = 0
        self.output_bytes = 0

    def read(self, rd, wr):
        nbytes = self.BLOCKSZ - len(self.buffer)
        if nbytes < 0:
            nbytes = 0
        if not nbytes or self.ieof:
            # buffer is full
            # clear the list
            del rd[:]
            return self.buffer
        data = os.read(self.istream, nbytes)
        # we don't check for !data, since we assume the istream will be flagged (it isn't currently)
        if data:
            self.buffer += data
            self.input_bytes += len(data)
        else:
            self.ieof = True

        if self.buffer:
            if self.ostream not in wr:
                wr.append(self.ostream)
        return self.buffer

    # This assumes it's only called when we can write at least one byte to self.ostream
    # self.buffer should be non-empty
    def write(self, rd, wr):
        if not self.buffer and self.ieof:
            # empty buffer, istream is closed - never going to have further data
            # anything we had was alreayd written
            self.oeof = True
            return 0
        try:
            n = os.write(self.ostream, self.buffer)
            if n > 0: # wrote something
                # lets read in some more data
                if not self.ieof:
                    rd.append(self.istream)
                self.output_bytes += n
                self.buffer = self.buffer[n:]
                return n
            return 0
        except Exception, e:
            n = 0
            self.oeof = True

        return n

    def run(self):
        # create poll object
        # testing python2.4 on os x, doesn't seem to support poll.  select works just as well I guess
        #poller = select.poll()
        #poller.register(self.ostream, select.POLLOUT)

        # initially start out waiting for data to come in
        rd_wait = [self.istream]
        wr_wait = []
        while True:
            #events = poller.poll(self.timeout)
            rd_ev, wr_ev, x_ev = select.select(rd_wait, wr_wait, [], self.timeout)
            if rd_ev:
                self.read(rd_wait, wr_wait)
            if wr_ev:
                n = self.write(rd_wait, wr_wait)
                if self.callback:
                    self.callback(n)
            if not rd_ev and not wr_ev:
                # timeout
                self.callback(0)

            if self.oeof:
                break
        if self.callback:
            # Force a final noop update
            self.callback(0, force=True)


class ProgressMonitor(object):
    def __init__(self, max):
        self.max = max > 0 and max or 1
        self.current = 0
        self.rate = 0
        self.last_update = 0
        self.bytes = 0
        self.frequency = 0.5

    def __call__(self, n, force=False):
        self.current += n
        now = time.time()
        if force or not self.last_update \
            or (now - self.last_update) >= self.frequency:
            r = float(self.current) / self.max
            bytes_remaining = self.max - self.current
            if self.last_update and self.last_update != now:
                rate = (self.current - self.bytes) / (now - self.last_update)
            else:
                rate = None
            width = terminal_width()
            estimated_time = rate and float(bytes_remaining) / rate
            print >>sys.stderr, " "*(width - 2), "\r",
            print >>sys.stderr, "\t(%.2f%%) (%s of %s) (%s per second) (%s remaining)\r" % \
                (
                    #'='*int(r*5) + '>',
                    r*100,
                    format_bytes(self.current),
                    format_bytes(self.max),
                    rate and format_bytes(rate) or 'unknown',
                    rate and format_time(estimated_time) or 'unknown'
                ),
            self.last_update = now
            self.bytes = self.current

