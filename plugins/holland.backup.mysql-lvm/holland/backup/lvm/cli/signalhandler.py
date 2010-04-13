"""Signal Handling module"""
import signal

def _sig_by_name(num):
    for name in dir(signal):
        if name.startswith('SIG') and not name.startswith('SIG_'):
            if num == getattr(signal, name):
                return name
    return num

def handle(signum, frame):
    logging.info("Received signal %s(%d)", _sig_by_name(signum), signum)   

def _setup_signals(callback=handle):
    signal.signal(signal.SIGINT, handle)
    signal.signal(signal.SIGHUP, handle)
    signal.signal(signal.SIGTERM, handle)
