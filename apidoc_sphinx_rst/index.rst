.. Pytomo documentation master file, created by
   sphinx-quickstart on Tue Oct 23 15:09:42 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Pytomo's documentation!
==================================

Pytomo is a Python based tomographic tool to perform analysis of video download
rates on websites that provide streaming services, like YouTube and
Dailymotion. The main purpose of the application is to offer an estimation for
the Quality of Experience the user perceives by gathering numerous statistics,
like the number of interruptions experienced or the average throughput of the
download.

We can start Pytomo either by providing an initial list of videos or by telling
it to select the most popular videos during a specific time frame. For each
video, Pytomo first retrieves the cache server where it is located, saving in a
list each redirect server it goes through to get there. Then, each cache server
is pinged to obtain the RTT times. We calculate the different statistics of the
download only on the cache server where the video is actually located.

After the first round of videos is crawled, Pytomo can retrieve their related
links and continue applying the same operations until the maximum number of
crawled videos is reached.

The more measures we get the better, so if you can advertise the use of this
crawler on top of running it, it would help us improve *your* YouTube and
Dailymotion experience.

Usage
=====

Video crawl
-----------

Linux video crawl
^^^^^^^^^^^^^^^^^
You need to have Python2.6+ installed. The current version has been tested
against Python 2.6/2.7.

user@host:~/Pytomo$ **./start_crawl.py** --help

Usage: start_crawl.py [-r max_rounds] [-u max_crawled_url] [-p max_per_url] [-P
max_per_page] [-t time_frame] [-s {youtube, dailymotion}][-n ping_packets] [-D
download_time] [-B buffering_video_duration] [-M min_playout_buffer_size] [-x]
[-L log_level] [-R] [input_urls]

Options:
  -h, --help            show this help message and exit
  -r MAX_ROUNDS         Max number of rounds to perform (default 10000)
  -l, --loop            Loop after completing the max nb of rounds
  -u MAX_CRAWLED_URL    Max number of urls to visit (default 10000)
  -p MAX_PER_URL        Max number of related urls from each page (default 20)
  -P MAX_PER_PAGE       Max number of related videos from each page (default
                        20)
  -t TIME_FRAME         Timeframe for the most popular videos to fetch at
                        start of crawl put 'today', 'week', 'month' or
                        'all_time' (default 'week')
  -s CRAWL_SERVICE      Service for the most popular videos to fetch at start
                        of crawl: select between 'youtube', or 'dailymotion'
                        (default 'youtube')
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

Windows video crawl
^^^^^^^^^^^^^^^^^^^
Double click on:
    **pytomo_windows_x86.exe**

.. note:: In case you use a proxy to connect to the internet, make sure you
    specify it in the correct format when asked:

    *Please enter the proxies you use to connect to the internet, in the format:
    {'http': 'http://proxy:8080/'}(press Enter for default None):
    (or wait 20 seconds)*

    **{'http': 'http://proxy:8080/'}**

Graphical web interface
------------------------

.. warning:: When you start the graphical interface, make sure you have already
    started a crawl following `Linux video crawl`_ or `Windows video crawl`_
    or you have a pytomo database from which to extract the data in the
    *databases* folder.

Linux graphical web interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You need to have Python2.6+ and RRDtool python binding installed (See the
`External resources`_ section for information on how to install it). The
current version has been tested against Python 2.6/2.7 and
python-rrdtool 0.2.1.

user@host:~/Pytomo$ **./start_server.py** --help

Usage: start_server.py [-v] [-f database] [-d database_directory] [port]

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

Windows graphical web interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Double click on:
    **pytomo_web_interface_windows_x86.exe**

.. note:: The graphical web interface is started, by default, on **port 5555**
    on your machine and uses information from the latest database located in the
    directory the server is started with (by default *databases*).

    You can connect on the respective machine (you need to know its IP and
    make sure it allows external connections, otherwise you will only be able
    to see the graphs locally on that machine):

        http://127.0.0.1:5555/          <= visualisation on local machine

        http://18.88.11.18:5555/        <= visualisation from remote host

    By default, the graphs are collected with information from the
    latest database in the default *databases* directory. If a new live
    crawl is started, it is recommened to stop and start again the
    graphical web interface and refresh the page from your browser.

    Furthermore, you can display graphs from other databases located in the
    directory you started the web server with. To do this, go to the link on
    the left of the page and select the desired database:
        Database_archive

    To display the graphs related to the latest database and the changes in a
    live crawl, you should select the latest database in this archive, the one
    on top of the list mentioned at the link above.

External resources
==================

We based the lib_youtube_download on `YouTube Download`_ script: we simplified
it at most and include only the classes we needed (and only YouTube video
retrieval).

The dns module is taken from the `DNS Python Package`_: we just modified rdata
so that Pyinstaller_ includes all needed modules.

The extraction of metadata out of video files is an adaptation of `Kaa Metadata
Python Package`_: it has been modified in order to be independent of Kaa-base
(thus pure Python and portable).

The web server necessary for the graphical web interface is based on `web.py`_
that is included in the Pytomo distribution sources.

The `RRDtool`_ python binding necassary for the graphical web interface should
be installed from the repository of your OS distribution:

* For Debian based OS:
    sudo apt-get install python-rrdtool
* For RHEL based OS:
    yum install python-rrdtool

External Links
^^^^^^^^^^^^^^

1. `YouTube Download`_.
2. `Kaa Metadata Python Package`_.
3. `DNS Python Package`_
4. `Pyinstaller`_
5. `RRDtool`_
6. `web.py`_

.. _YouTube Download: http://rg3.github.com/youtube-dl/
.. _Kaa Metadata Python Package:
      http://packages.debian.org/sid/python-kaa-metadata
.. _DNS Python Package: http://pypi.python.org/pypi/dnspython
.. _Pyinstaller: http://www.pyinstaller.org/
.. _RRDtool: http://oss.oetiker.ch/rrdtool/
.. _web.py: http://webpy.org/

Package contents
================

.. toctree::
   :maxdepth: 2

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

