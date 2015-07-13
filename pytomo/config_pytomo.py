#!/usr/bin/env python

"""The config file for the pytomo setup
Lines starting with # are comments
"""

from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

# use package directory for storing files
# put it False if you want files in the current working dir (from where pytomo
# is launched)
USE_PACKAGE_DIR = False

# execute crawl without prompting user for any parameters
# put to True if you are running jobs automatically
BATCH_MODE = False

#PROVIDER = None
PROVIDER = ''

RESULT_DIR = 'results'
RESULT_FILE = None
#RESULT_FILE = 'pytomo.result'

DATABASE_DIR = 'databases'
DATABASE = 'pytomo_database.db'
# DO NOT USE ANY . OR - IN THE TABLE NAME
TABLE = 'pytomo_crawl'

LOG_DIR = 'logs'
# log file use '-' for standard output
LOG_FILE = 'pytomo.log'
#LOG_FILE = '-'

# log level
# choose from: DEBUG, INFO, WARNING, ERROR and CRITICAL
LOG_LEVEL = DEBUG

# log the public IP address
LOG_PUBLIC_IP = True

# send the archive with the database and logs to the centralisation server
CENTRALISE_DATA = False
CENTRALISATION_SERVER = 'pytomo.dtdns.net'

# loop on input links
LOOP = False
#LOOP = True

# take related links
#RELATED = True
RELATED = False

# Image file to save the graphs
PLOT = False
 # List containig the column names to be plotted
COLUMN_NAMES = ['DownloadBytes', 'MaxInstantThp']
# Choose from  [ PingMin , PingAvg , PingMax , DownloadTime, VideoDuration
# VideoLength, EncodingRate, DownloadBytes, DownloadInterruptions,
# BufferingDuration, PlaybackDuration, BufferDurationAtEnd, MaxInstantThp]

IMAGE_FILE = 'pytomo_image.png'
IMAGE_DIR = 'plots'

# directories used by the graphical interface
RRD_FILE = 'pytomo.rrd'
RRD_DIR = 'rrds'
RRD_PLOT_DIR = 'images'
TEMPLATE_FILE = 'index.html'
TEMPLATES_DIR = 'templates'
DOC_DIR = 'templates/doc/'
PDF_FILE = 'report.pdf'
PDF_DIR = 'pdfs'
# graphical interface default port to run on
WEB_DEFAULT_PORT = '5555'


STD_HEADERS = {
    'Accept-Language': 'en-us,en;q=0.5',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:10.0) \
    Gecko/20100101 Firefox/10.0',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Cookie': 'YSC=h9wy7hcXxIo; VISITOR_INFO1_LIVE=d5TlLfzb2K0; PREF=f1=50000000; s_gl=1d69aac621b2f9c0a25dade722d6e24bcwIAAABVUw=='
}


################################################################################
# for start_pytomo.py

STATIC_URL_LIST = []
INPUT_FILE = None

# Max number of rounds to perform
MAX_ROUNDS = 10000
MAX_CRAWLED_URLS = 10000
# Max number of related videos from each url
MAX_PER_URL = 10
# Max number of related videos from each page
MAX_PER_PAGE = 10

# timeframe for the most popular videos fetch at start of crawl
# put 'today', 'week', 'month' or 'all_time' (default case)
# new API: only today and all_time are allowed
TIME_FRAME = 'today'

#Time delay between consecutive url crawls and download requests (in seconds)
DELAY_BETWEEN_REQUESTS = 10
# Max duration of round for getting input links
MAX_ROUND_DURATION = 600

IPADDR_TIMEOUT = 5
URL_TIMEOUT = 5
AS_URL_TIMEOUT = 15

# choose between 'youtube' and 'dailymotion'
CRAWL_SERVICE = 'youtube'


################################################################################
# for lib_cache_url.py
# proxy to set at command line
PROXIES = None
# replace with your values
#PROXIES = {'http': 'http://www.example.com:3128/'}

# cookie file
#cookie_file = 'cookie.jar'

################################################################################
# for lib_dns.py

# other DNS servers to query
GOOGLE_PUBLIC_DNS = ('google_public_dns', '8.8.8.8')
OPEN_DNS = ('open_dns', '208.67.220.220')
# The lifetime of a DNS query(in seconds). The default is 30 seconds.
DNS_TIMEOUT = 4.0
EXTRA_NAME_SERVERS = [GOOGLE_PUBLIC_DNS, OPEN_DNS]
#EXTRA_NAME_SERVERS = []
# also download video from IPs resolved by other DNS servers
DOWNLOAD_FROM_EXTRA_IPS = False

# just for sharing the servers between the modules
EXTRA_NAME_SERVERS_CC = []

# HTTP codes to check for redirects.
HTTP_REDIRECT_MULTIPLE_CHOICES = 300
HTTP_REDIRECT_MOVED_PERMANENTLY = 301
HTTP_REDIRECT_FOUND = 302
HTTP_REDIRECT_SEE_OTHER = 303
HTTP_REDIRECT_NOT_MODIFIED = 304
HTTP_REDIRECT_USE_PROXY = 305
HTTP_REDIRECT_SWITCH_PROXY = 306
HTTP_REDIRECT_TEMPORARY_REDIRECT = 307
HTTP_REDIRECT_PERMANENT_REDIRECT = 308
#HTTP_REDIRECT_CODE = 302
HTTP_OK = 200
MAX_NB_REDIRECT = 10
HTTP_REDIRECT_CODE_LIST = (
    HTTP_REDIRECT_MULTIPLE_CHOICES,
    HTTP_REDIRECT_MOVED_PERMANENTLY,
    HTTP_REDIRECT_FOUND,
    HTTP_REDIRECT_SEE_OTHER,
    HTTP_REDIRECT_NOT_MODIFIED,
    HTTP_REDIRECT_USE_PROXY,
    HTTP_REDIRECT_SWITCH_PROXY,
    HTTP_REDIRECT_TEMPORARY_REDIRECT,
    HTTP_REDIRECT_PERMANENT_REDIRECT,
)

################################################################################
# for lib_ping.py
# nb of packets to send for ping stats
PING_PACKETS = 10

################################################################################
# for lib_youtube_download.py
DOWNLOAD_TIME = 30.0
FREQ_FULL_DOWNLOAD = None
#FREQ_FULL_DOWNLOAD = 40
MAX_DOWNLOAD_TIME = 600.0
INITIAL_BUFFER = 2.0
MIN_PLAYOUT_BUFFER = 0.1
MIN_PLAYOUT_RESTART = 1.0
# Initial playback buffer duration in milliseconds
INITIAL_PLAYBACK_DURATION = 2000

# nb of tries for extracting metadata info from video
MAX_NB_TRIES_ENCODING = 9

# demo mode!
DEMO = False

EXTRA_COUNTRY = None
# for Tunisia
#EXTRA_COUNTRY = 'TN'
# for France
#EXTRA_COUNTRY = 'FR'

#high definition
HD_FIRST = False

################################################################################
# for snmp
SNMP = False
ROOT_OID = '.1.3.6.1.3.53.5.9'

# Table of global stats
snmp_pytomoGblStats = '.'.join((ROOT_OID, '1'))

snmp_pytomoObjectName = '.'.join((snmp_pytomoGblStats, '1'))
snmp_pytomoObjectName_str = 'Pytomo instance'
snmp_pytomoDescr = '.'.join((snmp_pytomoGblStats, '2'))
snmp_pytomoDescr_str = ('Pytomo  is a YouTube crawler designed to figure out '
                        'network information out of YouTube video download')
snmp_pytomoContact = '.'.join((snmp_pytomoGblStats, '3'))
snmp_pytomoContact_str = 'Jean-Luc Sire / Pascal Beringuie '
snmp_pytomoDownloadDuration = '.'.join((snmp_pytomoGblStats, '4'))
snmp_pytomoSleepTime = '.'.join((snmp_pytomoGblStats, '5'))

# Table of Url stats
snmp_pytomoUrlStats = '.'.join((ROOT_OID, '2', '1', '1'))

# UrlIndex is the first value in the tables but not in the stats!
snmp_pytomoUrlIndex = '.'.join((snmp_pytomoUrlStats, '1'))
snmp_pytomoTimeStamp = '.'.join((snmp_pytomoUrlStats, '2'))
snmp_pytomoService = '.'.join((snmp_pytomoUrlStats, '3'))
snmp_pytomoCacheUrl = '.'.join((snmp_pytomoUrlStats, '4'))
snmp_pytomoCacheServerDelay = '.'.join((snmp_pytomoUrlStats, '5'))
snmp_pytomoAddressIp = '.'.join((snmp_pytomoUrlStats, '6'))
snmp_pytomoResolver = '.'.join((snmp_pytomoUrlStats, '7'))
snmp_pytomoResolveTime = '.'.join((snmp_pytomoUrlStats, '8'))
snmp_pytomoAsNumber = '.'.join((snmp_pytomoUrlStats, '9'))
snmp_pytomoPingMin = '.'.join((snmp_pytomoUrlStats, '10'))
snmp_pytomoPingAvg = '.'.join((snmp_pytomoUrlStats, '11'))
snmp_pytomoPingMax = '.'.join((snmp_pytomoUrlStats, '12'))
snmp_pytomoDownloadTime = '.'.join((snmp_pytomoUrlStats, '13'))
snmp_pytomoVideoType = '.'.join((snmp_pytomoUrlStats, '14'))
snmp_pytomoVideoDuration = '.'.join((snmp_pytomoUrlStats, '15'))
snmp_pytomoVideoLength = '.'.join((snmp_pytomoUrlStats, '16'))
snmp_pytomoEncodingRate = '.'.join((snmp_pytomoUrlStats, '17'))
snmp_pytomoDownloadBytes = '.'.join((snmp_pytomoUrlStats, '18'))
snmp_pytomoDownloadInterruptions = '.'.join((snmp_pytomoUrlStats, '19'))
snmp_pytomoInitialData = '.'.join((snmp_pytomoUrlStats, '20'))
snmp_pytomoInitialRate = '.'.join((snmp_pytomoUrlStats, '21'))
snmp_pytomoInitialPlaybackBuffer = '.'.join((snmp_pytomoUrlStats, '22'))
snmp_pytomoBufferingDuration = '.'.join((snmp_pytomoUrlStats, '23'))
snmp_pytomoPlaybackDuration = '.'.join((snmp_pytomoUrlStats, '24'))
snmp_pytomoBufferDurationAtEnd = '.'.join((snmp_pytomoUrlStats, '25'))
snmp_pytomoTimeTogetFirstByte = '.'.join((snmp_pytomoUrlStats, '26'))
snmp_pytomoMaxInstantThp = '.'.join((snmp_pytomoUrlStats, '27'))
snmp_pytomoRedirectUrl = '.'.join((snmp_pytomoUrlStats, '28'))
snmp_pytomoStatusCode = '.'.join((snmp_pytomoUrlStats, '29'))

#Statistics by ip
snmp_pytomoIpStats = '.'.join((ROOT_OID, '3', '1', '1'))
snmp_pytomoIpName = '.' .join((snmp_pytomoIpStats,'1'))
snmp_pytomoIpCount = '.' .join((snmp_pytomoIpStats,'2'))

#Statistics by AS
snmp_pytomoASStats = '.'.join((ROOT_OID, '4', '1', '1'))
snmp_pytomoASName = '.'.join((snmp_pytomoASStats,'1'))
snmp_pytomoASCount = '.'.join((snmp_pytomoASStats,'2'))





URL_IDX = 2
TS_IDX = 0
IP_IDX = 5
AS_IDX = 8
STATS_IDX = (
    2, #Url
    0, #TIMESTAMP
    1, #Service
    3, #CacheUrl
    4, #CacheServerDelay
    5, #IP
    6, #Resolver
    7, #ResolveTime
    8, #ASNumber
    9, #PingMin
    10, #PingAvg
    11, #PingMax
    12, #DownloadTime
    13, #VideoType
    14, #VideoDuration
    15, #VideoLength
    16, #EncodingRate
    17, #DownloadBytes
    18, #DownloadInterruptions
    19, #InitialData
    20, #InitialRate
    21, #InitialPlaybackBuffer
    22, #BufferingDuration
    23, #PlaybackDuration
    24, #BufferDurationAtEnd
    25, #TimeTogetFirstByte
    26, #MaxInstantThp
    27, #RedirectUrl
    28, #StatusCode
)

################################################################################
################################################################################
# to be set by start_pytomo.py: DO NOT CHANGE
LOG = None
LOG_FILE_TIMESTAMP = None
DATABASE_TIMESTAMP = None
TABLE_TIMESTAMP = None
SYSTEM = None
RTT = None
DOWNLOADED_BY_IP = {}
DOWNLOADED_BY_AS = {}


SEP_LINE = 80 * '#'
NB_IDENT_VALUES = 8
NB_PING_VALUES = 3
NB_DOWNLOAD_VALUES = 15
NB_RELATED_VALUES = 2
NB_FIELDS = (NB_IDENT_VALUES + NB_PING_VALUES + NB_DOWNLOAD_VALUES
             + NB_RELATED_VALUES)

USER_INPUT_TIMEOUT = 10
CRAWLED_URLS_MODULO = 5

LEVEL_TO_NAME = {DEBUG: 'DEBUG',
                 INFO: 'INFO',
                 WARNING: 'WARNING',
                 ERROR: 'ERROR',
                 CRITICAL: 'CRITICAL'}

NAME_TO_LEVEL = {'DEBUG': DEBUG,
                 'INFO': INFO,
                 'WARNING': WARNING,
                 'ERROR': ERROR,
                 'CRITICAL': CRITICAL}

# set for NOT computing stats on already seen IP addresses
SKIP_COMPUTED = False

################################################################################
# black list utils

BLACK_LISTED = 'das_captcha'

class BlackListException(Exception):
    "Exception in case the crawler has been blacklisted"
    pass

