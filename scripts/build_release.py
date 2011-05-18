import os, sys
from optparse import OptionParser
import shutil
import tarfile
import tempfile
import logging
import _subprocess as subprocess
from _virtualenv import create_environment
try:
    from operator import itemgetter
except ImportError:
    # fallback for python2.3
    def itemgetter(*items):
        if len(items) == 1:
            item = items[0]
            def g(obj):
                return obj[item]
        else:
            def g(obj):
                return tuple(obj[item] for item in items)
        return g


def run(shell_cmd):
    logging.info("+ %s", shell_cmd)
    subprocess.check_call(['/bin/bash', '-c', shell_cmd])

def cmd_subst(shell_cmd):
    return subprocess.Popen(shell_cmd,
                            stdout=subprocess.PIPE,
                            shell=True).communicate()[0].strip()

def holland_version():
    return cmd_subst('python setup.py --version')

class ReleaseStaging(tuple):
    __slots__ = ()

    staging_dir     = property(itemgetter(0))
    env_dir         = property(itemgetter(1))
    env_bindir      = property(itemgetter(2))
    release_dir     = property(itemgetter(3))
    doc_dir         = property(itemgetter(4))
    doc_build_dir   = property(itemgetter(5))

    def cleanup(self):
        return shutil.rmtree(self.staging_dir)

def setup(name):
    staging_dir = tempfile.mkdtemp()
    env_dir = os.path.join(staging_dir, 'virtualenv')
    env_bindir = os.path.join(env_dir, 'bin')
    release_dir = os.path.join(staging_dir, name)
    doc_dir = os.path.join(release_dir, 'docs')
    doc_build_dir = os.path.join(doc_dir, 'build')

    return ReleaseStaging([staging_dir,
                           env_dir,
                           env_bindir,
                           release_dir,
                           doc_dir,
                           doc_build_dir])

def prepare_virtualenv(env_dir):
    from _virtualenv import create_environment
    create_environment(env_dir, site_packages=False,
                       clear=True, unzip_setuptools=False,
                       use_distribute=False)
    env_bindir = os.path.join(env_dir, 'bin')
    os.environ['PATH'] = env_bindir + ':' + os.environ['PATH']
    logging.info("Installing some packages into virtualenv")
    os.environ['PIP_DOWNLOAD_CACHE'] = os.environ.get('PIP_DOWNLOAD_CACHE', os.path.expanduser('~/.pip_download_cache'))
    logging.info("Setting pip download cache to %s.",
            os.environ['PIP_DOWNLOAD_CACHE'])
    logging.info("If you do not want this set PIP_DOWNLOAD_CACHE environment variable to override.")
    run('%s/pip install --upgrade sphinx' % env_bindir)

def prepare_docs(staging):
    logging.info("Generating documentation")
    run('make -C %s/docs/ man text html' % staging.release_dir)
    for fmt in 'man', 'text', 'html':
        shutil.copytree(os.path.join(staging.doc_build_dir, fmt),
                        os.path.join(staging.doc_dir, fmt))

    run('make -C %s/docs/ clean' % staging.release_dir)

def make_release():
    name = 'holland-%s' % holland_version()
    staging = setup(name)
    try:
        prepare_virtualenv(staging.env_dir)
        logging.info("Exporting git HEAD to %s", staging.release_dir)
        run('git archive --prefix=%s/ HEAD | tar xf - -C %s' %
            (name, staging.staging_dir))
        prepare_docs(staging)
    except:
        try:
            staging.cleanup()
        except OSError, exc:
            logging.warning("Failed to cleanup staging directory: %s", exc)
            pass
        raise
    return staging

def make_tarball(dst_dir):
    staging = make_release()
    name = os.path.basename(staging.release_dir)
    archive_path = os.path.join(dst_dir, name + '.tar.gz')
    try:
        archive = tarfile.open(archive_path, mode='w:gz')
        archive.add(staging.release_dir, name)
        archive.close()
        return archive_path
    finally:
        try:
            staging.cleanup()
        except OSError, exc:
            pass

# make_release.py
def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(message)s')

    logging.info("tarball is here: %s", make_tarball(dst_dir='.'))
    logging.info("Done!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
