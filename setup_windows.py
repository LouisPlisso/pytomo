#!/usr/bin/env python
""" Module to distribute the application with distutils

For running Pyinstaller, use:
# **From Pytomo sources directory**
find . -name '*.pyc' -delete
rm -r build

# **On Windows, from the parent of the Pytomo directory**
      *Example using Pytomo-1.9.6 source distribution*
    - to build pytomo_windows_x86.exe:
        * to create the .spec file used to build the .exe:
        > python C:\Python27\pyinstaller-1.5.1\Makespec.py --onefile \
        -p Pytomo-1.9.6\ -p Pytomo-1.9.6\pytomo -o Pytomo-1.9.6\ \
        Pytomo-1.9.6\bin\pytomo
        * modify by hand Pytomo-1.9.6\pytomo.spec to make sure the .exe is
        created directly in the root directory (due to distutils problems with
        including data files); it should look something like:
        > type Pytomo-1.9.6\pytomo.spec
        # -*- mode: python -*-
        from platform import system, machine
        a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'),
        os.path.join(HOMEPATH,'support\\useUnicode.py'), 'Pytomo-1.9.6\\bin\\pytomo'],
                     pathex=['Pytomo-1.9.6\\', 'Pytomo-1.9.6\\pytomo', 'C:\\Documents and Settings\\rqpj0589\\Desktop'])
        pyz = PYZ(a.pure)
        exe = EXE( pyz,
                  a.scripts,
                  a.binaries,
                  a.zipfiles,
                  a.datas,
                  name=''.join(('_'.join(('pytomo', system().lower(), machine())),
                        '.exe')),
                  #name=os.path.join('dist', 'pytomo.exe'),
                  debug=False,
                  strip=False,
                  upx=True,
                  console=True )'])
        * to create the executable pytomo_windows_x86.exe:
        > python C:\Python27\pyinstaller-1.5.1\Build.py Pytomo-1.9.6\pytomo.spec

    - to build pytomo_web_interface_windows_x86.exe
        * to create the .spec file used to build the .exe:
        > python C:\Python27\pyinstaller-1.5.1\Makespec.py --onefile \
        -p Pytomo-1.9.6\ -p Pytomo-1.9.6\pytomo -o Pytomo-1.9.6\ \
        Pytomo-1.9.6\bin\pytomo_web_interface
        * modify by hand Pytomo-1.9.6\pytomo.spec to make sure the .exe is
        created directly in the root directory (due to distutils problems with
        including data files); it should look something like:
        > type Pytomo-1.9.6\pytomo_web_interface.spec
        # -*- mode: python -*-
        from platform import system, machine
        a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'),
        os.path.join(HOMEPATH,'support\\useUnicode.py'), 'Pytomo-1.9.6\\bin\\pytomo_web_interface'],
             pathex=['Pytomo-1.9.6\\', 'Pytomo-1.9.6\\pytomo', 'C:\\Documents and Settings\\rqpj0589\\Desktop'])'])
        pyz = PYZ(a.pure)
        exe = EXE( pyz,
                  a.scripts,
                  a.binaries,
                  a.zipfiles,
                  a.datas,
                  name=''.join(('_'.join(('pytomo_web_interface',system().lower(),
                        machine())), '.exe')),
                  #name=os.path.join('dist', 'pytomo.exe'),
                  debug=False,
                  strip=False,
                  upx=True,
                  console=True )'])
         * to create the executable pytomo_windows_x86.exe:
        > python C:\Python27\pyinstaller-1.5.1\Build.py \
        Pytomo-1.9.6\pytomo_web_interface.spec

    - to create binary distribution:
        > cd Pytomo-1.9.6
        Pytomo-1.9.6> python setup_windows.py sdist -t MANIFEST_windows.in

# for MAC:
import sys
if sys.platform.startswith("darwin"):
    app = BUNDLE(exe,
                 name=os.path.join('dist', 'NAME.app'),
                 version=version)
"""

import distutils.core
from platform import system, machine

distutils.core.USAGE = """NO SETUP IS NEEDED TO LAUNCH THE PROGRAM.

This setup is only used to generate the source distribution:
                        './setup_windows.py sdist -t MANIFEST_windows.in'
[other setup commands are described in './setup_windows.py --help']

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

from setup import VERSION

LICENSE = 'GPLv2'

if __name__ == '__main__':
    KWARGS = {
        'name': '_'.join(('Pytomo', system().lower(), machine())),
        'version': VERSION,
        'description': 'Python tomography tool',
        'author': 'Louis Plissonneau',
        'author_email': 'louis.plissonneau@gmail.com',
        'url': 'http://code.google.com/p/pytomo',
        'data_files': [('templates', ['templates/start_template.html',
                                   'templates/end_template.html']),
                       ('images', ['images/Orange_logo.jpg']),
                       ('', ['README.txt', 'README.html', 'DESCRIPTION.txt',
                            'DESCRIPTION.html', 'pytomo.man',
                            'pytomo.exe',
                            'pytomo_web_interface.exe'])],
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


