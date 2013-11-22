#!/usr/bin/env python
'''Module for I/O operations on filesystem.
Used to write the index.html to display the graphical interface.
Version: 0.1
Author: Ana Oprea
Date: 20.07.2012

    Usage:
'''
from __future__ import with_statement, absolute_import, print_function
import time
from optparse import OptionParser
import re
# only for logging
import logging
import sys
import os
from itertools import chain
from datetime import datetime
from operator import itemgetter
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
# to check if files/dirs exist and set name
try:
    from .start_pytomo import check_out_files
except ValueError:
    from start_pytomo import check_out_files
from .fpdf import FPDF, HTMLMixin

# FPDF can buffer output or write to file
WRITE_TO_FILE = 'F'
# html related
# TODO: relative path?
# template that contains style and header
START_TEMPLATE_NAME = 'start_template.html'
# template that contains footer
END_TEMPLATE_NAME = 'end_template.html'
# names and headers
MIDDLE_COL_TABLE_HEADER = ['Time', 'Video', 'Cache server']
MID_COL_NAME = 'col1'
MID_COL_HEADER = 'Graphs'
LEFT_COL_NAME = 'col2'
LEFT_COL_HEADER = 'Links to graphs'
RIGHT_COL_NAME = 'col3'
RIGHT_COL_HEADER = 'Average parameters'
RIGHT_COL_TABLE_HEADER = ['Parameter', 'Value']
# html tags
BR_TAG = '<BR>'
IMG_TAG = '<IMG src="%s" alt=%s>'
LI_START_TAG = '<li>'
LI_END_TAG = '</li>'
UL_START_TAG = '<ul>'
UL_NOSTYLE_START_TAG = '<ul style="list-style: none;">'
UL_END_TAG = '</ul>'
DIV_START_TAG = '<div class=%s>'
DIV_END_TAG = '</div>'
HEADER_TAG = '<h2>%s</h2>'
TABLE_START_TAG = '<table border="1"; align="center">'
TABLE_END_TAG = '</table>'
TR_START_TAG = '<tr>'
TR_END_TAG = '</tr>'
TH_TAG = '<th>%s</th>'
TH_TAG_WIDTH = '<th width="50%">%s</th>'
TH_TAG_ALIGNED = '<th align="left">%s</th>'
TD_START_TAG = '<td>'
TD_START_TAG_ALIGNED = '<td align="left">'
TD_END_TAG = '</td>'
A_TAG = '<a href="%s">%s</a>'
P_TAG = '<p>%s</p>  '
# nr. of spaces before the DIV tags in the main page
NR_DIV_SPACES = 13
# nr. of spaces before the h2/IMG tags in the main page
NR_INNER_SPACES = 17
# end of line
END_LINE = '\n'
# separator for directories when accessing through http
# for example, you for an image, it will always be ..\images\xx.png
PATH_SEPARATOR = '/'
# text to display for Service link
TEXT_YT = ' video'
# text to display for cache server
TEXT_CACHE = 'cache server'
# names will have parameter and timestamp connected by '_'
NAME_CONNECTOR = '_'
# dictionaries/lists with parameters to plot
# key that contains all the parameters to plot
ALL_KEY = 'All_Parameters'
# key that contains all the main parameters to plot
MAIN_KEY = ' Main_Parameters'
# key that is used to display 'Service' videos downloaded instead of plots
LINKS_KEY = 'Links_to_played_videos'
# key that is used to display the existent databases in the database directory
DB_KEY = 'Database_archive'
# key that is used to link to the description
DOC_KEY = 'Project_documentation'
# database extension
DB_EXTENSION = '(pytomo_database\.db)$'
# database input parameter
DB_INPUT = '?db='
# units for graphs that do not have records in the database
NO_DB_RECORDS_UNITS = {
    'AvgThroughput': 'kbps',
    'ReceptionRatio': '',
    'VideosWithInterruptions': ''
}
# dictionary with mappings for what to plot
ALL_PLOTS = {
        ALL_KEY: sorted(UNITS.keys() + NO_DB_RECORDS_UNITS.keys()),
        MAIN_KEY: ['VideosWithInterruptions', 'AvgThroughput',
                   'BufferingDuration', 'PingAvg'],
        'QoE': ['VideosWithInterruptions','DownloadInterruptions',
                'ReceptionRatio', 'BufferingDuration', 'BufferDurationAtEnd'],
        'QoS': ['AvgThroughput', 'MaxInstantThp', 'InitialRate',
                'InitialData', 'DownloadBytes', 'DownloadTime',
                'PlaybackDuration', 'PingMin', 'PingAvg', 'PingMax'],
        'Video_characteristics': ['VideoLength', 'VideoDuration',
                                  'EncodingRate'],
        'ESMC': ['AvgThroughput', 'PingAvg', 'VideosWithInterruptions',
               'ResolveTime', 'TimeTogetFirstByte', 'StatusCode']
        }
# dictionary with explanations for what is plotted
MAN_PLOTS = {
        'PingMin': 'The minimum recorded ping time to the resolved IP address'
                    ' of the cache server',
        'PingAvg': 'The average recorded ping time to the resolved IP address'
                    ' of the cache server',
        'PingMax': 'The maximum recorded ping time to the resolved IP address'
                    ' of the cache server',
        'DownloadTime': 'The time taken to download the video sample (we do not'
                        ' download the entire video, but only its beginning)',
        'VideoDuration': 'The actual duration of the complete video',
        'VideoLength': 'The length of the complete video',
        'EncodingRate': 'The encoding rate of the video:'
                        ' VideoLength / VideoDuration',
        'DownloadBytes': 'The length of the video sample',
        'DownloadInterruptions': 'Number of interruptions experienced during'
                                 ' the download',
        'InitialData': 'Data downloaded in the initial buffering period',
        'InitialRate': 'The mean data rate during the initial'
                       ' buffering period',
        'BufferingDuration': 'Accumulated time spent in buffering state',
        'PlaybackDuration': 'Accumulated time spent in playing state',
        'BufferDurationAtEnd': 'The buffer length at the end of the download',
        'MaxInstantThp': 'The maximum instantaneous throughput of the '
                         'download',
        'AvgThroughput': 'The average throughput: DownloadBytes / DownloadTime',
        'ReceptionRatio': 'Quality of Experience parameter: '
                     'AvgThroughput / EncodingRate',
        'VideosWithInterruptions': 'Quality of Experience parameter: signals'
                            ' interruptions during video download <BR>'
                            '(1 - there are interuptions, 0 - no interuptions)',
    'TimeTogetFirstByte': 'Time from connection initialisation to first video'
                    'paquet',
    'StatusCode': 'Status code of the HTTP request',
    'ResolveTime': 'Time to get the DNS answer'
        }
# average parameters
AVERAGE_PARAM_DESCRIPTION = ['Service crawled', 'Total crawl time',
                'Start crawl time', 'End crawl time', 'Number of videos played',
                'Download Time average (sec)', 'Download Interruptions average',
                'Ping average (msec)']
AVERAGE_PARAM = ['DownloadTime', 'DownloadInterruptions', 'PingAvg']
# parameters regarding urls - must change Service position when needed!!!
URL_PARAM = ['Url', 'CacheUrl', 'Service']
SERVICE_POS_IN_URL = 2
# indexes of parameters (for example {'Url': 0})
#INDEX_DICT = dict((v,k) for (k,v) in enumerate(DATA_PARAM))
# timestamp position in the data extracted from the database
TIMESTAMP_POSITION = -1
# max timestamp length (not to display fractions)
MAX_TIMESTAMP_LENGTH = 19
# precision of average parameters
AVERAGE_PRECISION = 4
# message to display in case there are not enough records in db to create plots
DB_NO_RECORDS_MSG = ('There are not enough records in the selected database to'
                    ' create the graphs. Please wait for the database to be '
                    'populated or select another database.')
# only make page autorefresh if database has changed recently
REFRESH_TIMEOUT = 120000 # 120s
# http://ckon.wordpress.com/2008/07/25/stop-using-windowonload-in-javascript/
ONLOAD_REFRESH_SCRIPT = ('<script type="text/JavaScript">'
                         'window.addEventListener ?\n'
                         'window.addEventListener("load",'
                                                     'AutoRefresh(%i),false):\n'
                         'window.attachEvent && window.attachEvent("onload",'
                                                    'AutoRefresh(%i));\n'
                         '</script>\n'% (REFRESH_TIMEOUT, REFRESH_TIMEOUT))
# Service being crawled taken from the database info, default config_pytomo
SERVICE = config_pytomo.CRAWL_SERVICE
# message to display PDF path
PDF_MSG = 'The PDF report of this page is can be found at:<BR>'
PDF_HEADER = '<H1 align="center">Pytomo Statistics Report</H1>'
# how many BR to insert in order to not write man under image
PDF_SPACE_FOR_IMG = 12
# how many BR to insert between images
PDF_SPACE_BETWEEN = 5
# connector for http links (needed for rel path of pdf on win)
HTTP_CONNECTOR = '/'

class PytomoFPDF(FPDF, HTMLMixin):
    ''' Class to create pdf from html
    '''

    def __init__(self, pdf_name):
        ''' Set the pdf name
        '''
        self.pdf_name = pdf_name
        super(PytomoFPDF, self).__init__()

    def close_pdf(self):
        self.output(self.pdf_name, WRITE_TO_FILE)

def create_pdf(pdf_name, timestamp, average_values, *parameters):
    config_pytomo.LOG.debug('pdf_name = %s; timestamp = %s; parameters = %s' %
                           (pdf_name, timestamp, str(parameters)))
    pdf = PytomoFPDF(pdf_name)
    pdf.add_page()
    #config_pytomo.LOG.debug('Added 1 page')
    html_text = html_graphs_for_pdf(timestamp, average_values, *parameters)
    pdf.write_html(html_text)
    #config_pytomo.LOG.debug('Wrote html')
    pdf.close_pdf()
    #config_pytomo.LOG.debug('Closed pdf')

# code adapted from write_middle/right_column, done in a hurry
def html_graphs_for_pdf(timestamp, average_values, *parameters):
    ''' Function to return the html containing graphs and their explanation
    for the *parameters
    '''
    html_text = PDF_HEADER
    # average values
    if not average_values:
        config_pytomo.LOG.debug('No data has been received to create the list')
        return html_text
    # start list of average values
    html_text += (' ' * NR_INNER_SPACES + UL_START_TAG + END_LINE)
    for parameter, value in zip(AVERAGE_PARAM_DESCRIPTION, average_values):
        html_text += ((' ' * NR_INNER_SPACES + LI_START_TAG + '%s: %s' +
                    LI_END_TAG + END_LINE) % (parameter, value))
    # end list of average values
    html_text += (' ' * NR_INNER_SPACES + UL_END_TAG + END_LINE)
    html_text += (BR_TAG)
    # graphs
    # if there are not enough records in the db to display plots
    if not timestamp and parameters[0] != DB_KEY:
        html_text += ((P_TAG + END_LINE) % DB_NO_RECORDS_MSG)
        return
    # check which graphs to display
    if parameters[0] not in [LINKS_KEY, DB_KEY]:
        param_to_display = parameters
    else:
        param_to_display = ALL_PLOTS[MAIN_KEY]
    # the middle column consists of plots for the parameters
    # the graphs
    for parameter in param_to_display:
        for index in xrange(PDF_SPACE_BETWEEN):
            html_text += (' ' * NR_INNER_SPACES + BR_TAG + END_LINE)
        # function is called from pytomo directory, the image dir is
        # a subfolder of parent directory
        html_text += ((' ' * NR_INNER_SPACES + IMG_TAG + END_LINE) %
                 (plot_path_to_write_in_pdf(parameter, timestamp), parameter))
        for index in xrange(PDF_SPACE_FOR_IMG):
            html_text += (BR_TAG)
        html_text += ((' ' * NR_INNER_SPACES + P_TAG + END_LINE) %
                    MAN_PLOTS[parameter])
    return html_text


# TODO: check on windows
def plot_path_to_write_in_pdf(param, timestamp):
    ''' Return the path to the plot relative to the TEMPLATES_DIR
    Will have the pattern:
        <RRD_PLOT_DIR>/<plot_name>
    '''
    return PATH_SEPARATOR.join((config_pytomo.RRD_PLOT_DIR,
                            os.path.basename(plot_filename(param, timestamp))))

def pdf_filename(param, timestamp):
    ''' Return the file name of the pdf (try to create it if it does not
    exist).  Will have the pattern:
                <PDF_DIR>/<hostname>.<timestamp>.<param_PDF_FILE>
    '''
    return check_out_files(NAME_CONNECTOR.join((param,
                                    config_pytomo.PDF_FILE)),
                                    config_pytomo.PDF_DIR, str(timestamp))

def rrd_filename(timestamp):
    ''' Return the file name of the rrd (try to create it if it does not
    exist). Will have the pattern:
                <RRD_DIR>/<hostname>.<timestamp>.<RRD_FILE>
    '''
    return check_out_files(config_pytomo.RRD_FILE, config_pytomo.RRD_DIR,
                           str(timestamp))

def plot_filename(param, timestamp):
    ''' Return the file name of the plot (try to create it if it does not
    exist).  Will have the pattern:
                <RRD_PLOT_DIR>/<hostname>.<timestamp>.<param_IMAGE_FILE>
    '''
    return check_out_files(NAME_CONNECTOR.join((param,
                                    config_pytomo.IMAGE_FILE)),
                                    config_pytomo.RRD_PLOT_DIR, str(timestamp))

def index_filename(param, timestamp):
    ''' Return the file name of the index (try to create it if it does not
    exist). Will have the pattern:
                <TEMPLATES_DIR>/<hostname>.<timestamp>.<param_TEMPLATE_FILE>
    '''
    return check_out_files(NAME_CONNECTOR.join((param,
                                    config_pytomo.TEMPLATE_FILE)),
                                    config_pytomo.TEMPLATES_DIR, str(timestamp))

def plot_path_to_write_in_html(param, timestamp):
    ''' Return the path to the plot relative to the TEMPLATES_DIR
    Will have the pattern:
        ../<RRD_PLOT_DIR>/<plot_name>
    '''
    return PATH_SEPARATOR.join((os.pardir, config_pytomo.RRD_PLOT_DIR,
                            os.path.basename(plot_filename(param, timestamp))))

def check_templates_exist(timestamp):
    ''' Verify that all html templates and their plots have been created.
    '''
    for parameter in ALL_PLOTS[ALL_KEY]:
        if (not (os.path.getsize(index_filename(parameter, timestamp)))
                or not (os.path.getsize(plot_filename(parameter, timestamp)))):
            return False
    for parameter in chain(ALL_PLOTS.keys(), [LINKS_KEY, DB_KEY]):
        if not os.path.getsize(index_filename(parameter, timestamp)):
            return False
    return True

def get_latest_file(path):
    ''' Function to return the newest file in a path
    >>> import os.path
    >>> from tempfile import NamedTemporaryFile
    >>> f = NamedTemporaryFile(delete=False)
    >>> f.name == get_latest_file(os.path.dirname(f.name))
    True
    >>> f.close()
    >>> os.unlink(f.name)
    '''
    for root, dirs, files in os.walk(path):
        try:
            return max([os.path.join(root, name) for name in files],
                                                key=os.path.getmtime)
        except ValueError:
            config_pytomo.LOG.error('There is no file in %s' % path)

def get_latest_specific_file(path, include):
    ''' Function to return the newest file in a path
    >>> import os.path
    >>> from tempfile import NamedTemporaryFile
    >>> INCLUDE = 'test'
    >>> f = NamedTemporaryFile(suffix=INCLUDE, delete=False)
    >>> f.name == get_latest_specific_file(os.path.dirname(f.name), INCLUDE)
    True
    >>> f.close()
    >>> os.unlink(f.name)
    '''
    try:
        return max(get_specific_files(path, include), key=os.path.getmtime)
    except TypeError:
        #config_pytomo.LOG.warning('There is no file in %s that includes %s!' %
        #                          (path, include))
        return None

def get_specific_files(path, include):
    ''' Function to return all the files in path that contain include string in
    their name
    >>> import os.path
    >>> from tempfile import NamedTemporaryFile
    >>> INCLUDE = 'test'
    >>> f1 = NamedTemporaryFile(suffix=INCLUDE, delete=False)
    >>> f2 = NamedTemporaryFile(suffix=INCLUDE, delete=False)
    >>> f3 = NamedTemporaryFile(delete=False)
    >>> set([f1.name, f2.name]) == set(
    ... get_specific_files(os.path.dirname(f1.name), INCLUDE))
    True
    >>> set([f1.name, f2.name, f3.name]) == set(
    ... get_specific_files(os.path.dirname(f1.name), INCLUDE))
    False
    >>> f1.close()
    >>> f2.close()
    >>> f3.close()
    >>> os.unlink(f1.name)
    >>> os.unlink(f2.name)
    >>> os.unlink(f3.name)
    '''
    p = re.compile(include)
    for root, dirs, files in os.walk(path):
        # both Linux&Win must have / as separator (http acces)
        return sorted([(path + PATH_SEPARATOR + name)
                for name in files if p.search(name)], key=os.path.getmtime,
                                                               reverse=True)

# AO 20121015 not used anymore
def get_file_by_param_timestamp(path, parameter, timestamp):
    ''' Function to return from the path directory the files for a specific
     parameter timestamped or None.
     The filenames are relative to the parent directory.
    >>> import os.path
    >>> from tempfile import NamedTemporaryFile
    >>> from time import time
    >>> PARAM = 'DownloadTime'
    >>> TIMESTAMP = str(int(time()))
    >>> RRD_PLOT_DIR = 'images'
    >>> f1 = NamedTemporaryFile(suffix=PARAM, dir=RRD_PLOT_DIR, delete=False)
    >>> f2 = NamedTemporaryFile(suffix=TIMESTAMP, dir=RRD_PLOT_DIR,
    ... delete=False)
    >>> f3 = NamedTemporaryFile(suffix=(PARAM + '_' + TIMESTAMP),
    ... dir=RRD_PLOT_DIR, delete=False)
    >>> os.path.basename(f3.name) == os.path.basename(
    ... get_file_by_param_timestamp(RRD_PLOT_DIR, PARAM, TIMESTAMP))
    True
    >>> os.path.basename(f2.name) == os.path.basename(
    ... get_file_by_param_timestamp(RRD_PLOT_DIR, PARAM, TIMESTAMP))
    False
    >>> os.path.basename(f1.name) == os.path.basename(
    ... get_file_by_param_timestamp(RRD_PLOT_DIR, PARAM, TIMESTAMP))
    False
    >>> f1.close()
    >>> f2.close()
    >>> f3.close()
    >>> os.unlink(f1.name)
    >>> os.unlink(f2.name)
    >>> os.unlink(f3.name)
    '''
    try:
        file_name = str(os.path.pardir + PATH_SEPARATOR +
                get_specific_files(path, parameter + NAME_CONNECTOR +
                                                            str(timestamp))[0])
    except IndexError:
        file_name = None
    return file_name

# AO 20121015 not used anymore
def check_templates_exist_obsolete(timestamp):
    ''' Verify that all html templates and their plots have been created.
    '''
    for parameter in ALL_PLOTS[ALL_KEY]:
        if ((get_file_by_param_timestamp(config_pytomo.TEMPLATES_DIR, parameter,
                                        timestamp) is None)
                    or (get_file_by_param_timestamp(config_pytomo.RRD_PLOT_DIR,
                                        parameter, timestamp) is None)):
            return False
    for parameter in chain(ALL_PLOTS.keys(), [LINKS_KEY, DB_KEY]):
        if (get_file_by_param_timestamp(config_pytomo.TEMPLATES_DIR, parameter,
                                        timestamp) is None):
            return False
    return True

def write_database_archive(f_index, db_dir):
    ''' Write the list of databases from db_dir in the html template.
    '''
    # if a history of plots needs to be kept, the existent databases are
    # displayed with links that represent parameters;
    # in web.py the parameters can be retrieved as mentioned in:
    # http://webpy.org/cookbook/input
    f_index.write(' ' * NR_INNER_SPACES + BR_TAG + END_LINE)
    # the column header
    f_index.write((' ' * NR_INNER_SPACES + HEADER_TAG + END_LINE) % DB_KEY)
    # the list of databases
    # the start of the list of links
    f_index.write(' ' * NR_INNER_SPACES + UL_NOSTYLE_START_TAG + END_LINE)
    # the links
    for database in get_specific_files(db_dir, DB_EXTENSION):
        # function is called from pytomo directory, the image dir is
        # subfolder of parent directory
        f_index.write((' ' * NR_INNER_SPACES + LI_START_TAG + A_TAG +
                       END_LINE) % (MAIN_KEY + DB_INPUT + database,
                                    os.path.basename(database)))
        f_index.write(' ' * NR_INNER_SPACES + LI_END_TAG + END_LINE)
    # the end of the list of databases
    f_index.write(' ' * NR_INNER_SPACES + UL_END_TAG + END_LINE)

def write_middle_column(f_index, timestamp, links, db_dir, *parameters):
    ''' Function to write the header and contents of the middle column - plots
    for the *parameters or the table with the links to the videos downloaded
    '''
    # TODO: temporary, write the column div outside to also put the pdf path
    # the column div
    #f_index.write((' ' * NR_DIV_SPACES + DIV_START_TAG + END_LINE) %
    #                                                        MID_COL_NAME)
    # if only the database archive is displayed
    if parameters[0] == DB_KEY:
        write_database_archive(f_index, db_dir)
        # the column div
        f_index.write(' ' * NR_DIV_SPACES + DIV_END_TAG + END_LINE)
        return
    # if there are not enough records in the db to display plots
    if not timestamp and parameters[0] != DB_KEY:
        # the column header
        f_index.write((' ' * NR_INNER_SPACES + HEADER_TAG + END_LINE) %
                                                            MID_COL_HEADER)
        f_index.write((' ' * NR_INNER_SPACES + P_TAG + END_LINE) %
                            DB_NO_RECORDS_MSG)
        # the column div
        f_index.write(' ' * NR_DIV_SPACES + DIV_END_TAG + END_LINE)
        return
    # the column header
    f_index.write((' ' * NR_INNER_SPACES + HEADER_TAG + END_LINE) %
                                                            MID_COL_HEADER)
    # check which graphs to display
    if parameters[0] not in [LINKS_KEY, DB_KEY]:
        param_to_display = parameters
    else:
        param_to_display = ALL_PLOTS[MAIN_KEY]
    # the middle column consists of plots for the parameters
    # the graphs
    for parameter in param_to_display:
        f_index.write(' ' * NR_INNER_SPACES + BR_TAG + END_LINE)
        # function is called from pytomo directory, the image dir is
        # a subfolder of parent directory
        f_index.write((' ' * NR_INNER_SPACES + IMG_TAG + END_LINE) %
                 (plot_path_to_write_in_html(parameter, timestamp), parameter))
        f_index.write((' ' * NR_INNER_SPACES + P_TAG + END_LINE) %
                    MAN_PLOTS[parameter])
        f_index.write(' ' * NR_INNER_SPACES + BR_TAG + END_LINE)
    if parameters[0] == LINKS_KEY:
        # the middle column consists of the main plots and a table with links to
        # the crawled videos
        # table div
        f_index.write(' ' * NR_INNER_SPACES + TABLE_START_TAG + END_LINE)
        # tr
        f_index.write(' ' * NR_INNER_SPACES + TR_START_TAG + END_LINE)
        # table header
        for parameter in MIDDLE_COL_TABLE_HEADER:
            f_index.write((' ' * NR_INNER_SPACES + TH_TAG_ALIGNED + END_LINE) %
                                                                parameter)
        # tr
        f_index.write(' ' * NR_INNER_SPACES + TR_END_TAG + END_LINE)
        # table contents
        for (url, url_cache, service, timestamp) in links:
            # tr
            f_index.write(' ' * NR_INNER_SPACES + TR_START_TAG + END_LINE)
            # td for each column in a row
            f_index.write(' ' * NR_INNER_SPACES + TD_START_TAG_ALIGNED +
                    timestamp[:MAX_TIMESTAMP_LENGTH] + TD_END_TAG + END_LINE)
            f_index.write((' ' * NR_INNER_SPACES + TD_START_TAG_ALIGNED + A_TAG
                           + TD_END_TAG + END_LINE) % (url, url))
            f_index.write((' ' * NR_INNER_SPACES + TD_START_TAG_ALIGNED + A_TAG
                           + TD_END_TAG + END_LINE) % (url_cache, url_cache))
            # tr
            f_index.write(' ' * NR_INNER_SPACES + TR_END_TAG + END_LINE)
        # table div
        f_index.write(' ' * NR_INNER_SPACES + TABLE_END_TAG + END_LINE)
    # the column div
    f_index.write(' ' * NR_DIV_SPACES + DIV_END_TAG + END_LINE)

def write_left_column(f_index, database):
    ''' Function to write the header and contents of the left column - links
    '''
    # the column div
    f_index.write((' ' * NR_DIV_SPACES + DIV_START_TAG + END_LINE) %
                                                            LEFT_COL_NAME)
    # the column header
    f_index.write((' ' * NR_INNER_SPACES + HEADER_TAG + END_LINE) %
                                                            LEFT_COL_HEADER)
    # the start of the list of links
    f_index.write(' ' * NR_INNER_SPACES + UL_START_TAG + END_LINE)
    # the links
    for parameter in sorted(ALL_PLOTS.keys()):
        # function is called from pytomo directory, the image dir is subfolder
        # of parent directory
        f_index.write((' ' * NR_INNER_SPACES + LI_START_TAG + A_TAG +
                        UL_START_TAG + END_LINE) % (parameter + DB_INPUT +
                                                    database, parameter))
        # all the parameters are already present in the other keys
        if parameter != ALL_KEY and parameter != MAIN_KEY:
            for mapping in ALL_PLOTS[parameter]:
                f_index.write((' ' * NR_INNER_SPACES + LI_START_TAG + A_TAG +
                    LI_END_TAG + END_LINE) % (mapping + DB_INPUT + database,
                                              mapping))
        f_index.write(' ' * NR_INNER_SPACES + UL_END_TAG + LI_END_TAG +
                      END_LINE)
    # the link to the table that displays the links to the crawled videos
    f_index.write(' ' * NR_INNER_SPACES + BR_TAG + END_LINE)
    f_index.write((' ' * NR_INNER_SPACES + A_TAG + END_LINE) %
                  (LINKS_KEY + DB_INPUT + database, LINKS_KEY))
    # the link to the list that displays the existent database archive
    f_index.write(' ' * NR_INNER_SPACES + BR_TAG + END_LINE)
    f_index.write(' ' * NR_INNER_SPACES + BR_TAG + END_LINE)
    f_index.write((' ' * NR_INNER_SPACES + A_TAG +  END_LINE) %
                  (DB_KEY + DB_INPUT + database, DB_KEY))
    # the link to the project documentation index
    f_index.write(' ' * NR_INNER_SPACES + BR_TAG + END_LINE)
    f_index.write(' ' * NR_INNER_SPACES + BR_TAG + END_LINE)
    f_index.write((' ' * NR_INNER_SPACES + A_TAG + END_LINE) %
                (config_pytomo.DOC_DIR + config_pytomo.TEMPLATE_FILE, DOC_KEY))
    # the link to the pdf gen
    f_index.write(' ' * NR_INNER_SPACES + BR_TAG + END_LINE)
    f_index.write(' ' * NR_INNER_SPACES + BR_TAG + END_LINE)
    # the end of the list of links
    f_index.write(' ' * NR_INNER_SPACES + UL_END_TAG + END_LINE)
    # the column div
    f_index.write(' ' * NR_DIV_SPACES + DIV_END_TAG + END_LINE)

def write_right_column(f_index, average_values):
    ''' Function to write the header and contents of the right column - tables
    containing the average values determined by the crawl and the list of
    existent databases.
    '''
    if not average_values:
        config_pytomo.LOG.debug('No data has been received to create the table')
        return
    # the column div
    f_index.write((' ' * NR_DIV_SPACES + DIV_START_TAG + END_LINE) %
                                                            RIGHT_COL_NAME)
    # the column header
    f_index.write((' ' * NR_INNER_SPACES + HEADER_TAG + END_LINE) %
                                                            RIGHT_COL_HEADER)
    # the table including the average parameters
    # table div
    f_index.write(' ' * NR_INNER_SPACES + TABLE_START_TAG + END_LINE)
    # tr
    f_index.write(' ' * NR_INNER_SPACES + TR_START_TAG + END_LINE)
    # table header
    for header in RIGHT_COL_TABLE_HEADER:
        f_index.write((' ' * NR_INNER_SPACES + TH_TAG + END_LINE) % header)
    # tr
    f_index.write(' ' * NR_INNER_SPACES + TR_END_TAG + END_LINE)
    # table contents
    for parameter, value in zip(AVERAGE_PARAM_DESCRIPTION, average_values):
        # tr
        f_index.write(' ' * NR_INNER_SPACES + TR_START_TAG + END_LINE)
        # td
        f_index.write(' ' * NR_INNER_SPACES + TD_START_TAG + parameter +
                    TD_END_TAG + END_LINE)
        f_index.write(' ' * NR_INNER_SPACES + TD_START_TAG + str(value) +
                    TD_END_TAG + END_LINE)
        # tr
        f_index.write(' ' * NR_INNER_SPACES + TR_END_TAG + END_LINE)
    # table div
    f_index.write(' ' * NR_INNER_SPACES + TABLE_END_TAG + END_LINE)
    # the column div
    f_index.write(' ' * NR_DIV_SPACES + DIV_END_TAG + END_LINE)

def write_end_div_refresh(f_index, database):
    # the column div colleft
    f_index.write(' ' * NR_DIV_SPACES + DIV_END_TAG + END_LINE)
    # the column div colmid
    f_index.write(' ' * NR_DIV_SPACES + DIV_END_TAG + END_LINE)
    # the column div colmask threecol
    f_index.write(' ' * NR_DIV_SPACES + DIV_END_TAG + END_LINE)
    # if the database was modified recently, should refresh page
    if (time.time() - os.path.getmtime(database)) < REFRESH_TIMEOUT:
        f_index.write(ONLOAD_REFRESH_SCRIPT)

def write_index(timestamp, database, db_dir=config_pytomo.DATABASE_DIR):
    ''' Function to create the parameter_timestamp_index.html from template
    files and include the images that also contain a specific timestamp.
    '''
    # if database is not empty
    if timestamp:
        # get the data from the database
        # retrieve data on which average parameters and video links depend on
        try:
            avg_data = lib_database.PytomoDatabase(database).\
                                        fetch_all_parameters(AVERAGE_PARAM)
        except Error, mes:
            config_pytomo.LOG.error('Unable to extract data %s with error:'
                                    '%s' % (str(AVERAGE_PARAM), mes))
        try:
            links_data = lib_database.PytomoDatabase(database).\
                                        fetch_all_parameters(URL_PARAM)
            # assumes all crawled links are from the same service (hardcoded)
            SERVICE = links_data[0][SERVICE_POS_IN_URL]
        except Error, mes:
            config_pytomo.LOG.error('Unable to extract data %s with error:'
                                    '%s' % (str(URL_PARAM), mes))
    else:
        links_data = None
        avg_data = None
    # open all the file descriptors
    try:
        f_s_template = open(os.path.join(config_pytomo.TEMPLATES_DIR,
                                         START_TEMPLATE_NAME), 'r')
    except IOError:
        config_pytomo.LOG.error('Problem opening file %s' %
                            os.path.join(config_pytomo.TEMPLATES_DIR,
                                         START_TEMPLATE_NAME))
        return
    try:
        f_e_template = open(os.path.join(config_pytomo.TEMPLATES_DIR,
                                         END_TEMPLATE_NAME), 'r')
    except IOError:
        config_pytomo.LOG.error('Problem opening file %s' %
                                os.path.join(config_pytomo.TEMPLATES_DIR,
                                             END_TEMPLATE_NAME))
        return
    # create a different index.html for each parameter, with specific timestamp
    # first the elements in ALL_PLOTS.keys()
    # then the elements in UNITS.keys()
    # then LINKS_KEY, DB_KEY
    f_param = []
    for param in chain(ALL_PLOTS.keys(), ALL_PLOTS[ALL_KEY],
                       [LINKS_KEY, DB_KEY]):
        try:
            f_name = index_filename(param, timestamp)
        except IOError:
            config_pytomo.LOG.error('Problem opening index file for parameter'
                                    ' %s' % param)
            return
        f_index = open(f_name, 'w')
        f_param.append(f_index)
    # retrieve the header lines
    header_lines = f_s_template.readlines()
    # retrieve the footer lines
    footer_lines = f_e_template.readlines()
    # add the style and header of the page to each index
    for f_index in f_param:
        for line in header_lines:
            f_index.write(line)
    if timestamp:
        avg_values = tuple(chain(*((SERVICE,),
                                   compute_average_values(avg_data))))
    # add the body of the page
    # middle column - plots or table with the links to crawled videos or
    # database archive
    # parameter represents either a list (a key in the dictionary ALL_PLOTS),
    # a single parameter that can be plotted or the LINKS_KEY / DB_KEY
    # if anything else is given, the main graphs are plotted
    for parameter, f_index in \
                        zip(ALL_PLOTS.keys(), f_param[:len(ALL_PLOTS.keys())]):
        # TODO: must be moved back to middle column
        # the middle column div
        f_index.write((' ' * NR_DIV_SPACES + DIV_START_TAG + END_LINE) %
                                                                MID_COL_NAME)
        if timestamp:
            # TODO: function is not properly checked, this must be removed
            try:
                pdf_name = pdf_filename(parameter, timestamp)
                rel_pdf_name = HTTP_CONNECTOR.join((config_pytomo.PDF_DIR,
                                            os.path.basename(pdf_name)))
                create_pdf(pdf_name, timestamp, avg_values,
                           *ALL_PLOTS[parameter])
                f_index.write((' ' * NR_INNER_SPACES + P_TAG + END_LINE) %
                              PDF_MSG)
                f_index.write((' ' * NR_INNER_SPACES + A_TAG + END_LINE) %
                              (rel_pdf_name, rel_pdf_name))
            except Exception, mes:
                config_pytomo.LOG.error('Could not create PDF, error: %s' % mes)
        write_middle_column(f_index, timestamp, links_data, db_dir,
                            *ALL_PLOTS[parameter])
    for parameter, f_index in zip(chain(ALL_PLOTS[ALL_KEY],
                        [LINKS_KEY, DB_KEY]), f_param[len(ALL_PLOTS.keys()):]):
        # TODO: must be moved back to middle column
        # the middle column div
        f_index.write((' ' * NR_DIV_SPACES + DIV_START_TAG + END_LINE) %
                                                                MID_COL_NAME)
        if timestamp:
            # TODO: function is not properly checked, this must be removed
            try:
                pdf_name = pdf_filename(parameter, timestamp)
                rel_pdf_name = HTTP_CONNECTOR.join((config_pytomo.PDF_DIR,
                                            os.path.basename(pdf_name)))
                create_pdf(pdf_name, timestamp, avg_values, parameter)
                f_index.write((' ' * NR_INNER_SPACES + P_TAG + END_LINE) %
                              PDF_MSG)
                f_index.write((' ' * NR_INNER_SPACES + A_TAG + END_LINE) %
                              (rel_pdf_name, rel_pdf_name))
            except Exception, mes:
                config_pytomo.LOG.error('Could not create PDF, error: %s' % mes)
        write_middle_column(f_index, timestamp, links_data, db_dir, parameter)
    # add the left, right columns and the footer to each index
    for f_index in f_param:
        # left column - links to plots
        write_left_column(f_index, database)
        # right column - average values
        if timestamp:
            write_right_column(f_index, avg_values)
        # check if page should be automatically refreshed
        write_end_div_refresh(f_index, database)
        # add the footer of the page
        for line in footer_lines:
            f_index.write(line)
        # close the file object
        f_index.close()
    f_s_template.close()
    f_e_template.close()

def compute_average_values(data):
    '''Function to return a tuple (start_crawl_time, end_crawl_time,
    nr_videos, average_ping, average_download_time,
    average_download_interruptions)
    '''
    # data is retrieved sorted from the database
    start_crawl_time = data[0][TIMESTAMP_POSITION]\
                        [:MAX_TIMESTAMP_LENGTH]
    end_crawl_time = data[-1][TIMESTAMP_POSITION]\
                        [:MAX_TIMESTAMP_LENGTH]
    # total crawl time (sync time is added at the beginning and end for
    # the plots)
    total_time = (datetime.fromtimestamp(lib_database.time_to_epoch(
                                    data[-1][TIMESTAMP_POSITION])) -
                  datetime.fromtimestamp(lib_database.time_to_epoch(
                                    data[0][TIMESTAMP_POSITION])))
    # each row in the dataset represents a video
    nr_videos = len(data)
    # filter values that are not None (can be zero)
    not_none = lambda x: x is not None
    # for some videos data cannot be retrieved
    # average download time represents the average of DownloadTime
    average_list = filter(not_none,
                    map(itemgetter(AVERAGE_PARAM.index('DownloadTime')), data))
    average_download_time = average(average_list, len(average_list))
    # average download interruptions represents the average of
    # DownloadInterruptions
    average_list = filter(not_none, map(itemgetter(
                        AVERAGE_PARAM.index('DownloadInterruptions')), data))
    average_download_interruptions = average(average_list, len(average_list))
    # average ping represents the average of PingAvg
    average_list = filter(not_none, map(itemgetter(
                            AVERAGE_PARAM.index('PingAvg')), data))
    average_ping = average(average_list, len(average_list))
    return (total_time, start_crawl_time,
            end_crawl_time, nr_videos, average_download_time,
            average_download_interruptions, average_ping)

def average(values, known_values):
    ''' Computes the arithmetic mean of a list of numbers.
    >>> average([20, 30, 70], 3)
    40.0
    >>> average([], 0)
    nan
    '''
    return round((float(sum(values)) / known_values
                if known_values else float('nan')), AVERAGE_PRECISION)

def logger_io():
    '''Initialze the logger'''
    config_pytomo.LOG = logging.getLogger('pytomo_io')
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
            return 1
        handler = logging.FileHandler(filename=log_file)
    log_formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                  "%(levelname)s - %(message)s")
    handler.setFormatter(log_formatter)
    config_pytomo.LOG.addHandler(handler)

def main(argv=None):
    "Program wrapper"
    if argv is None:
        argv = sys.argv[1:]
    usage = ("%prog [-v] database")
    parser = OptionParser(usage=usage)
    # to run the doctest
    parser.add_option('-v', '--verbose', dest = 'verbose',
            action = 'store_true', default = False, help = 'verbose')
    (options, args) = parser.parse_args(argv)
    # Intialize the logger for standalone testing Logging
    if not config_pytomo.LOG:
        logger_io()
    if options.verbose:
        config_pytomo.LOG.setLevel(logging.DEBUG)
        config_pytomo.LOG_FILE = '-'
    return 0

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    sys.exit(main())
