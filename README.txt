======
PYTOMO
======

Pytomo is a YouTube crawler designed to figure out network information out of
YouTube video download.


Usage
-----

- Video crawl:
start_crawl.py [-r max_rounds] [-u max_crawled_url] [-p max_per_url] [-P
max_per_page] [-t time_frame] [-n ping_packets] [-D download_time] [-B
buffering_video_duration] [-M min_playout_buffer_size] [-x] [-L log_level] [-R]
[input_urls]
Options:
  -h, --help            show this help message and exit
  -r MAX_ROUNDS         Max number of rounds to perform (default 10000)
  -l, --loop            Loop after completing the max nb of rounds
  -u MAX_CRAWLED_URL    Max number of urls to visit (default 5000000)
  -p MAX_PER_URL        Max number of related urls from each page (default 20)
  -P MAX_PER_PAGE       Max number of related videos from each page (default
                        20)
  -t TIME_FRAME         Timeframe for the most popular videos to fetch at
                        start of crawl put 'today', 'week', 'month' or
                        'all_time' (default 'week')
  -n PING_PACKETS       Number of packets to be sent for each ping (default
                        10)
  -D DOWNLOAD_TIME      Download time for the video in seconds (default
                        30.000000)
  -B INITIAL_PLAYBACK_DURATION 
                        Buffering video duration in seconds (default
                        2000.000000)
  -M MIN_PLAYOUT_BUFFER_SIZE
                        Minimum Playout Buffer Size in seconds (default
                        0.100000)
  -x                    Do NOT store public IP address of the machine in the
                        logs
  -L LOG_LEVEL          The log level setting for the Logging module.Choose
                        from: 'DEBUG', 'INFO', 'WARNING', 'ERROR' and
                        'CRITICAL' (default 'DEBUG')
  --http-proxy=PROXIES  in case of http proxy to reach Internet (default None)
  --provider=PROVIDER   Indicate the ISP
  -R, --no-related      Do NOT crawl related videos (stays with the first urls
                        found: either most popular or arguments given)

- Graphical web interface to display graphs about the crawled data:
start_server.py [-v] [-f database] [-d database_directory] port
Options:
  -h, --help            show this help message and exit
  -v, --verbose         run as verbose mode
  -f DB_NAME, --file=DB_NAME
                        run on a specific database (by default the latest
                        database in the default database directory is
                        selected)
  -d DB_DIR_NAME, --dir=DB_DIR_NAME
                        run on a specific directory where the latest database
                        will be selected


Installation-free
-----------------
In order to provide installation-free package, we provide binary executables
for Linux (32 and 64bits), Windows, and Mac OS X.
The binaries files were generated with Pyinstaller_ (version 1.5RC1).

If you have Python installed, you can directly run the 'start_crawl.py' script at
root or the pytomo script in bin directory.

If you have Python installed and the RRDtool and webpy python bindings, you can
directly run the 'start_server.py' script at root - you need to specify a port
on which to start the server and then connect to that port on the respective
host from your favourite browser. For example, you start the graphical web
interface on port 5555:
    $ ./start_server.py 5555
You will then connect on the respective machine (you need to know its IP and
make sure it allows external connections, otherwise you will only be able to
see the graphs locally on that machine):
    http://127.0.0.1:5555/          <= visualisation on local machine
    http://10.193.224.73:5555/      <= visualisation from remote host
By default, the graphs are collected with information from the latest database
in the default database directory. If a new live crawl is started, it is
recommened to stop and start again the graphical web interface and refresh the
page from your browser.


External Resources
------------------

We based the lib_youtube_download on `YouTube Download`_ script: we simplified
it at most and include only the classes we needed (and only YouTube video
retrieval).

The dns module is taken from the `DNS Python Package`_: we just modified rdata
so that Pyinstaller_ include all needed modules.

The extraction of metadata out of video files is an adaptation of `Kaa Metadata
Python Package`_: it has been modified in order to be independent of Kaa-base
(thus pure Python and portable).

The graphical web interface requires the following external resources, that we
recommend you to install from the repository of your OS distribution:
a) RRDtool python binding
- For Debian based OS:
    sudo apt-get install python-rrdtool
- For RHEL based OS:
    yum install python-rrdtool
b) webpy
- For Debian based OS:
    sudo apt-get install python-webpy
- For RHEL based OS:
    yum install python-webpy


External Links
~~~~~~~~~~~~~~

1. `YouTube Download`_.
2. `Kaa Metadata Python Package`_.
3. `DNS Python Package`_
4. Pyinstaller_
5. RRDtool_
6. web.py_

.. _YouTube Download: http://rg3.github.com/youtube-dl/
.. _Kaa Metadata Python Package: http://packages.debian.org/sid/python-kaa-metadata
.. _DNS Python Package: http://pypi.python.org/pypi/dnspython
.. _Pyinstaller: http://www.pyinstaller.org/
.._RRDtool: http://oss.oetiker.ch/rrdtool/
.._web.py: http://webpy.org/
