#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
'''Simple python server to display an index page and static objects.
    .. note:: External module included: webpy (http://webpy.org/)
    .. moduleauthor:: Ana Oprea

Usage:
    >>> # call the class from top level
    >>> start_server.py
'''

from __future__ import with_statement, absolute_import, print_function
from optparse import OptionParser
import sys
import os
import logging
import time
from itertools import chain
# webpy
try:
    from . import web
except (ValueError, ImportError):
    import web
# config file
try:
    from . import config_pytomo
except (ValueError):
    import config_pytomo
# rrd library to interact with
try:
    from .lib_rrdtools import PytomoRRD, create_options
except (ValueError):
    from lib_rrdtools import PytomoRRD, create_options
# database connection
try:
    from .lib_database import PytomoDatabase
except (ValueError):
    from lib_database import PytomoDatabase
from sqlite3 import Error
# file operations
try:
    from .lib_io import ALL_PLOTS, ALL_KEY, LINKS_KEY, MAIN_KEY, DB_KEY, \
    DB_EXTENSION, get_latest_specific_file, write_index, \
    check_templates_exist, index_filename
except (ValueError):
    from lib_io import ALL_PLOTS, ALL_KEY, LINKS_KEY, MAIN_KEY, DB_KEY, \
    DB_EXTENSION, get_latest_specific_file, write_index, \
    check_templates_exist, index_filename
# to check if files/dirs exist and set name
try:
    from .start_pytomo import check_out_files, configure_log_file
except ValueError:
    from start_pytomo import check_out_files, configure_log_file

# port range to run the server
MIN_PORT = 1024
MAX_PORT = 65535
# refresh time in seconds to reload the main page
REFRESH_TIME = 90
# first line in the html to be displayed in the browser
START_RENDERING = 1
# global directory where the databases are stored (can be changed if the user
# requests a specific one in cli)
DB_DIR = config_pytomo.DATABASE_DIR
#DATABASE = config_pytomo.DATABASE
DATABASE = get_latest_specific_file(DB_DIR, DB_EXTENSION)
# rrd needs minimum 3 points to plot graphs
RRD_MIN_NR_POINTS = 3

if not config_pytomo.LOG:
    configure_log_file('http_server')

# the main page (index)
# static objects found under folders below in the current dir
# each element is treated by its respective class
URLS = (
    '/(js|css|%s|%s)/(.*)' % (config_pytomo.IMAGE_DIR,
                              config_pytomo.RRD_PLOT_DIR), 'Static',
    '/(%s)/(.*)' % (config_pytomo.PDF_DIR), 'Pdf',
    '/%s(.*)' % config_pytomo.DOC_DIR, 'Doc',
    '/(.*)', 'Index'
    )

class Index:
    ''' Class that serves the main page.
    Will search for a .html file under the folder set in render below.
    '''
    def __init__(self):
        # search for the main page that will be displayed in the templates dir
        self.render = web.template.render(config_pytomo.TEMPLATES_DIR,
                                          cache=False)

    def GET(self, parameter):
        '''Retrieves the main page from the parameter_timestamp_index.html
        template, based on the selected database as parameter.
        '''
        # verify if the user has already specified a certain database on which
        # to display the plots, otherwise choose the latest database
        # database is a parameter in the link
        # example: http://127.0.0.1:5555/Database_archive?db=databases/large.db
        # has as 'db' parameter the database 'databases/large.db'
        try:
            #global DATABASE
            #DATABASE = web.input().db
            database = web.input().db
        except AttributeError:
            config_pytomo.LOG.debug('Could not get a database specified by the'
                                    ' user')
            database = DATABASE
        config_pytomo.LOG.debug('Database: %s' % database)
        try:
            db_nr_rows = PytomoDatabase(database).count_rows()
        except Error, mes:
            db_nr_rows = RRD_MIN_NR_POINTS - 1
            config_pytomo.LOG.error('Unable to extract data with error: %s'
                                               % mes)
        # if database is has less than 3 points no graphs will be created
        # (rrd limitation)
        if db_nr_rows < RRD_MIN_NR_POINTS:
            config_pytomo.LOG.warning('Database %s does not have enough points'
                                      ' to create graphs' % database)
            timestamp = None
            write_index(timestamp, database, DB_DIR)
        else:
            try:
                timestamp = PytomoDatabase(database).fetch_start_time()
            except Error, mes:
                timestamp = None
                config_pytomo.LOG.error('Unable to extract data with error:'
                                        '%s' % mes)
            latest_db = get_latest_specific_file(DB_DIR, DB_EXTENSION)
            # check if:
            # the modification time of the db has changed in the REFRESH_TIME s
            # or if template files don't exist
            # or if there is a new database that is not in the db archive list
            if (((time.time() - os.path.getmtime(database)) < REFRESH_TIME)
                    or not check_templates_exist(timestamp)
                    or (os.path.getmtime(index_filename(DB_KEY, timestamp))
                        < os.path.getmtime(latest_db))):
                config_pytomo.LOG.debug('RRD operations start...')
                pytomo_rrd = PytomoRRD(database)
                pytomo_rrd.update_pytomo_rrd()
                #pytomo_rrd.fetch_pytomo_rrd()
                pytomo_rrd.plot_pytomo_rrd()
                config_pytomo.LOG.debug('RRD operations end...')
                write_index(timestamp, database, DB_DIR)
        config_pytomo.LOG.debug('Start rendering page...')
        # these headers allow browsers to display the page
        web.header('Content-type','text/html')
        web.header('Transfer-Encoding','chunked')
        # if the user provides a legitimate link, it will be displayed
        # otherwise the main graphs will be displayed
        # parameter is taken from the link, for example:
        # http://127.0.0.1:5555/PlaybackDuration
        # has as parameter PlaybackDuration
        # on the main page (no parameter) the main plots are displayed
        if (parameter in chain(ALL_PLOTS[ALL_KEY], ALL_PLOTS.keys(),
                               [LINKS_KEY, DB_KEY])):
            template_file = index_filename(parameter, timestamp)
        else:
            template_file = index_filename(MAIN_KEY, timestamp)
        try:
            f_index = open(template_file, 'r')
        except IOError:
            config_pytomo.LOG.error('Template file %s does not exist!' %
                                    template_file)
        config_pytomo.LOG.debug('Template file is open: %s' % template_file)
        # skip the first line that allows to process the parameter given by the
        # link
        for line in f_index.readlines()[START_RENDERING:]:
            yield line
        f_index.close()
        config_pytomo.LOG.debug('End rendering page...')

class Static:
    ''' Class that serves the static objects of the main page.
    Will search for elements under the directories mentioned in urls related to
    this class.
    '''
    def __init__(self):
        self.object_path = None

    def GET(self, media, filename):
        '''Retrieves the static objects located in the main page.'''
        try:
            self.object_path = open(media + '/' + filename, 'rb')
        except IOError, mes:
            config_pytomo.LOG.exception(mes)
            config_pytomo.LOG.error('File, %s, does not exist.' % filename)
        yield self.object_path.read()

class Doc:
    ''' Class that serves the documentation pages.
    '''
    def __init__(self):
        self.object_path = None

    def GET(self, filename):
        '''Retrieves the documentation files.'''
        try:
            self.object_path = open(config_pytomo.DOC_DIR + filename, 'rb')
        except IOError, mes:
            config_pytomo.LOG.exception(mes)
            config_pytomo.LOG.error('File, %s, does not exist.' % filename)
            return
        yield self.object_path.read()

class Pdf:
    ''' Class that serves the PDF reports.
    Will search for elements under the directories mentioned in urls related to
    this class.
    '''
    def __init__(self):
        self.object_path = None

    def GET(self, media, filename):
        '''Retrieves the static objects located in the main page.'''
        # these headers allow browsers to display the page
        web.header('Content-type','application/octet-stream')
        try:
            self.object_path = open(media + '/' + filename, 'rb')
        except IOError, mes:
            config_pytomo.LOG.exception(mes)
            config_pytomo.LOG.error('File, %s, does not exist.' % filename)
        yield self.object_path.read()

def configure_logger_web():
    'Configure log file and indicate succes or failure'
    print('Configuring log file')
    config_pytomo.LOG = logging.getLogger('pytomo_webpage')
    timestamp = time.strftime("%Y-%m-%d.%H_%M_%S")
    if config_pytomo.LOG_FILE == '-':
        handler = logging.StreamHandler(sys.stdout)
        print('Logs are on standard output')
        log_file = True
    else:
        try:
            log_file = check_out_files(config_pytomo.LOG_FILE,
                                       config_pytomo.LOG_DIR, timestamp)
        except IOError:
            print('Problem opening file with timestamp: %s' % timestamp)
            return None
        print('Graphical web interface logs are there: %s' % log_file)
        # for lib_youtube_download
        handler = logging.FileHandler(filename=log_file)
    log_formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - '
                                      '%(levelname)s - %(message)s')
    handler.setFormatter(log_formatter)
    config_pytomo.LOG.addHandler(handler)
    config_pytomo.LOG.setLevel(config_pytomo.LOG_LEVEL)
    config_pytomo.LOG.critical('Log level set to %s',
                           config_pytomo.LEVEL_TO_NAME[config_pytomo.LOG_LEVEL])
    # to not have console output
    config_pytomo.LOG.propagate = False
    # log all config file values except built in values
    for value in filter(lambda x: not x.startswith('__'),
                        config_pytomo.__dict__):
        config_pytomo.LOG.critical('%s: %s'
                                   % (value, getattr(config_pytomo, value)))

def main(argv=None):
    'Program wrapper'
    if argv is None:
        argv = sys.argv[1:]
    usage = '%prog [-v] [-f database] [-d database_directory] [port]'
    parser = OptionParser(usage=usage)
    create_options(parser)
    (options, args) = parser.parse_args(argv)
    # Intialize the logger for standalone testing Logging
    if not config_pytomo.LOG:
        configure_logger_web()
    if options.verbose:
        config_pytomo.LOG.setLevel(logging.DEBUG)
    # set port for web server
    port = None
    if len(args) == 0:
        # add default port
        port = int(config_pytomo.WEB_DEFAULT_PORT)
    elif len(args) == 1:
        # set port
        try:
            port = int(args[0])
        except ValueError, mes:
            config_pytomo.LOG.exception(mes)
            parser.error('You must specify an integer in the range [%d,%d]'
                % (MIN_PORT, MAX_PORT))
        if (port < MIN_PORT or port > MAX_PORT):
            parser.error('Port %d is not in the range [%d,%d])' %
                         (port, MIN_PORT, MAX_PORT))
    else:
        parser.error('Only the port on which to run the application should be '
                'specified, in the range [%d,%d]' % (MIN_PORT, MAX_PORT))
    # if a directory is specified, the latest database there is selected
    if options.db_dir_name:
        global DB_DIR
        DB_DIR = options.db_dir_name
    global DATABASE
    # if database is specified
    if options.db_name:
        DATABASE = options.db_name
    else:
        # last database in directory is selected
        DATABASE = get_latest_specific_file(DB_DIR, DB_EXTENSION)
    if not DATABASE:
        print('Please start a crawl first, in order to have a database to '
              'extract data from!\n Use:\n For Linux: ./start_crawl.py\n '
              'For Windows: pytomo_windows_x86.exe\n')
        return 1
    config_pytomo.LOG.debug('Initial database: %s' % DATABASE)
    # hack due to the  fact that web.application.__init__() expects the
    # globals() dictionary as second parameter, so application would only
    # work with port number as option (no -v or anything else)
    app = web.application(URLS, {'Static': Static, 'Pdf': Pdf, 'Doc': Doc,
                                 'Index': Index}, autoreload=True)
    # parameter is taken from the link, for example:
    # http://127.0.0.1:5555/PlaybackDuration
    # has as parameter PlaybackDuration
    # on the main page (no parameter) the main plots are displayed
    config_pytomo.LOG.debug('Launching server on port %d' % port)
    # hack due to line 54 in /usr/lib/pymodules/python2.6/web/wsgi.py
    # return httpserver.runsimple(func, validip(listget(sys.argv, 1, '')))
    if len(sys.argv) == 0 or len(sys.argv) == 1:
        sys.argv.append(str(port))
    else:
        sys.argv[1] = str(port)
    try:
        print('Launching server on port %d' % port)
        print('Type Ctrl-C to stop server.')
        app.run()
    except IOError:
        parser.error('Address already in use, start the application with '
                'another port number in the range [%d,%d])'
                % (MIN_PORT,MAX_PORT))
    except KeyboardInterrupt:
        print('\nServer stopped by user')
        config_pytomo.LOG.critical('Server stopped by user')
        return 1
    return 0

# for running with gunicorn as: gunicorn  pytomo.webpage:wsgi_app
wsgi_app = web.application(URLS, {'Static': Static, 'Pdf': Pdf, 'Doc': Doc,
                             'Index': Index}, autoreload=True).wsgifunc()
if __name__ == '__main__':
    import doctest
    doctest.testmod()
    sys.exit(main())
