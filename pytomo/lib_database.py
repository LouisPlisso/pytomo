#!/usr/bin/env python
''' Module for sqllite interface to the pytomo database
    Usage (to be run interactively above the pytomo directory):

       import pytomo.start_pytomo as start_pytomo
       start_pytomo.configure_log_file('doc_test')
       import pytomo.lib_database as lib_database
       import time
       import datetime
       timestamp = time.strftime("%Y-%m-%d.%H_%M_%S")
       # to make sure a new file is created for every run.
       db_name = 'doc_test' + str(timestamp) + '.db'
       doc_db = lib_database.PytomoDatabase(db_name)
       doc_db.create_pytomo_table('doc_test_table')
       doc_db.describe_tables()
       row = (datetime.datetime(2011, 5, 6, 15, 30, 50, 103775),
            'Youtube', 'http://www.youtube.com/watch?v=RcmKbTR--iA',
            'http://v15.lscache3.c.youtube.com',
            '173.194.20.56','default_10.193.225.12', None, None, None,
            8.9944229125976562, 'mp4', 225, 115012833.0, 511168.14666666667,
            9575411, 0, 1024, 100, 0.99954795837402344, 7.9875903129577637,
            40, 11.722306421319782, 1192528.8804511931,
            'http://www.youtube.com/fake_redirect')
       doc_db.insert_record(row)
       doc_db.fetch_all()
       doc_db.fetch_all_parameters(['DownloadTime', 'PingMin', 'PingMax'])

       >>> import time
       >>> timestamp = time.strftime("%Y-%m-%d.%H_%M_%S")
       >>> # to make sure a new file is created for every run we use
       >>> # timestamp.
       >>> db_name = 'doc_test_lib_db' + str(timestamp) + '.db'
       >>> # import pytomo.lib_database as lib_database
       >>> doc_db = PytomoDatabase(db_name)
       >>> doc_db.create_pytomo_table('doc_test_table')
       >>> doc_db.describe_tables() #doctest: +NORMALIZE_WHITESPACE
       (u'CREATE TABLE doc_test_table(ID TIMESTAMP,\\n
           Service text,\\n                       Url text,\\n
           CacheUrl text,\\n                       IP text,\\n
           Resolver text,\\n                       PingMin real,\\n
           PingAvg real,\\n                       PingMax real,\\n
           DownloadTime real,\\n                       VideoType text,\\n
           VideoDuration real,\\n                       VideoLength real,\\n
           EncodingRate real,\\n                       DownloadBytes int,\\n
           DownloadInterruptions int,\\n                       InitialData
           real,\\n                       InitialRate real,\\n
           InitialPlaybackBuffer real,\\n
           BufferingDuration real,\\n                       PlaybackDuration
           real,\\n                       BufferDurationAtEnd real,\\n
           MaxInstantThp real,\\n                       RedirectUrl text\\n
           )',)
       >>> import datetime
       >>> record = (datetime.datetime(2011, 5, 6, 15, 30, 50, 103775),
       ... 'Youtube', 'http://www.youtube.com/watch?v=RcmKbTR--iA',
       ... 'http://v15.lscache3.c.youtube.com',
       ... '173.194.20.56','default_10.193.225.12', None, None, None,
       ... 8.9944229125976562, 'mp4', 225, 115012833.0, 511168.14666666667,
       ... 9575411, 0, 1024 ,100,  0.99954795837402344, 7.9875903129577637,
       ... 35, 11.722306421319782, 1192528.8804511931, None)
       >>> doc_db.insert_record(record)
       >>> record = (datetime.datetime(2011, 5, 6, 15, 40, 50, 103775),
       ... 'Youtube', 'http://www.youtube.com/watch?v=RcmKbTR--iA',
       ... 'http://v15.lscache3.c.youtube.com',
       ... '173.194.20.56','default_10.193.225.12', None, None, None,
       ... 8.9944229125976562, 'mp4', 225, 115012833.0, 511168.14666666667,
       ... 9575411, 0, 1024, 100, 0.99954795837402344, 7.9875903129577637,
       ... 40, 11.722306421319782, 1192528.8804511931,
       ... 'http://www.youtube.com/fake_redirect')
       >>> doc_db.insert_record(record)
       >>> doc_db.fetch_all() #doctest: +NORMALIZE_WHITESPACE
       (u'2011-05-06 15:30:50.103775',
        u'Youtube',
        u'http://www.youtube.com/watch?v=RcmKbTR--iA',
        u'http://v15.lscache3.c.youtube.com',
        u'173.194.20.56',
        u'default_10.193.225.12',
        None,
        None,
        None,
        8.9944229125976562,
        u'mp4',
        225.0,
        115012833.0,
        511168.14666666667,
        9575411,
        0,
        1024.0,
        100.0,
        0.99954795837402344,
        7.9875903129577637,
        35.0,
        11.722306421319782,
        1192528.8804511931,
        None)
       (u'2011-05-06 15:40:50.103775',
        u'Youtube',
        u'http://www.youtube.com/watch?v=RcmKbTR--iA',
        u'http://v15.lscache3.c.youtube.com',
        u'173.194.20.56',
        u'default_10.193.225.12',
        None,
        None,
        None,
        8.9944229125976562,
        u'mp4',
        225.0,
        115012833.0,
        511168.14666666667,
        9575411,
        0,
        1024.0,
        100.0,
        0.99954795837402344,
        7.9875903129577637,
        40.0,
        11.722306421319782,
        1192528.8804511931,
        u'http://www.youtube.com/fake_redirect')
       >>> doc_db.fetch_single_parameter('DownloadTime')
       ... #doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        [(u'2011-05-06 15:30:50.103775', 8.9944229125976562),
        (u'2011-05-06 15:40:50.103775', 8.9944229125976562)]
        >>> doc_db.fetch_all_parameters(['DownloadTime', 'PingMin', 'PingMax'])
        ... #doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        [(8.9944229125976562, None, None, u'2011-05-06 15:30:50.103775'),
        (8.9944229125976562, None, None, u'2011-05-06 15:40:50.103775')]
        >>> doc_db.fetch_start_time()
        1304688650
        >>> from os import unlink
        >>> unlink(db_name)
'''

from __future__ import with_statement, absolute_import, print_function
import sqlite3
from pprint import pprint
import operator

# only for logging
import logging
import sys
import time
import os

# config file
try:
    from . import config_pytomo
except ValueError:
    import config_pytomo

class PytomoDatabase:
    ''' Pytomo database class
        The columns of the file pytomo_table are as follows:
        TID     - A timestamped ID generated by for each record entered
        Service - The website on which the analysis is performed
                  Example: Youtube, Dailymotion
        Url     - The url of the webpage
        CacheUrl- The Url of the cache server hosting the video
        CacheServerDelay- the delay to obtain the cache server url (from the
                    initial web page)
        IP      - The IP address of the cache server from which the video is
                  downloaded
        Resolver- The DNS resolver used to get obtain the IP address of the
                  cache server prefixed with ISP given (if any)
                  Example Google DNS, Local DNS
        ResolveTime- The time to get an answer from DNS
        AS      - The AS as resolved by RIPE
        PingMin - The minimum recorded ping time to the resolved IP address of
                  the cache server
        PingAvg - The average recorded ping time to the resolved IP address of
                  the cache server
        PingMax - The maximum recorded ping time to the resolved IP address of
                  the cache server
        DownloadTime - The Time taken to download the video sample
                       (We do not download the entire video but only for a
                       limited download time)
        VideoDuration - The actual duration of the complete video
        VideoLength - The length (in bytes) of the complete video
        EncodingRate - The encoding rate of the video: VideoLength/VideoDuration
        DownloadBytes - The length of the video sample (in bytes)
        DownloadInterruptions -  Nb of interruptions experienced during the
                                 download
        InitialData - Number of bytes downloaded in the initial buffering
                      period,
        InitialRate - The mean data rate (in kbps) during the initial
                      buffering period,
        BufferingDuration -  Accumulate time spend in buffering state
        PlaybackDuration - Accumulate time spend in playing state
        BufferDurationAtEnd - The buffer length at the end of download
        TimeTogetFirstByte - Time to get first byte
        MaxInstantThp - The max instantaneous throughput of the download
        RedirectUrl - The Redirection Url in case of an HTTP redirect
        StatusCode - HTTP Return Code
    '''

    _table_name = None
    created = None

    def __init__(self, database_file=config_pytomo.DATABASE_TIMESTAMP):
        '''Initialize the database object'''
        # Intialize the logger for standalone testing Logging
        if not config_pytomo.LOG:
            self.logger_db()
        try:
            # isolation_level in order to auto-commit
            self.py_conn = sqlite3.connect(database_file, isolation_level=None)
        except sqlite3.Error, mes:
            config_pytomo.LOG.exception(''.join((
                'Unable to connect to the database: ', database_file,
                '\nError message: ', str(mes))))
            self.created = False
            return
        config_pytomo.LOG.info(' '.join(("Created connection to data base",
                                "Database:", os.path.basename(database_file))))
        self.created = True
        self.py_cursor = self.py_conn.cursor()

    def create_pytomo_table(self, table=config_pytomo.TABLE_TIMESTAMP):
        '''  Function to create a table'''
        # Using Python's string operations makes it insecure (vulnerable
        # to SQL injection attack). Use of tuples makes it secure.
        if not self.created:
            config_pytomo.LOG.warn('Database could not be created\n'
                                   'Table creation aborted')
            return
        table_name = (table,)
        self._table_name = table
        cmd = ''.join(( "CREATE TABLE ", table,
                       """(ID TIMESTAMP,
                       Service text,
                       Url text,
                       CacheUrl text,
                       CacheServerDelay real,
                       IP text,
                       Resolver text,
                       ResolveTime real,
                       ASNumber int,
                       PingMin real,
                       PingAvg real,
                       PingMax real,
                       DownloadTime real,
                       VideoType text,
                       VideoDuration real,
                       VideoLength real,
                       EncodingRate real,
                       DownloadBytes int,
                       DownloadInterruptions int,
                       InitialData real,
                       InitialRate real,
                       InitialPlaybackBuffer real,
                       BufferingDuration real,
                       PlaybackDuration real,
                       BufferDurationAtEnd real,
                       TimeTogetFirstByte real,
                       MaxInstantThp real,
                       RedirectUrl text,
                       StatusCode int
                      )"""))
        try:
            self.py_cursor.execute(cmd)
        except sqlite3.Error, mes:
            config_pytomo.LOG.info("Table %s already exists: %s"
                                   % (table_name, mes))
        else:
            config_pytomo.LOG.info("Creating table : %s" % table_name)

    def insert_record(self, row):
        ''' Function to insert a record'''
        if not self.created:
            config_pytomo.LOG.warn('Database could not be created\n'
                                   'Insertion aborted')
            return
        cmd = ''.join(("INSERT INTO ", self._table_name,
                       " VALUES(?",
                       ',?' * config_pytomo.NB_FIELDS, ')'))
        try:
            self.py_cursor.execute(cmd, row)
        except sqlite3.Error, mes:
            config_pytomo.LOG.error('unable to add row: %s with error: %s'
                                    % (row, mes))
        else:
            config_pytomo.LOG.debug('row added to table')

    def fetch_all(self):
        ''' Function to print all the records of the table'''
        if not self.created:
            config_pytomo.LOG.warn('Database could not be created\n'
                                   'Fetch aborted')
            return
        if not self._table_name:
            cmd = "select name from sqlite_master"
            self.py_cursor.execute(cmd)
            table = self.py_cursor.fetchall()
            if len(table) == 1:
                self._table_name = table[0][0]
            else:
                print("No tables found in database")

        cmd = ' '.join(("SELECT * FROM", self._table_name))
        self.py_cursor.execute(cmd)
        for record in self.py_cursor:
            pprint(record)

    def describe_tables(self):
        '''Function to show the create command of a table'''
        if not self.created:
            config_pytomo.LOG.warn('Database could not be created\n'
                                   'Fetch aborted')
            return
        if not self._table_name:
            cmd = "SELECT name FROM sqlite_master"
            self.py_cursor.execute(cmd)
            table = self.py_cursor.fetchall()
            if len(table) == 1:
                self._table_name = table[0][0]
            else:
                print("No tables found in database")
        cmd = "SELECT sql FROM sqlite_master WHERE type = 'table'"
        self.py_cursor.execute(cmd)
        for record in self.py_cursor:
            pprint(record)

    def count_rows(self):
        '''Function to return the number of rows in a table.
        If there are problems related to database integrity, -1 is returned.
        '''
        if not self.created:
            config_pytomo.LOG.warn('Database could not be created\n'
                                   'Fetch aborted')
            return -1
        if not self._table_name:
            cmd = "SELECT name FROM sqlite_master"
            self.py_cursor.execute(cmd)
            table = self.py_cursor.fetchall()
            if len(table) == 1:
                self._table_name = table[0][0]
            else:
                print("No tables found in database")
                return -1
        cmd = ' '.join(("SELECT COUNT(*) FROM", self._table_name))
        self.py_cursor.execute(cmd)
        return self.py_cursor.fetchall()[0][0]

    def fetch_single_parameter_with_stats(self, parameter):
        '''Function to save (timestamp, parameter) in a sorted list of tuples
        only for records with stats
        '''
        if not self.created:
            config_pytomo.LOG.warn('Database could not be created\n'
                                   'Fetch aborted')
            return
        if not self._table_name:
            cmd = "select name from sqlite_master"
            self.py_cursor.execute(cmd)
            table = self.py_cursor.fetchall()
            if len(table) == 1:
                self._table_name = table[0][0]
            else:
                print("No tables found in database")
                return
        cmd = ' '.join(('SELECT ID, %s FROM' % parameter, self._table_name,
                        'WHERE DownloadTime > 0'))
        self.py_cursor.execute(cmd)
        return sorted(self.py_cursor.fetchall(), key=operator.itemgetter(0))

    def fetch_single_parameter(self, parameter):
        '''Function to save (timestamp,parameter) in a sorted list of tuples'''
        if not self.created:
            config_pytomo.LOG.warn('Database could not be created\n'
                                   'Fetch aborted')
            return
        if not self._table_name:
            cmd = "select name from sqlite_master"
            self.py_cursor.execute(cmd)
            table = self.py_cursor.fetchall()
            if len(table) == 1:
                self._table_name = table[0][0]
            else:
                print("No tables found in database")
                return
        cmd = ' '.join(("SELECT ID, %s FROM" % parameter,
                        self._table_name))
        self.py_cursor.execute(cmd)
        return sorted(self.py_cursor.fetchall(), key=operator.itemgetter(0))

    def fetch_all_parameters(self, parameters):
        '''Function to save (parameter_1, ..., parameter_n, timestamp) in a
        sorted list of tuples dependent on timestamp'''
        if not self.created:
            config_pytomo.LOG.warn('Database could not be created\n'
                                   'Fetch aborted')
            return
        if not self._table_name:
            cmd = "select name from sqlite_master"
            self.py_cursor.execute(cmd)
            table = self.py_cursor.fetchall()
            if len(table) == 1:
                self._table_name = table[0][0]
            else:
                print("No tables found in database")
                return
        # create the command to extract all the specified parameters
        # timestamp is the last element of each tuple
        join_parameters = ', '.join(parameters)
        cmd = ' '.join(("SELECT %s, ID FROM" % join_parameters,
                        self._table_name))
        config_pytomo.LOG.debug('Select command: %s' % cmd)
        self.py_cursor.execute(cmd)
        all_parameters = self.py_cursor.fetchall()
        #config_pytomo.LOG.debug('Extracted: %s' %
        #        str(all_parameters))
        return sorted(all_parameters, key=operator.itemgetter(-1))

    def fetch_start_time(self):
        '''Function to return the first timestamp in the database in linux
        format
        '''
        if not self.created:
            config_pytomo.LOG.warn('Database could not be created\n'
                                   'Fetch aborted')
            return
        if not self._table_name:
            cmd = "select name from sqlite_master"
            self.py_cursor.execute(cmd)
            table = self.py_cursor.fetchall()
            if len(table) == 1:
                self._table_name = table[0][0]
            else:
                config_pytomo.LOG.warning('No tables found in database')
                return
        cmd = ' '.join(("SELECT ID FROM", self._table_name))
        self.py_cursor.execute(cmd)
        try:
            timestamp = time_to_epoch(min(self.py_cursor.fetchall())[0])
        except ValueError:
            timestamp = None
        return timestamp

    def close_handle(self):
        "Closes the connection to the database"
        if not self.created:
            config_pytomo.LOG.warn('Database could not be created\n'
                                   'Close aborted')
            return
        self.py_conn.close()

    @staticmethod
    def logger_db():
        ''' Initialze the logger'''
        config_pytomo.LOG = logging.getLogger('pytomo_db')
        # to not have console output
        config_pytomo.LOG.propagate = False
        config_pytomo.LOG.setLevel(config_pytomo.LOG_LEVEL)
        timestamp = time.strftime("%Y-%m-%d.%H_%M_%S")
        if config_pytomo.LOG_FILE == '-':
            handler = logging.StreamHandler(sys.stdout)
        else:
            log_file = os.path.sep.join((config_pytomo. LOG_DIR,
                                '.'.join((timestamp, config_pytomo.LOG_FILE))))
            try:
                with open(log_file, 'a') as _:
                    pass
            except IOError:
                raise IOError('Logfile %s could not be open for writing' %
                                                                    log_file)
            handler = logging.FileHandler(filename=log_file)
        log_formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                  "%(levelname)s - %(message)s")
        handler.setFormatter(log_formatter)
        config_pytomo.LOG.addHandler(handler)

# TODO
def time_to_epoch(timestamp):
    ''' Function to transform to seconds from epoch time represented by a
    string of the form '%Y-%m-%d %H:%M:%S.%f'
    >>> time_to_epoch('2012-06-25 14:54:57.422007')
    1340628897
    >>> time_to_epoch(None)
    Traceback (most recent call last):
        ...
    TypeError: expected string or buffer
    >>> time_to_epoch('2012-06-25 14:54:57')
    1340628897
    >>> time_to_epoch('2012-06-25 14:54:57') #doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    ValueError: time data '2012-06-25 14:54:57' does not match format
    '%Y-%m-%d %H:%M:%S.%f'
    '''
    try:
        return int(time.mktime(time.strptime(timestamp,
                                             "%Y-%m-%d %H:%M:%S.%f")))
    except ValueError:
        return int(time.mktime(time.strptime(timestamp, "%Y-%m-%d %H:%M:%S")))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
