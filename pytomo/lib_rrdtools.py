#!/usr/bin/env python
'''Module for RRDtool interface to the pytomo data.

Necessary module: rrdtool (python-rrdtool,
                  http://oss.oetiker.ch/rrdtool/download.en.html)
Version: 0.1
Author: Ana Oprea
Date: 11.07.2012

    Usage:
        # first create a database - follow steps in lib_database
        import pytomo.start_pytomo as start_pytomo
        start_pytomo.configure_log_file('doc_test')
        import pytomo.lib_database as lib_database
        from pytomo.lib_plot import UNITS
        import pytomo.lib_rrdtools as lib_rrdtools

        pytomo_rrd = lib_rrdtools.PytomoRRD(db_name)
        pytomo_rrd.update_pytomo_rrd()
        pytomo_rrd.plot_pytomo_rrd()

        >>> import time
        >>> timestamp = time.strftime("%Y-%m-%d.%H_%M_%S")
        >>> # to make sure a new file is created for every run we use
        >>> # timestamp.
        >>> db_name = 'doc_test_lib_db' + str(timestamp) + '.db'
        >>> # import pytomo.lib_database as lib_database
        >>> doc_db = lib_database.PytomoDatabase(db_name)
        >>> doc_db.create_pytomo_table('doc_test_table')
        >>> import datetime
        >>> record = (datetime.datetime(2011, 5, 6, 15, 30, 50, 103775),
        ... 'Youtube', 'http://www.youtube.com/watch?v=RcmKbTR--iA',
        ... 'http://v15.lscache3.c.youtube.com',
        ... '173.194.20.56','default_10.193.225.12', None, None, None,
        ... 8.9944229125976562, 'mp4', 225, 115012833.0, 511168.14666666667,
        ... 9575411, 0, 1024 ,100,  0.99954795837402344, 7.9875903129577637,
        ... 35, 11.722306421319782, 1192528.8804511931, None)
        >>> doc_db.insert_record(record)
        >>> record = (datetime.datetime(2011, 5, 6, 15, 31, 10, 103775),
        ... 'Youtube', 'http://www.youtube.com/watch?v=RcmKbTR--iA',
        ... 'http://v15.lscache3.c.youtube.com',
        ... '173.194.20.56','default_10.193.225.12', None, None, None,
        ... 8.9944229125976562, 'mp4', 225, 115012833.0, 511168.14666666667,
        ... 9575411, 0, 1024, 100, 0.99954795837402344, 7.9875903129577637,
        ... 40, 11.722306421319782, 1192528.8804511931,
        ... 'http://www.youtube.com/fake_redirect')
        >>> doc_db.insert_record(record)
        >>> pytomo_rrd = PytomoRRD(db_name)
        >>> pytomo_rrd.update_pytomo_rrd()
        >>> pytomo_rrd.plot_pytomo_rrd()
        >>> from os import unlink
        >>> unlink(db_name)
'''

from __future__ import with_statement, absolute_import, print_function
import sys
# TODO Louis check if correct
if 'win' in sys.platform:
    try:
        import rrdtoolmodule as rrdtool
    except ImportError:
        from .rrdtool_win_x86_DLLs import rrdtoolmodule as rrdtool
else:
    try:
        import rrdtool
    except ImportError:
        print('Please install the RRDtool module on your system.\nWe suggest to'
              ' download from your distribution repository: python-rrdtool\n'
              'For Debian based systems: sudo apt-get install python-rrdtool\n'
              'For RHEL based systems: sudo yum install python-rrdtool\n')
import time
import math
from optparse import OptionParser
from operator import itemgetter
# only for logging
import logging
import os
# config file
try:
    from . import config_pytomo
except ValueError:
    import config_pytomo
# database data
try:
    from . import lib_database
except ValueError:
    import lib_database
from sqlite3 import Error
# parameters to extract from db and plot
try:
    from .lib_plot import UNITS
except ValueError:
    from lib_plot import UNITS
# file operations
try:
    from .lib_io import TIMESTAMP_POSITION, NO_DB_RECORDS_UNITS, \
    get_latest_file, rrd_filename, plot_filename
except ValueError:
    from lib_io import TIMESTAMP_POSITION, NO_DB_RECORDS_UNITS, \
    get_latest_file, rrd_filename, plot_filename

# RRD parameters
# RRD syncronise interval in seconds (plot cannot start exactly at start)
RRD_PLOT_SYNC_TIME = 300
# RRD syncronise interval in seconds (plot cannot start exactly at start)
RRD_STEP_SYNC_TIME = 1
# Consolidation function: AVERAGE, MIN, MAX, LAST
CF_AVG = 'AVERAGE'
CF_MAX = 'MAX'
CF_MIN = 'MIN'
CF_LAST = 'LAST'
# how many of primary DS are used to build a Consolidated Data Point which then
# goes into the archive (if all points need to be plotted set to 1)
# RRA_POINTS * RRD_STEP = time interval to apply CF
# specific for each CF, there can be different aggregations for the same CF
RRA_POINTS_AVG = 1
#RRA_POINTS_AVG3 = 3
RRA_POINTS_MIN = 1
RRA_POINTS_MAX = 1
RRA_POINTS_LAST = 1
# Data Source in rrd only allows for maximum 19 characters name
DS_NAME_MAX_LENGTH = 19
# percentage of allowed Unknown DS in a consolidation interval
RRA_U_PERCENTAGE = 0.99
# graph line thickness (mm)
RRD_PLOT_LINE = 2
# for some parameters that are generally zero the line is not very noticeable
# (problem noticed on WinXP_x86 and Ubuntu1204)
RRD_PLOT_LINE_GENERALLY_ZERO = 3
# line name for AVERAGE CF
RRD_PLOT_AVG_NAME = 'line_avg'
# line colour for AVERAGE CF in 0x
RRD_PLOT_AVG_COL = 'FF0000'
# line name for MIN CF
RRD_PLOT_MIN_NAME = 'line_min'
# line colour for AVERAGE CF in 0x
RRD_PLOT_MIN_COL = '00FF00'
# line name for MAX CF
RRD_PLOT_MAX_NAME = 'line_max'
# line colour for MAX CF in 0x
RRD_PLOT_MAX_COL = '0000FF'
# line name for LAST CF
RRD_PLOT_LAST_NAME = 'line_last'
# line colour for MAX CF in 0x
RRD_PLOT_LAST_COL = 'FFFF00'
# rrd plot characteristics
RRD_PLOT_CHARACTER = ['--lower-limit', '0',
                        '--rigid',
                        '--alt-autoscale-max',
                        '--font', 'WATERMARK:7']
# nr. of '=' displayed by log
NR_REPEAT = 28
# specific parameters
AVG_TH_PARAM = 'AvgThroughput'
INDICATOR_PARAM = 'ReceptionRatio'
DOWN_B_PARAM = 'DownloadBytes'
DOWN_T_PARAM = 'DownloadTime'
ENC_PARAM = 'EncodingRate'
DOWN_INT_PARAM = 'DownloadInterruptions'
VIDEO_PERCENTAGE_PARAM = 'VideosWithInterruptions'
# parameters to extract from db
PARAMETERS = sorted(UNITS.keys())
# parameters that do not exist in db
PARAM_NO_DB = sorted(NO_DB_RECORDS_UNITS.keys())
# all parameters to plot
ALL_PARAM = sorted(PARAMETERS + PARAM_NO_DB)
# parameters that are measured in bytes
PARAMETERS_IN_BYTES = ['DownloadBytes', 'InitialData', 'VideoLength']
# parameters that include buffering time
PARAMETERS_FOR_BUFFERING = ['BufferingDuration', 'BufferDurationAtEnd']
# parameters that should be genrally zero
PARAMETERS_GENERALLY_ZERO = ([DOWN_INT_PARAM, VIDEO_PERCENTAGE_PARAM] +
                             PARAMETERS_FOR_BUFFERING)
# indexes of parameters (for example {'DownloadTime': 0})
INDEX_DICT = dict((v, k) for (k, v) in enumerate(ALL_PARAM))
# power of 10 for Mega
MEGA_ORDER = 6
# needed to compute average throughput in kpbs
# 1 byte = 8 bits
BYTE_BIT_TRANS = 8
# kilo = 1000
KILO_TRANS = 1000
# easier to tranform rates to kbps
KBPS_TRANS = 8e-3

def create_DS_types(parameters, heartbeat):
    '''Function to return a list of elements 'DS:ds-name:GAUGE:heartbeat:U:U'
    >>> HEARTBEAT = 100
    >>> create_DS_types(['BufferDurationAtEnd', 'PingMin',
    ... 'InitialData'], HEARTBEAT) #doctest: +NORMALIZE_WHITESPACE
    ['DS:BufferDurationAtEnd:GAUGE:100:U:U', 'DS:PingMin:GAUGE:100:U:U',
    'DS:InitialData:GAUGE:100:U:U']
    >>> create_DS_types([], HEARTBEAT)
    []
    >>> create_DS_types(None, HEARTBEAT)
    Traceback (most recent call last):
        ...
    TypeError: 'NoneType' object is not iterable
    '''
    return [('DS:%s:GAUGE:%i:U:U' %
                                (parameter[:DS_NAME_MAX_LENGTH], heartbeat))
                                for parameter in parameters]

def generate_plot_names(parameters, timestamp):
    ''' Function to create a list of filenames for plots like:
    RRD_PLOT_DIR/parameter_to_plot_timestamp.extension
    TODO: redo doctest
    >>> from time import time
    >>> TIMESTAMP = '2012-07-20.11_44_27'
    >>> generate_plot_names(['DownloadTime',
    ... 'PingMin'], TIMESTAMP) #doctest: +NORMALIZE_WHITESPACEi, +ELLIPSIS
    ['/home/capture/co/pytomo/trunk/Pytomo/images/s-spo-hti.2012-07-20.11_44_27.DownloadTime_pytomo_image.png',
     '/home/capture/co/pytomo/trunk/Pytomo/images/s-spo-hti.2012-07-20.11_44_27.PingMin_pytomo_image.png']
    >>> generate_plot_names([], TIMESTAMP)
    []
    >>> generate_plot_names(None, TIMESTAMP)
    Traceback (most recent call last):
        ...
    TypeError: 'NoneType' object is not iterable
    '''
    try:
        return [plot_filename(parameter, timestamp) for parameter in parameters]
    except IOError:
        return None

def update_data_types(parameters):
    '''Function to return a string '%i:%s:...:%s' dependent on the number of DS
    >>> update_data_types(['BufferDurationAtEnd', 'PingMin', 'InitialData'])
    '%i:%s:%s:%s'
    >>> update_data_types([])
    '%i'
    >>> update_data_types(None)
    Traceback (most recent call last):
        ...
    TypeError: object of type 'NoneType' has no len()
    '''
    return "".join(("%i", "".join((":%s")*len(parameters))))

def format_null_values(*args):
    ''' Function to return a list where None arguments are transformed to U
    >>> format_null_values(('2012-06-25 14:54:57.422007', 0.0, None, 130048.0,
    ... None, 4643.9046215020562)) #doctest: +NORMALIZE_WHITESPACE
    [('2012-06-25 14:54:57.422007', 0.0, None, 130048.0, None,
        4643.9046215020562)]
    >>> format_null_values(*('2012-06-25 14:54:57.422007', 0.0, None, 130048.0,
    ... None, 4643.9046215020562)) #doctest: +NORMALIZE_WHITESPACE
    ['2012-06-25 14:54:57.422007', 0.0, 'U', 130048.0, 'U', 4643.9046215020562]
    >>> format_null_values(None)
    ['U']
    >>> format_null_values('2012-06-25 14:54:57.422007',*(0.0, None, 130048.0,
    ... None, 4643.9046215020562)) #doctest: +NORMALIZE_WHITESPACE
    ['2012-06-25 14:54:57.422007', 0.0, 'U', 130048.0, 'U', 4643.9046215020562]
    >>> format_null_values('2012-06-25 14:54:57.422007',(0.0, None, 130048.0,
    ... None, 4643.9046215020562)) #doctest: +NORMALIZE_WHITESPACE
    ['2012-06-25 14:54:57.422007', (0.0, None, 130048.0, None,
        4643.9046215020562)]
    '''
    return ['U' if item is None else item for item in args]

def rrd_filename_escape_colon(rrd_file):
    ''' Escape the : in the filename of a rrd because this is not accepted in
    the rrd_graph when defining a function (problem appears generally on
    Windows)
    >>> rrd_filename_escape_colon('/home/capture/co/pytomo/trunk/Pytomo/rrds/s-spo-hti.1350291171.pytomo.rrd')
    '/home/capture/co/pytomo/trunk/Pytomo/rrds/s-spo-hti.1350291171.pytomo.rrd'
    >>> rrd_filename_escape_colon('C:\Pytomo\rrds\s-spo-hti.1350291171.pytomo.rrd')
    'C\\:\\Pytomo\rrds\\s-spo-hti.1350291171.pytomo.rrd'
    '''
    return rrd_file.replace(':','\:')

class PytomoRRD:
    '''Pytomo class to interact with rrdtools
    '''

    has_values = None

    def __init__(self, db_file):
        '''Get the data and create the RRD (Round Robin Database).
        Parameters:
        --start = minimum timestamp in db - sync time
        --step = STEP - by default, data is fed in the rrd every 300s (5min)
        DS: ds-name : ds-type : heartbeat : min : max
        Data Source type: GAUGE - current, absolute value is saved
        Data Source heartbeat: HEARTBEAT - if no data is received after 5min, it
                                            is set to Unknown
        Data Source min: U - Unknown
        Data Source max: U - Unknown
        RRA: CF : cf-arguments
        Round Robin Archive: consists of a number of data values or statistics
        for each of the defined Data Sources (DS) and is defined within a line
        RRA Consolidation Function: AVERAGE - the average of the data points
        RRA CF-arguments: RRA_U_PERCENTAGE - percentage of values that can be U
        RRA CF-arguments: RRD_STEP - the CF of every (RRD_STEP * RRA_POINTS_...)
                                        is computed
        RRA CF-arguments: rra_rows - how many generations of data values are
            kept in an RRA; the CF is computed during
            (RRD_STEP * RRA_POINTS_AVG) * self.rra_rows (= total time plotted)
        '''
        # Intialize the logger for standalone testing Logging
        if not config_pytomo.LOG:
            self.logger_rrd()
        config_pytomo.LOG.info('=' * NR_REPEAT)
        config_pytomo.LOG.info("Parameters plotted by rrd: %s", PARAMETERS)
        # retrieve desired data from the database in a list of tuples
        try:
            self.data = lib_database.PytomoDatabase(db_file).\
                        fetch_all_parameters(PARAMETERS)
        except Error, mes:
            config_pytomo.LOG.error('Unable to extract data %s with  error:'
                                    '%s' % (str(PARAMETERS), mes))
            return
        config_pytomo.LOG.info(' '.join(("Retrieved data for rrd.",
                                "From database: ", os.path.basename(db_file))))
        # if no data is extracted from sqlite, no other operation is performed
        if not self.data:
            self.has_values = False
            config_pytomo.LOG.warn('No data could be extracted from the '
                                    '%s for the parameters: %s' %
                                (os.path.basename(db_file), PARAMETERS))
            return
        # if there is only one point in the data, rrdtool cannot plot
        if len(self.data) == 1:
            self.has_values = False
            config_pytomo.LOG.warn('Only one point could be extracted from the '
                                    '%s for the parameters: %s' %
                                (os.path.basename(db_file), str(PARAMETERS)))
            return
        self.has_values = True
        #config_pytomo.LOG.debug("Data: %s", str(self.data))
        # number of unknown (None) values in the dataset for each parameter
        self.unknown_values = [0] * len(PARAMETERS)
        # all the timestamps in the database
        timestamps = map(lib_database.time_to_epoch,
                                map(itemgetter(TIMESTAMP_POSITION), self.data))
        # the timestamp is the last element of each tuple in the data list
        # start time is the minimum timestamp (epoch) from the db - sync time
        self.start_time = timestamps[0] - RRD_PLOT_SYNC_TIME
        config_pytomo.LOG.debug("Start time rrd: %i", self.start_time)
        # end time is the maximum timestamp (epoch) from the db + sync time
        self.end_time = timestamps[-1] + RRD_PLOT_SYNC_TIME
        config_pytomo.LOG.debug("End time rrd: %i", self.end_time)
        # difference between two adjacent timestamps
        timestamp_dif = [abs(a - b) for a, b in zip(timestamps, timestamps[1:])]
        # time interval in seconds at which data will be fed into the RRD
        # minimum time difference between the data inserted
        # when time changes in winter the clock goes back 1h, difference is < 1s
        min_time_diff = min(timestamp_dif) - RRD_STEP_SYNC_TIME
        if min_time_diff < 1:
            RRD_STEP = 1
        else:
            RRD_STEP = min_time_diff
        # time interval in seconds after which data is considered Unknown
        # maximum time difference between the data inserted
        RRD_HEARTBEAT = max(timestamp_dif) + RRD_STEP_SYNC_TIME
        # create the Data Sources for the rrd
        self.data_sources = create_DS_types(PARAMETERS, RRD_HEARTBEAT)
        config_pytomo.LOG.debug("Data sources: %s", self.data_sources)
        # rrd file has the first db time to epoch timestamp
        # RRA number of data generations kept
        try:
            self.rrd_file = rrd_filename(str(timestamps[0]))
        except IOError:
            self.rrd_file = None
            config_pytomo.LOG.error("Could not get rrd file")
        # (RRD_STEP * RRA_POINTS_AVG) * self.rra_rows = total time plotted
        self.rra_rows = math.ceil((self.end_time - self.start_time) /
                                    RRD_STEP * RRA_POINTS_AVG)
        # if there is only one database entry or if the time difference between
        # start, end is too small, there might be no generation of data kept
        if self.rra_rows < 1:
            self.rra_rows = 1
        config_pytomo.LOG.debug("Number of data generations kept: %i",
                self.rra_rows)
        # all the points are plotted if RRA_POINTS_... = 1
        # to uncomment if other CF need to be applied on aggregated data
        # (min/max of 3 points for a specific interval, for example)
        rrdtool.create(self.rrd_file,
                        '--start', '%i' % self.start_time,
                        '--step', '%i' % RRD_STEP,
                        self.data_sources,
                        'RRA:%s:%f:%i:%i' %
                                    (CF_AVG, RRA_U_PERCENTAGE, RRA_POINTS_AVG,
                                        self.rra_rows) #,
        #                'RRA:AVERAGE%f:%i:%i' %
        #                                (RRA_U_PERCENTAGE, RRA_POINTS_AVG3,
        #                                self.rra_rows),
        #                'RRA:%s:%f:%i:%i' %
        #                            (CF_MIN, RRA_U_PERCENTAGE, RRA_POINTS_MIN,
        #                                self.rra_rows),
        #                'RRA:%s:%f:%i:%i' %
        #                            (CF_MAX, RRA_U_PERCENTAGE, RRA_POINTS_MAX,
        #                                self.rra_rows),
        #                'RRA:%s:%f:%i:%i' %
        #                            (CF_LAST, RRA_U_PERCENTAGE, RRA_POINTS_LAST,
        #                                self.rra_rows)
                        )
        config_pytomo.LOG.info(' '.join(("Created rrd: ",
                                            os.path.basename(self.rrd_file))))
        # image files have the first db time to epoch timestamp
        self.rrd_plot_files = generate_plot_names(ALL_PARAM, timestamps[0])

    def update_pytomo_rrd(self):
        '''Insert data from the list of tuples (timestamp, parameter1, ...)
        to the rrd.
        '''
        if not self.has_values:
            config_pytomo.LOG.warn('RRD data update aborted')
            return 1
        # insert into rrd all the values for the extracted parameters to plot
        # data[][TIMESTAMP_POSITION] is the timestamp
        # data[][:TIMESTAMP_POSITION] represents the parameters to plot
        for row in self.data:
            # transform timestamp to epoch in local time
            # TODO: check problems related to timezone
            timestamp = row[TIMESTAMP_POSITION]
            parameter_values = row[:TIMESTAMP_POSITION]
            # function used in order to take advantage of the * operator and
            # retrieve all the elements of an argument
            identity = lambda *x: x
            try:
                rrdtool.update(self.rrd_file,
                                update_data_types(parameter_values) %
                                identity(lib_database.time_to_epoch(timestamp),
                                    *format_null_values(*parameter_values)))
            except rrdtool.error, mes:
                config_pytomo.LOG.debug('Could not update the rrd with error'
                                        ' %s' % mes)
                continue
            #config_pytomo.LOG.debug('Updated rrd data: (%s, %s)' %
            #       (timestamp, str(format_null_values(*parameter_values))))
            for index, parameter in enumerate(parameter_values):
                if parameter is None:
                    self.unknown_values[index] += 1
                    #config_pytomo.LOG.debug('Updated unknown[%i]' %
                    #                       index)
        config_pytomo.LOG.debug('Unknown values per parameter: %s' %
                                                    str(self.unknown_values))

    def fetch_pytomo_rrd(self):
        '''Fetch data from the rrd.
        '''
        if not self.has_values:
            config_pytomo.LOG.warn('RRD data fetch aborted')
            return 1
        # fetch data
        config_pytomo.LOG.debug('Fetched rrd %s data %s' % (CF_AVG,
                        str(rrdtool.fetch(self.rrd_file,
                            '%s' % CF_AVG,
                            '--start', '%i' % self.start_time,
                            '--end', '%i' % self.end_time #,
                            ))))

    def plot_pytomo_rrd(self):
        '''Plot the time series parameters (at least 3 points must exist in the
        database for the graphs to exist).
        '''
        if not self.has_values:
            config_pytomo.LOG.warn('RRD data plot aborted')
            return 1
        # rrdtool graph does not accept ":" in the rrd filename path
        def_rrd_file = rrd_filename_escape_colon(self.rrd_file)
        # graphs that exist in db
        for unknown_values_index, parameter in enumerate(PARAMETERS):
            # set the line thickness of the plots (this needs to be thicker if
            # values are generally zero)
            line_thickness = RRD_PLOT_LINE
            index = INDEX_DICT[parameter]
            # display in Mega for parameters that are in bytes
            if parameter in PARAMETERS_IN_BYTES:
                units_exp = ['--units-exponent', '%s' % str(MEGA_ORDER)]
            elif parameter in PARAMETERS_FOR_BUFFERING:
                units_exp = ['--alt-y-grid']
            else:
                units_exp = ['--units-exponent', '0']
            if parameter in PARAMETERS_GENERALLY_ZERO:
                line_thickness = RRD_PLOT_LINE_GENERALLY_ZERO
            # all the points are plotted if RRA_POINTS_... = 1
            # to uncomment if other CF need to be applied on aggregated data
            # (min/max of 3 points for a specific interval, for example)
            rrdtool.graph(self.rrd_plot_files[index],
                            '--start', '%i' % self.start_time,
                            '--end', '%i' % self.end_time,
                            '--vertical-label', '%s' % UNITS[parameter],
                            '--title', 'Pytomo %s statistics' % parameter,
                            RRD_PLOT_CHARACTER,
                            units_exp,
                            # only display number of unknown data values
                            '--watermark', 'Number of unknown data values: %i'
                                    % self.unknown_values[unknown_values_index],
                            #'--full-size-mode',
                            'DEF:%s=%s:%s:%s'
                            % (RRD_PLOT_AVG_NAME, def_rrd_file,
                                parameter[:DS_NAME_MAX_LENGTH], CF_AVG),
                            'LINE%i:%s#%s' % (line_thickness,
                                RRD_PLOT_AVG_NAME, RRD_PLOT_AVG_COL),
                            #'DEF:%s=%s:%s:%s'
                            #% (RRD_PLOT_MIN_NAME, self.rrd_file,
                            #    parameter[:DS_NAME_MAX_LENGTH], CF_MIN),
                            #'LINE%i:%s#%s:Minimum' % (RRD_PLOT_LINE,
                            #    RRD_PLOT_MIN_NAME, RRD_PLOT_MIN_COL),
                            #'DEF:%s=%s:%s:%s'
                            #% (RRD_PLOT_MAX_NAME, self.rrd_file,
                            #    parameter[:DS_NAME_MAX_LENGTH], CF_MAX),
                            #'LINE%i:%s#%s:Maximum' % (RRD_PLOT_LINE,
                            #    RRD_PLOT_MAX_NAME, RRD_PLOT_MAX_COL),
                            #'DEF:%s=%s:%s:%s'
                            #% (RRD_PLOT_LAST_NAME, self.rrd_file,
                            #    parameter[:DS_NAME_MAX_LENGTH], CF_LAST),
                            #'LINE%i:%s#%s:Last' % (RRD_PLOT_LINE,
                            #    RRD_PLOT_LAST_NAME, RRD_PLOT_LAST_COL)
                            )
            config_pytomo.LOG.info(' '.join(("The rrd plot was updated: ",
                                os.path.basename(self.rrd_plot_files[index]))))
            config_pytomo.LOG.info('=' * NR_REPEAT)
        # graph for average throughput:
        # avg_th [Kbps] = DownBytes [bytes] / DownTime [s] * 8 /1000
        rrdtool.graph(self.rrd_plot_files[INDEX_DICT[AVG_TH_PARAM]],
                        '--start', '%i' % self.start_time,
                        '--end', '%i' % self.end_time,
                        '--vertical-label', '%s' %
                                            NO_DB_RECORDS_UNITS[AVG_TH_PARAM],
                        '--title', 'Pytomo %s statistics' % AVG_TH_PARAM,
                        RRD_PLOT_CHARACTER,
                        '--units-exponent', '0',
                        '--watermark', 'Number of unknown data values: %i'
                                % self.unknown_values[INDEX_DICT[DOWN_B_PARAM]],
                        'DEF:%s=%s:%s:%s' % (DOWN_B_PARAM[:DS_NAME_MAX_LENGTH],
                                             def_rrd_file,
                                             DOWN_B_PARAM[:DS_NAME_MAX_LENGTH],
                                             CF_AVG),
                        'DEF:%s=%s:%s:%s' % (DOWN_T_PARAM[:DS_NAME_MAX_LENGTH],
                                             def_rrd_file,
                                             DOWN_T_PARAM[:DS_NAME_MAX_LENGTH],
                                             CF_AVG),
                        'CDEF:%s=%s,%s,/,%s,*' %
                                            (AVG_TH_PARAM[:DS_NAME_MAX_LENGTH],
                                             DOWN_B_PARAM[:DS_NAME_MAX_LENGTH],
                                             DOWN_T_PARAM[:DS_NAME_MAX_LENGTH],
                                             str(KBPS_TRANS)
                                             #str(KILO_TRANS)
                                            ),
                        'LINE%i:%s#%s' % (RRD_PLOT_LINE,
                                          AVG_TH_PARAM[:DS_NAME_MAX_LENGTH],
                                          RRD_PLOT_AVG_COL)
                         )
        config_pytomo.LOG.info(' '.join(("The rrd plot was updated: ",
            os.path.basename(self.rrd_plot_files[INDEX_DICT[AVG_TH_PARAM]]))))
        config_pytomo.LOG.info('=' * NR_REPEAT)
        # graph for indicator:
        # indicator = DownBytes[B] / DownTime[s] * 8 / 1000 / EncodingRate[kbps]
        rrdtool.graph(self.rrd_plot_files[INDEX_DICT[INDICATOR_PARAM]],
                        '--start', '%i' % self.start_time,
                        '--end', '%i' % self.end_time,
                        '--vertical-label', '%s' %
                                        NO_DB_RECORDS_UNITS[INDICATOR_PARAM],
                        '--title', 'Pytomo %s statistics' % INDICATOR_PARAM,
                        RRD_PLOT_CHARACTER,
                        '--units-exponent', '0',
                        '--watermark', 'Number of unknown data values: %i'
                                % self.unknown_values[INDEX_DICT[DOWN_B_PARAM]],
                        'DEF:%s=%s:%s:%s' % (DOWN_B_PARAM[:DS_NAME_MAX_LENGTH],
                                             def_rrd_file,
                                             DOWN_B_PARAM[:DS_NAME_MAX_LENGTH],
                                             CF_AVG),
                        'DEF:%s=%s:%s:%s' % (DOWN_T_PARAM[:DS_NAME_MAX_LENGTH],
                                             def_rrd_file,
                                             DOWN_T_PARAM[:DS_NAME_MAX_LENGTH],
                                             CF_AVG),
                        'DEF:%s=%s:%s:%s' % (ENC_PARAM[:DS_NAME_MAX_LENGTH],
                                             def_rrd_file,
                                             ENC_PARAM[:DS_NAME_MAX_LENGTH],
                                             CF_AVG),
                        #'CDEF:%s=%s,%s,/,%s,*,%s,/' %
                        'CDEF:%s=%s,%s,/,%s,*,%s,/' %
                                        (INDICATOR_PARAM[:DS_NAME_MAX_LENGTH],
                                         DOWN_B_PARAM[:DS_NAME_MAX_LENGTH],
                                         DOWN_T_PARAM[:DS_NAME_MAX_LENGTH],
                                         str(KBPS_TRANS),
                                         ENC_PARAM[:DS_NAME_MAX_LENGTH]),
                        'LINE%i:%s#%s' % (RRD_PLOT_LINE,
                                          INDICATOR_PARAM[:DS_NAME_MAX_LENGTH],
                                          RRD_PLOT_AVG_COL)
                         )
        config_pytomo.LOG.info(' '.join(("The rrd plot was updated: ",
           os.path.basename(self.rrd_plot_files[INDEX_DICT[INDICATOR_PARAM]]))))
        config_pytomo.LOG.info('=' * NR_REPEAT)
        # graph for magic parameter:
        # video_percentage = 1 IF DownInterruptions > 0, ELSE 0
        rrdtool.graph(self.rrd_plot_files[INDEX_DICT[VIDEO_PERCENTAGE_PARAM]],
                        '--start', '%i' % self.start_time,
                        '--end', '%i' % self.end_time,
                        '--vertical-label', '%s' %
                                    NO_DB_RECORDS_UNITS[VIDEO_PERCENTAGE_PARAM],
                        '--title', 'Pytomo %s statistics' %
                                                        VIDEO_PERCENTAGE_PARAM,
                        RRD_PLOT_CHARACTER,
                        '--units-exponent', '0',
                        '--watermark', 'Number of unknown data values: %i'
                            % self.unknown_values[INDEX_DICT[DOWN_INT_PARAM]],
                        'DEF:%s=%s:%s:%s' % (DOWN_INT_PARAM[:DS_NAME_MAX_LENGTH],
                                             def_rrd_file,
                                             DOWN_INT_PARAM[:DS_NAME_MAX_LENGTH],
                                             CF_AVG),
                        # IF DownloadInterruptions > 0: ((DOWN_INT_PARAM, 0) GT)
                        # IF so, return 1, else return 0
                        'CDEF:%s=%s,0,GT,1,0,IF' %
                                (VIDEO_PERCENTAGE_PARAM[:DS_NAME_MAX_LENGTH],
                                 DOWN_INT_PARAM[:DS_NAME_MAX_LENGTH]),
                        'LINE%i:%s#%s' % (RRD_PLOT_LINE_GENERALLY_ZERO,
                                    VIDEO_PERCENTAGE_PARAM[:DS_NAME_MAX_LENGTH],
                                    RRD_PLOT_AVG_COL)
                         )
        config_pytomo.LOG.info(' '.join(("The rrd plot was updated: ",
            os.path.basename(self.rrd_plot_files[INDEX_DICT[AVG_TH_PARAM]]))))
        config_pytomo.LOG.info('=' * NR_REPEAT)


    @staticmethod
    def logger_rrd():
        ''' Initialze the logger'''
        config_pytomo.LOG = logging.getLogger('pytomo_rrd')
        # to not have console output
        #config_pytomo.LOG.propagate = False
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

def create_options(parser):
    ''' Add the different options to the parser'''
    parser.add_option('-v', '--verbose', dest='verbose',
            action='store_true', default=False, help = 'run as verbose mode')
    parser.add_option('-f', '--file', dest='db_name',
            help = 'run on a specific database (by default the latest database'
                     ' in the default database directory is selected)')
    parser.add_option('-d', '--dir', dest='db_dir_name',
            help = 'run on a specific directory where the '
            'latest database will be selected')

def main(argv=None):
    "Program wrapper"
    if argv is None:
        argv = sys.argv[1:]
    usage = '%prog [-v] [-d database_directory] [-f database]'
    parser = OptionParser(usage=usage)
    create_options(parser)
    (options, args) = parser.parse_args(argv)
    # if no specific directory or database is specified, the latest one from
    # DB_DIR is selected
    if not options.db_name and not options.db_dir_name:
        database = get_latest_file(config_pytomo.DATABASE_DIR)
    # if database is specified
    if options.db_name:
        database = options.db_name
    # if a directory is specified, the latest database there is selected
    if options.db_dir_name:
        database = get_latest_file(options.db_dir_name)
    pytomo_rrd = PytomoRRD(database)
    pytomo_rrd.update_pytomo_rrd()
    pytomo_rrd.plot_pytomo_rrd()
    return 0

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    sys.exit(main())
