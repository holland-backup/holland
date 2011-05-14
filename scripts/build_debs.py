import os, sys
import glob
import shutil
import tarfile
import logging
from build_release import make_release, run

def make_debs(dst_dir):
    # Make debian source tarball holland_%{version}.orig.tar.gz
    staging = make_release()
    name = os.path.basename(staging.release_dir)
    try:
        archive = tarfile.open(os.path.join(staging.staging_dir,
                                            name.replace('-', '_') +
                                            '.orig.tar.gz'),
                               mode='w:gz')
        logging.info("Creating %s from %s",
                     os.path.join(name + '.tar.gz'),
                     staging.release_dir)
        logging.info("archive.add(%s)", staging.release_dir)
        archive.add(staging.release_dir, name)
        archive.close()

        # copy contrib/debian/ to ${release_dir}/debian/
        logging.info("Setting up %s/debian/", staging.release_dir)
        shutil.copytree(os.path.join(staging.release_dir, 'contrib', 'debian'),
                        os.path.join(staging.release_dir, 'debian'))

        # update changelog
        run('cd %s && dch --local .$(date +%%Y%%m%%d%%H%%M%%S) "Local build"' %
            staging.release_dir)

        # run debuild
        logging.info("Building debian packages.")
        run("cd %s && debuild -us -uc" % (staging.release_dir))
        dst_dir = os.path.expanduser(dst_dir)
        logging.info("Copying debs to %s", dst_dir)
        for src_path in glob.glob(os.path.join(staging.staging_dir, '*.deb')):
            dst_path = os.path.join(dst_dir, os.path.basename(src_path))
            shutil.copyfile(src_path, dst_path)
	return dst_dir
    finally:
        try:
            staging.cleanup()
        except:
            pass

def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(message)s')
    logging.info("Debs can be found here: %s", make_debs(dst_dir='..'))
    return 0
if __name__ == '__main__':
    sys.exit(main())

