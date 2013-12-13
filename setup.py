#!/usr/bin/env python
"""Module to distribute the code with distutils

For running Pyinstaller, use:
# **From Pytomo sources directory**
find . -name '*.pyc' -delete
rm -r build
# **From Pyinstaller repository**
python2.5 Makespec.py --onefile \
    -p ~/streaming/pytomo/Pytomo/ -p ~/streaming/pytomo/Pytomo/pytomo/ \
    -o ~/streaming/pytomo/Pytomo/ \
    ~/streaming/pytomo/Pytomo/bin/pytomo
# Check differences
diff  ~/streaming/pytomo/Pytomo/pytomo_named.spec \
        ~/streaming/pytomo/Pytomo/pytomo.spec
# Run with automatic naming of exe
python2.5 Build.py ~/streaming/pytomo/Pytomo/pytomo_named.spec

# for MAC:
import sys
if sys.platform.startswith("darwin"):
    app = BUNDLE(exe,
                 name=os.path.join('dist', 'NAME.app'),
                 version=version)
"""

import distutils.core

distutils.core.USAGE = """NO SETUP IS NEEDED TO LAUNCH THE PROGRAM.

This setup is only used to generate the source distribution: './setup.py sdist'
[other setup commands are described in './setup.py --help']

Use './start_crawl.py' to start the crawl.
You can check the options with 'start_crawl.py -h'.
You can configure options in the command line of start_crawl.py or in the
pytomo/config_pytomo.py file.


The graphical interface requires extrenal dependencies (see README for more
information on how to install them):
    - rrdtool (http://oss.oetiker.ch/rrdtool/download.en.html) - used
    'python-rrdtool' version 1.4.3-1 for Debian GNU/Linux 6.0;
    - webpy (http://webpy.org/download) - used 'web.py-0.37' source distribution
    for linux or 'python-webpy' 1:0.34-2 for Debian GNU/Linux 6.0.
Use './start_server.py PORT_NR' to start the graphical web server that displays
the plots on the desired PORT_NR.
You can check the options with './start_server.py -h'.
Do not change the RRD_PLOT_DIR, RRD_DIR in pytomo/config_pytomo.py.
"""

VERSION = '3.0.5'

LICENSE = 'GPLv2'

if __name__ == '__main__':
    KWARGS = {
        'name': 'Pytomo',
        'version': VERSION,
        'description': 'Python tomography tool',
        'author': 'Louis Plissonneau',
        'author_email': 'louis.plissonneau@gmail.com',
        'url': 'http://code.google.com/p/pytomo',
        'packages': ['pytomo','pytomo/dns', 'pytomo/dns/rdtypes',
                     'pytomo/dns/rdtypes/ANY', 'pytomo/dns/rdtypes/IN',
                     'pytomo/kaa_metadata', 'pytomo/kaa_metadata/audio',
                     'pytomo/kaa_metadata/image', 'pytomo/kaa_metadata/video',
                     'pytomo/kaa_metadata/misc', 'pytomo/flvlib',
                     'pytomo/flvlib/scripts', 'pytomo/rrdtool_win_x86_DLLs',
                     'pytomo/web', 'pytomo/web/contrib',
                     'pytomo/web/wsgiserver', 'pytomo/fpdf'],
        'scripts': ['bin/pytomo', 'start_crawl.py',
                    'bin/pytomo_web_interface', 'start_server.py'],
        'long_description': open('README.txt').read(),
        'platforms': ['Linux', 'Windows', 'Mac'],
        'license': LICENSE,
        'classifiers': ['Development Status :: 4 - Beta',
                        'Environment :: Console',
                        'Intended Audience :: Science/Research',
                        'Operating System :: OS Independent',
                        'Operating System :: POSIX',
                        'Operating System :: Microsoft',
                        'Operating System :: MacOS :: MacOS X',
                        'Programming Language :: Python :: 2',
                        'Topic :: Internet',
                       ],
    }
    distutils.core.setup(**KWARGS)


