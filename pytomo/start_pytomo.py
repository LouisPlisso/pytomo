#!/usr/bin/env python
'''
Module to launch a crawl.
This module supplies the following functions that can be used
independently:
    1. compute_stats: To calculate the download statistics of a URL.

    Usage:
        To use the functions provided in this module independently,
        first place yourself just above pytomo folder.Then:

import pytomo.start_pytomo as start_pytomo
import pytomo.config_pytomo as config_pytomo
config_pytomo.LOG_FILE = '-'
import time
timestamp = time.strftime('%Y-%m-%d.%H_%M_%S')
log_file = start_pytomo.configure_log_file(timestamp)
import platform
config_pytomo.SYSTEM = platform.system()
url = 'http://youtu.be/3VdOTTfSKyM'
start_pytomo.compute_stats(url)
# test Dailymotion
url = 'http://www.dailymotion.com/video/xscdm4_le-losc-au-pays-basque_sport?no_track=1'

import pytomo.start_pytomo as start_pytomo
import pytomo.config_pytomo as config_pytomo
config_pytomo.LOG_FILE = '-'
import time
timestamp = time.strftime('%Y-%m-%d.%H_%M_%S')
log_file = start_pytomo.configure_log_file(timestamp)
import platform
config_pytomo.SYSTEM = platform.system()

# video delivered by akamai CDN
url = 'http://www.dailymotion.com/video/xp9fq9_test-video-akamai_tech'
start_pytomo.compute_stats(url)
# redirect url: do not work
url = 'http://vid.ak.dmcdn.net/video/986/034/42430689_mp4_h264_aac.mp4?primaryToken=1343398942_d77027d09aac0c5d5de74d5428fb9e5b'
start_pytomo.compute_stats(url, redirect=True)

# video delivered by edgecast CDN
url = 'http://www.dailymotion.com/video/xmcyww_test-video-cell-edgecast_tech'
start_pytomo.compute_stats(url)
url = 'http://vid.ec.dmcdn.net/cdn/H264-512x384/video/xmcyww.mp4?77838fedd64fa52abe6a11b3bdbb4e62f4387ebf7cbce2147ea4becc5eee5c418aaa6598bb98a61fc95a02997247e59bfb0dcd58cdf05c1601ded04f75ae357b225da725baad5e97ea6cce6d6a12e17d1c01'
start_pytomo.compute_stats(url, redirect=True)

# video delivered by dailymotion servers
url = 'http://www.dailymotion.com/video/xmcyw2_test-video-cell-core_tech'
start_pytomo.compute_stats(url)
url = 'http://proxy-60.dailymotion.com/video/246/655/37556642_mp4_h264_aac.mp4?auth=1343399602-4098-bdkyfgul-eb00ad223e1964e40b327d75367b273b'
start_pytomo.compute_stats(url, redirect=True)

'''

from __future__ import with_statement, absolute_import, print_function

import sys
from urlparse import urlsplit
from pprint import pprint
import logging
import datetime
from time import strftime, timezone
import os
from string import maketrans, lowercase
from optparse import OptionParser
import hashlib
import socket
import urllib2
import platform
import signal
import time
from os.path import abspath, dirname, sep
from sys import path
import tarfile
import re
from operator import concat, itemgetter, eq
from sqlite3 import Error
#from ast import literal_eval
import json

# assumes the standard distribution paths
PACKAGE_DIR = dirname(abspath(path[0]))

#PUBLIC_IP_FINDER = 'http://automation.whatismyip.com/n09230945.asp'
#PUBLIC_IP_FINDER = 'http://ipogre.com/linux.php'
PUBLIC_IP_FINDER = r'http://stat.ripe.net/data/whats-my-ip/data.json'
AS_REQUEST_URL = r'http://stat.ripe.net/data/routing-status/data.json?resource='
# to store the request on /24 prefixes
CACHED_PREFIXES = dict()
# give a default fake value for convenience
CACHED_PREFIXES['0.0.0'] = 0

IP_MATCH_PATTERN = ('^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}'
                    '([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$')
SEPARATOR_LINE = '#' * 80
YOUTUBE_SERVICE = 'youtube'
DAILYMOTION_SERVICE = 'dailymotion'
GALERIE_VIDEO_SERVICE = 'galerievideo.orange-business.com'
CONTINUOUS_CRAWL_SIZE = 10
PARAM_URL = 'Url'
#REDIRECT_CACHE_URL_PATTERN = '.youtube.com/videoplayback?sparams=id'

# initial cache url regex
#CACHE_URL_REGEXP = re.compile(r'(http://o-o---preferred---sn-)(\w{8})'
#                              '(---v\d{1,2}---lscache\d.c.youtube.com)')
# updated
# direct cache *o-o---preferred* or redirect *rXX*
# *---*
# *sn-* - will be omitted in the decrypted url
# something like *25g7rn7r* or *vg5obx-hgne*
# direct cache have *---vXX---lscacheX*
# *.c.youtube.com*
CACHE_URL_REGEXP = re.compile(r'(http://)(o-o---preferred|r\d{1,2})(---)(sn-)'
                              r'(\w{6}-\w{4}|(?:-|\w{8}))(---v\d{1,2}---lscache\d){0,1}'
                              r'(.c.youtube.com)')
TRANSLATION = maketrans(''.join(map(str, range(10))) + lowercase,
                               'uzpkfa50vqlgb61wrmhc72xsnid83ytoje94')

try:
    from win32com.shell import shell, shellcon
    HOME_DIR = shell.SHGetFolderPath(0, shellcon.CSIDL_PROFILE, None, 0)
except ImportError:
    HOME_DIR = os.path.expanduser('~')

from . import config_pytomo
from . import lib_dns
from . import lib_ping
from . import lib_youtube_download
from . import lib_dailymotion_download
from . import lib_general_download
from . import lib_galerie_download
from . import lib_database
from . import lib_youtube_api
from . import lib_dailymotion_api
from . import lib_links_extractor
from . import lib_data_centralisation
from . import translation_cache_url

if config_pytomo.PLOT:
    from . import lib_plot

# default service is YouTube
SERVICE = 'YouTube'

def select_libraries(url):
    ''' Return the libraries to use for dowloading and retrieving specific
    links'''
    if DAILYMOTION_SERVICE in url or 'dmcdn' in url or 'dmcloud' in url:
        lib_download = lib_dailymotion_download
        lib_api = lib_dailymotion_api
    elif YOUTUBE_SERVICE in url or 'youtu.be' in url:
        lib_download = lib_youtube_download
        lib_api = lib_youtube_api
    elif GALERIE_VIDEO_SERVICE in url:
        lib_download = lib_galerie_download
        lib_api = lib_dailymotion_api
    else:
        config_pytomo.LOG.critical('only YouTube and Dailymotion download '
                                   'are implemented')
        return None
    return (lib_download, lib_api)

#def translate_cache_url(url):
#    ''' Return decrypted cache url name, using monoalphabetic cipher:
#        digits, letters -> uzpkfa50vqlgb61wrmhc72xsnid83ytoje94
#    Assumes all cache servers that match pattern are encrypted, otherwise
#    it returns original address. Unencrypted cache urls still exist, they do
#    not contain *--sn* (http://r3---orange-mrs2.c.youtube.com/).
#    >>> url = 'http://o-o---preferred---sn-25g7rn7k---v18---lscache1.c.youtube.com/'
#    >>> translate_cache_url(url)
#    'http://o-o---preferred---par08s07---v18---lscache1.c.youtube.com'
#    >>> url = 'http://o-o---preferred---sn-vg5obx-hgnl---v16---lscache6.c.youtube.com'
#    >>> translate_cache_url(url)
#    'http://o-o---preferred---orange-mrs2---v16---lscache6.c.youtube.com'
#    >>> url = 'http://r10---sn-25g7rn7l.c.youtube.com/'
#    >>> translate_cache_url(url)
#    'http://r10---par08s02.c.youtube.com'
#    >>> url = 'http://r3---orange-mrs2.c.youtube.com/'
#    >>> translate_cache_url(url)
#    'http://r3---orange-mrs2.c.youtube.com/'
#    >>> url = 'http://r6---sn-5up-u0ol.c.youtube.com'
#    >>> translate_cache_url(url)
#    'http://r6---ati-tun2.c.youtube.com'
#    '''
#    match = CACHE_URL_REGEXP.match(url)
#    config_pytomo.LOG.debug('translating url: %s', url)
#    if not match:
#        config_pytomo.LOG.debug('no match')
#        new_url = url
#    else:
#        groups = match.groups()
#        assert len(groups) == 7
#        groups = filter(None, groups)
#        new_url = (''.join((groups[0:3])) + groups[4].translate(TRANSLATION) +
#                   ''.join((groups[5:])))
#    config_pytomo.LOG.debug('url translated as: %s', new_url)
#    return new_url

def compute_stats(url, cache_uri, do_download_stats, redirect_url=None,
                  do_full_crawl=None):
    '' 'Return a list of the statistics related to the url'''
    if not cache_uri:
        return None
    current_stats = dict()
    # the cache url server where the video is stored
    # <scheme>://<netloc>/<path>?<query>#<fragment>
    parsed_uri = urlsplit(cache_uri)
    cache_url = '://'.join((parsed_uri.scheme, parsed_uri.netloc))
    status_code = None
    if config_pytomo.CRAWL_SERVICE.lower() == YOUTUBE_SERVICE:
        cache_url = translation_cache_url.translate_cache_url(cache_url)
    #cache_urn = '?'.join((parsed_uri.path, parsed_uri.query))
    ip_addresses = lib_dns.get_ip_addresses(parsed_uri.netloc)
    # in case there is a problem in the DNS, for the variables to be bound
    if redirect_url:
        parsed_uri = urlsplit(redirect_url)
        redirect_url = '://'.join((parsed_uri.scheme, parsed_uri.netloc))
        if config_pytomo.CRAWL_SERVICE.lower() == YOUTUBE_SERVICE:
            redirect_url = translation_cache_url.translate_cache_url(
                                                                   redirect_url)
    redirect_list = []
    for (ip_address, resolver, req_time) in ip_addresses:
        config_pytomo.LOG.debug('Compute stats for IP: %s', ip_address)
        timestamp = datetime.datetime.now()
        if ip_address in current_stats and config_pytomo.SKIP_COMPUTED:
            config_pytomo.LOG.debug('Skip IP already crawled: %s',
                                    ip_address)
            continue
        ping_times = lib_ping.ping_ip(ip_address)
        if do_download_stats and ('default' in resolver
                                  or config_pytomo.DOWNLOAD_FROM_EXTRA_IPS):
            (download_stats, new_redirect_url,
             status_code) = compute_download_stats(resolver, ip_address,
                                                   cache_uri, current_stats,
                                                   do_full_crawl=do_full_crawl)
            redirect_list.append(new_redirect_url)
        else:
            download_stats, new_redirect_url = None, None
        if config_pytomo.PROXIES:
            proxy = urllib2.ProxyHandler(config_pytomo.PROXIES)
            opener = urllib2.build_opener(proxy)
            urllib2.install_opener(opener)
        # we do consider only /24 prefixes
        prefix = '.'.join(ip_address.split('.')[0:3])
        if prefix not in CACHED_PREFIXES:
            try:
                # HARD CODED fields of json data
                as_nb = int(json.load(urllib2.urlopen(
                    AS_REQUEST_URL + ip_address,
                timeout=config_pytomo.AS_URL_TIMEOUT))['data']['last_seen']['origin'])
                CACHED_PREFIXES[prefix] = as_nb
                config_pytomo.LOG.debug('IP %s resolved as AS: %d',
                                        ip_address, as_nb)
            except Exception, mes:
                config_pytomo.LOG.exception(mes)
                prefix = '0.0.0'
        if not status_code and redirect_url:
            # should not happen, but guess a 302 in this case
            config_pytomo.LOG.debug('no status code found with this '
                                    'redirect_url: %s', redirect_url)
            status_code = config_pytomo.HTTP_REDIRECT_FOUND
        current_stats[ip_address] = [timestamp, ping_times, download_stats,
                                     redirect_url, resolver, req_time,
                                     CACHED_PREFIXES[prefix], status_code]
    # check if cache_url is the same independently of DNS: YES only depend on
    # video id
    #assert reduce(eq, redirect_list)
    config_pytomo.LOG.info('new redirect urls: %s', redirect_list)
    return (url, cache_url, current_stats), redirect_list

def compute_download_stats(resolver, ip_address, cache_uri, current_stats,
                            do_full_crawl=False):
    #redirect=False,
    '' 'Return a list of the download statistics related to the cache_uri'''
    # it's important to pass the uri with the ip_address to avoid
    # uncontrolled DNS resolution
    if do_full_crawl:
        d_time = config_pytomo.MAX_DOWNLOAD_TIME
    else:
        d_time = config_pytomo.DOWNLOAD_TIME
    # may be done multiple times in case of different IP addresses
    # resolved and uncaught errors on each IP
    redirect_url = None
#    if 'default' in resolver:
#    config_pytomo.LOG.debug('trying url without IP')
    try:
        status_code, download_stats, redirect_url = (
                lib_general_download.get_download_stats(cache_uri,
                                        ip_address, download_time=d_time))
                                                #redirect=redirect))
    except (urllib2.HTTPError, ), nested_err:
        config_pytomo.LOG.exception(nested_err)
        # do nothing
        return None, None, None
    except (TypeError, ), mes:
        config_pytomo.LOG.debug('no data')
        config_pytomo.LOG.exception(mes)
        return None, None, None
    except Exception, mes:
        config_pytomo.LOG.exception('Uncaught exception: %s', mes)
        #import pdb; pdb.set_trace()
        return None, None, None
#    else:
#        # stats can thus be collected only on default resolver
#        if ip_address in current_stats:
#            # HARD CODED current_stats index: BAD
#            download_stats = current_stats[ip_address][2]
#        else:
#            download_stats = None
    return download_stats, redirect_url, status_code

def format_stats(stats, cache_server_delay, service=SERVICE):
    """Return the stats as a list of tuple to insert into database
    >>> stats = ('http://www.youtube.com/watch?v=RcmKbTR--iA',
    ...            'http://v15.lscache3.c.youtube.com',
    ...             {'173.194.20.56': [datetime.datetime(
    ...                                 2011, 5, 6, 15, 30, 50, 103775),
    ...                                 None,
    ...                                [8.9944229125976562, 'mp4',
    ...                                225,
    ...                                115012833.0,
    ...                                511168.14666666667,
    ...                                9575411,
    ...                                0,
    ...                                0.99954795837402344,
    ...                                7.9875903129577637,
    ...                                11.722306421319782,
    ...                                1192528.8804511931, 15169],
    ...                              None, 'default_10.193.225.12']})

    >>> format_stats(stats) #doctest: +NORMALIZE_WHITESPACE
        [(datetime.datetime(2011, 5, 6, 15, 30, 50, 103775),
          'Youtube', 'http://www.youtube.com/watch?v=RcmKbTR--iA',
      'http://v15.lscache3.c.youtube.com', '173.194.20.56',
       'default_10.193.225.12', 15169, None, None, None, 8.9944229125976562,
      'mp4', 225, 115012833.0, 511168.14666666667, 9575411, 0,
     0.99954795837402344, 7.9875903129577637, 11.722306421319782,
      1192528.8804511931, None)]

    >>> stats = ('http://www.youtube.com/watch?v=OdF-oiaICZI',
    ...  'http://v7.lscache8.c.youtube.com',
    ...                 {'74.125.105.226': [datetime.datetime(
    ...                                       2011, 5, 6, 15, 30, 50, 103775),
    ...                                     [26.0, 196.0, 82.0],
    ...                                     [30.311000108718872, 'mp4',
    ...                                      287.487, 16840065.0,
    ...                                      58576.78781997099,
    ...                                      1967199, 0,
    ...                                      1.316999912261963,
    ...                                      28.986000061035156,
    ...                                      5.542251416248594,
    ...                                      1109.4598961624772, 15169],
    ...                                    'http://www.youtube.com/fake_redirect',
    ...                       'google_public_dns_8.8.8.8_open_dns_208.67.220.220'],
    ...                  '173.194.8.226': [datetime.datetime(2011, 5, 6, 15,
    ...                                                       30, 51, 103775),
    ...                                    [103.0, 108.0, 105.0],
    ...                                    [30.287999868392944, 'mp4',
    ...                                     287.487, 16840065.0,
    ...                                     58576.78781997099,
    ...                                     2307716,
    ...                                     0,
    ...                                     1.3849999904632568,
    ...                                     28.89300012588501,
    ...                                     11.47842453761781,
    ...                                     32770.37517215069, 15169],
    ...                                    None, 'default_212.234.161.118']})


    >>> format_stats(stats) #doctest: +NORMALIZE_WHITESPACE
    [(datetime.datetime(2011, 5, 6, 15, 30, 50, 103775),
       'Youtube', 'http://www.youtube.com/watch?v=OdF-oiaICZI',
      'http://v7.lscache8.c.youtube.com', '74.125.105.226',
            'google_public_dns_8.8.8.8_open_dns_208.67.220.220', 15169, 26.0, 196.0, 82.0,
      30.311000108718872, 'mp4', 287.48700000000002, 16840065.0,
      58576.787819970988, 1967199, 0, 1.3169999122619629,
      28.986000061035156, 5.5422514162485941, 1109.4598961624772,
      'http://www.youtube.com/fake_redirect'),
     (datetime.datetime(2011, 5, 6, 15, 30, 51, 103775),
      'Youtube', 'http://www.youtube.com/watch?v=OdF-oiaICZI',
      'http://v7.lscache8.c.youtube.com', '173.194.8.226',
      'default_212.234.161.118', 103.0, 108.0, 105.0, 30.287999868392944,
      'mp4', 287.48700000000002, 16840065.0, 58576.787819970988, 2307716,
      0, 1.3849999904632568, 28.89300012588501, 11.47842453761781,
      32770.375172150692, None)]
    """
    record_list = []
    (url, cache_url, current_stats) = stats
    for (ip_address, values) in current_stats.items():
        (timestamp, ping_times, download_stats, redirect_url,
         resolver, req_time, as_nb, status_code) = values
        if not ping_times:
            ping_times = [None] * config_pytomo.NB_PING_VALUES
        if not download_stats:
            download_stats = [None] * config_pytomo.NB_DOWNLOAD_VALUES
        # use inet_aton(ip_address) for optimisation on this field
        row = ([timestamp, service, url, cache_url, cache_server_delay,
                ip_address, resolver, req_time, as_nb]
               + list(ping_times) + download_stats + [redirect_url, status_code])
        record_list.append(tuple(row))
    return record_list

def set_up_snmp():
    '''Run Agent X and prepare the dataset'''
    try:
        from . import hebexsnmptools
    except ImportError:
        config_pytomo.LOG.error('No hebexsnmptools module')
        config_pytomo.LOG.info('Try installing it and ctypes')
        config_pytomo.SNMP = False
    else:
        config_pytomo.hebexsnmptools = hebexsnmptools
        config_pytomo.dataset = hebexsnmptools.SnmpData(
                                                    root=config_pytomo.ROOT_OID)
        ax = hebexsnmptools.AgentX(name='PytomoAgent',
                                   data=config_pytomo.dataset)
        ax.Run()
        # pytomoGlbStats
        config_pytomo.dataset.registerVar(
                                    config_pytomo.snmp_pytomoObjectName + '.0',
                                    hebexsnmptools.ASN_OCTET_STR,
                                    config_pytomo.snmp_pytomoObjectName_str)
        config_pytomo.dataset.registerVar(
                                        config_pytomo.snmp_pytomoDescr + '.0',
                                        hebexsnmptools.ASN_OCTET_STR,
                                        config_pytomo.snmp_pytomoDescr_str)
        config_pytomo.dataset.registerVar(
                                        config_pytomo.snmp_pytomoContact + '.0',
                                        hebexsnmptools.ASN_OCTET_STR,
                                        config_pytomo.snmp_pytomoContact_str)
        config_pytomo.dataset.registerVar(
                            config_pytomo.snmp_pytomoDownloadDuration + '.0',
                            hebexsnmptools.ASN_GAUGE,
                            int(config_pytomo.DOWNLOAD_TIME))
        config_pytomo.dataset.registerVar(
                                    config_pytomo.snmp_pytomoSleepTime + '.0',
                                    hebexsnmptools.ASN_GAUGE,
                                    int(config_pytomo.DELAY_BETWEEN_REQUESTS))
        # initiate tables for Url stats
        config_pytomo.snmp_tables = []
        config_pytomo.snmp_types = []
        config_pytomo.urlIndexTable = config_pytomo.dataset.addTable(
                config_pytomo.snmp_pytomoUrlIndex, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlIndexTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_OCTET_STR)
        config_pytomo.urlTimeStampTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoTimeStamp, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlTimeStampTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_OCTET_STR)
        config_pytomo.urlServiceTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoService, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlServiceTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_OCTET_STR)
        config_pytomo.urlCacheUrlTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoCacheUrl, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlCacheUrlTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_OCTET_STR)
        config_pytomo.urlCacheServerDelayTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoCacheServerDelay, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlCacheServerDelayTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlAddressIpTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoAddressIp, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlAddressIpTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_OCTET_STR)
        config_pytomo.urlResolverTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoResolver, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlResolverTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_OCTET_STR)
        config_pytomo.urlResolveTimeTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoResolveTime, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlResolveTimeTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlAsNumberTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoAsNumber, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlAsNumberTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_INTEGER)
        config_pytomo.urlPingMinTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoPingMin, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlPingMinTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlPingAvgTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoPingAvg, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlPingAvgTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlPingMaxTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoPingMax, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlPingMaxTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlDownloadTimeTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoDownloadTime, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlDownloadTimeTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlVideoTypeTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoVideoType, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlVideoTypeTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlVideoDurationTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoVideoDuration, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlVideoDurationTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlVideoLengthTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoVideoLength, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlVideoLengthTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlEncodingRateTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoEncodingRate, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlEncodingRateTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlDownloadBytesTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoDownloadBytes, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlDownloadBytesTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_INTEGER)
        config_pytomo.urlDownloadInterruptionsTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoDownloadInterruptions, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlDownloadInterruptionsTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_INTEGER)
        config_pytomo.urlInitialDataTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoInitialData, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlInitialDataTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlInitialRateTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoInitialRate, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlInitialRateTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlInitialPlaybackBufferTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoInitialPlaybackBuffer, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlInitialPlaybackBufferTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlBufferingDurationTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoBufferingDuration, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlBufferingDurationTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlPlaybackDurationTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoPlaybackDuration, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlPlaybackDurationTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlBufferDurationAtEndTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoBufferDurationAtEnd, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlBufferDurationAtEndTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlTimeTogetFirstByteTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoTimeTogetFirstByte, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlTimeTogetFirstByteTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlMaxInstantThpTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoMaxInstantThp, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlMaxInstantThpTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_GAUGE)
        config_pytomo.urlRedirectUrlTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoRedirectUrl, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlRedirectUrlTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_OCTET_STR)
        config_pytomo.urlStatusCodeTable = config_pytomo.dataset.addTable(
            config_pytomo.snmp_pytomoStatusCode, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.snmp_tables.append(config_pytomo.urlStatusCodeTable)
        config_pytomo.snmp_types.append(hebexsnmptools.ASN_INTEGER)

        #Statistics by ip
        config_pytomo.IpNameTable = config_pytomo.dataset.addTable(config_pytomo.snmp_pytomoIpName, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.IpCountTable = config_pytomo.dataset.addTable(config_pytomo.snmp_pytomoIpCount, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.IpCountType =  hebexsnmptools.ASN_COUNTER64
        config_pytomo.IpNameType =  hebexsnmptools.ASN_OCTET_STR
		#Statistics by AS
        config_pytomo.ASNameTable = config_pytomo.dataset.addTable(config_pytomo.snmp_pytomoASName, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.ASCountTable = config_pytomo.dataset.addTable(config_pytomo.snmp_pytomoASCount, hebexsnmptools.TABLE_INDEX_STRING)
        config_pytomo.ASCountType = hebexsnmptools.ASN_COUNTER64
        config_pytomo.ASNameType =  hebexsnmptools.ASN_OCTET_STR


def check_out_files(file_pattern, directory, timestamp):
    """Return a full path of the file used for the output
    Test if the path exists, create if possible or create it in default user
    directory

    >>> file_pattern = None
    >>> directory = 'logs'
    >>> timestamp = 'doc_test'
    >>> check_out_files(file_pattern, directory, timestamp) #doctest: +ELLIPSIS
    >>> file_pattern = 'pytomo.log'
    >>> check_out_files(file_pattern, directory, timestamp) #doctest: +ELLIPSIS
    '...doc_test.pytomo.log'

    """
    if file_pattern == None:
        return None
    if config_pytomo.USE_PACKAGE_DIR:
        base_dir = PACKAGE_DIR
    else:
        base_dir = os.getcwd()
    if directory:
        out_dir = sep.join((base_dir, directory))
        if not os.path.exists(out_dir):
            try:
                os.makedirs(out_dir)
            except OSError, mes:
                config_pytomo.LOG.warn(
                    'Out dir %s does not exist and cannot be created\n%s',
                    out_dir, mes)
                if HOME_DIR:
                    config_pytomo.LOG.warn('Will use home base dir: %s',
                                           HOME_DIR)
                    out_dir = sep.join((HOME_DIR, directory))
                    if not os.path.exists(out_dir):
                        # do not catch OSError as it's our second attempt
                        os.makedirs(out_dir)
                else:
                    config_pytomo.LOG.error(
                        'Impossible to create output file: %s', file_pattern)
                    raise IOError
    else:
        out_dir = os.getcwd()
    # AO 27112012 modified to also include service (yt, dm)
    crawl_service_provider = (config_pytomo.CRAWL_SERVICE +
                              ('_%s' % config_pytomo.PROVIDER
                               if config_pytomo.PROVIDER else ''))
    out_file = sep.join((out_dir, '.'.join((socket.gethostname(),
                                            crawl_service_provider,
                                            timestamp, file_pattern))))
    # do not catch IOError
    with open(out_file, 'a') as _:
        # just test writing in the out file
        pass
    return out_file

def md5sum(input_file):
    'Return the standard md5 of the file'
    # to cope with large files
    # value taken from Python distribution
    try:
        input_stream = open(input_file, 'rb')
    except (TypeError, IOError), mes:
        config_pytomo.LOG.exception('Unable to compute the md5 of file: %s',
                                    mes)
        return None
    bufsize = 8096
    hash_value = hashlib.md5()
    while True:
        data = input_stream.read(bufsize)
        if not data:
            break
        hash_value.update(data)
    return hash_value.hexdigest()

class MaxUrlException(Exception):
    'Class to stop crawling when the max nb of urls has been attained'
    pass

def add_stats(stats, cache_server_delay, url, result_stream=None, data_base=None):
    '''Insert the stats in the db and update the crawled urls
    '''
    if result_stream:
        pprint(stats, stream=result_stream)
    if data_base:
        if YOUTUBE_SERVICE in url:
            service = 'YouTube'
        elif DAILYMOTION_SERVICE in url:
            service = 'Dailymotion'
        else:
            service = 'Unknown'
        for row in format_stats(stats, cache_server_delay, service=service):
            data_base.insert_record(row)
    if config_pytomo.SNMP:
        format_gauge = lambda x: int(x * 1000 if x else 0)
        format_datetime = lambda x: x.strftime('%Y%m%d %H:%M:%S')
        format_int = lambda x: x if x else 0
        identity = lambda x: x if x else ''
        formatted_stats = format_stats(stats, cache_server_delay,service=service)

        for stats_line in formatted_stats:
            video_url = stats_line[config_pytomo.URL_IDX]
            video_ip = stats_line[config_pytomo.IP_IDX]
            video_as = str(stats_line[config_pytomo.AS_IDX])
            for table, snmp_type, idx in zip(config_pytomo.snmp_tables,
                                             config_pytomo.snmp_types,
                                             config_pytomo.STATS_IDX):
                if snmp_type == config_pytomo.hebexsnmptools.ASN_GAUGE:
                    formatter = format_gauge
                elif snmp_type == config_pytomo.hebexsnmptools.ASN_INTEGER:
                    formatter = format_int
                elif idx == config_pytomo.TS_IDX:
                    formatter = format_datetime
                else:
                    formatter = identity
                table.registerValue(video_url, snmp_type,
                        formatter(stats_line[idx]))

            if not config_pytomo.DOWNLOADED_BY_IP.has_key(video_ip):
                config_pytomo.DOWNLOADED_BY_IP[video_ip] = 0
                config_pytomo.IpNameTable.registerValue(video_ip, config_pytomo.IpNameType, video_ip)
            if not config_pytomo.DOWNLOADED_BY_AS.has_key(video_as):
                config_pytomo.DOWNLOADED_BY_AS[video_as] = 0
                config_pytomo.ASNameTable.registerValue(video_as, config_pytomo.ASNameType, video_as)

            config_pytomo.DOWNLOADED_BY_IP[video_ip] += 1
            config_pytomo.DOWNLOADED_BY_AS[video_as] += 1

            config_pytomo.IpCountTable.registerValue(video_ip, config_pytomo.IpCountType , config_pytomo.DOWNLOADED_BY_IP[video_ip] )
            config_pytomo.ASCountTable.registerValue(video_as, config_pytomo.ASCountType , config_pytomo.DOWNLOADED_BY_AS[video_as] )




def retrieve_cache_urls(url, lib_download, hd_first=False):
    ''' Return the list of cache url servers for a given video.
    The last element is the server from which the actual video is downloaded.
    '''
    # cache url server dependent on the service
    cache_uri = lib_download.get_cache_url(url, hd_first=hd_first)
    if not cache_uri:
        return []
    # list of cache urls
    redirect_links = []
    nb_redirects = 0
    redirect_links.append(cache_uri)
    # try to connect to the cache url, check if there are more redirects
    response = lib_links_extractor.retrieve_header(cache_uri,
                                                   follow_redirect=False)
    while (response and nb_redirects <= config_pytomo.MAX_NB_REDIRECT):
        config_pytomo.LOG.debug('response_code: %s', response.code)
        # no redirect
        if response.code == config_pytomo.HTTP_OK:
            break
        redirect_server = response.location
        redirect_links.append(redirect_server)
        response = lib_links_extractor.retrieve_header(redirect_server,
                                                       follow_redirect=False)
        cache_uri = redirect_server
        nb_redirects += 1
    if nb_redirects > config_pytomo.MAX_NB_REDIRECT:
        config_pytomo.LOG.debug('retrieve_redirect_links: Too many cache server'
                                ' redirects.')
        return []
    return redirect_links

def check_full_download(len_crawled_urls):
    'Check if the urls should be fully downloaded'
    if (config_pytomo.FREQ_FULL_DOWNLOAD
        and len_crawled_urls % config_pytomo.FREQ_FULL_DOWNLOAD == 0):
        return True
    else:
        return False

def crawl_link(url, next_urls, result_stream, data_base, related, loop,
               hd_first=False):
    '''Crawl the link and return the next urls'''
    try:
        crawled_urls = map(itemgetter(-1),
                       data_base.fetch_single_parameter_with_stats(PARAM_URL))
    except Error, mes:
        config_pytomo.LOG.error('Unable to extract data %s with error: %s',
                                PARAM_URL, mes)
        return next_urls
    if not loop and len(crawled_urls) >= config_pytomo.MAX_CRAWLED_URLS:
        config_pytomo.LOG.debug('Reached max crawls')
        raise MaxUrlException()
    config_pytomo.LOG.debug('Crawl of url# %d: %s', len(crawled_urls), url)
    if not loop and url in crawled_urls:
        config_pytomo.LOG.debug('Skipped url already crawled: %s', url)
        return next_urls
    # print completed urls so that user knows that the crawl is running
    if (crawled_urls
        and len(crawled_urls) % config_pytomo.CRAWLED_URLS_MODULO == 0
        # AO 26112012 trying to solve win freeze when printing to stdout
        # does not work, best to not print on windows?
        and 'win' not in sys.platform.lower()):
        sys.stdout.write('Completed %d urls\n' % len(crawled_urls))
        sys.stdout.flush()
        #print('Completed %d urls' % len(crawled_urls))
    if result_stream:
        config_pytomo.LOG.debug('Printing to result_stream')
        print(sep=config_pytomo.SEP_LINE, file=result_stream)
    stats = None
    redirect_list = []
    download_libs = select_libraries(url)
    if download_libs:
        (lib_download, lib_api) = download_libs
    else:
        config_pytomo.LOG.error('Could not select libraries to compute'
                                ' statistics for %s', url)
        return next_urls
    start_cache_server_time = time.time()
    cache_servers = retrieve_cache_urls(url, lib_download, hd_first=hd_first)
    end_cache_server_time = time.time()
    cache_server_delay = end_cache_server_time - start_cache_server_time
    config_pytomo.LOG.debug('For url=%s the cache urls are %s',
                            url, cache_servers)
    if not cache_servers:
        config_pytomo.LOG.error('Error retrieving cache for: %s', url)
        return next_urls
    # redirect servers (all except last) just ping statistics are stored
    for index, cache_server in enumerate(cache_servers[:-1]):
        try:
            stats, redirect_list = compute_stats(url, cache_server, False,
                                    redirect_url=cache_servers[index + 1])
        except TypeError:
            config_pytomo.LOG.error('Error retrieving stats for: %s',
                                    cache_server)
        if stats:
            add_stats(stats, cache_server_delay, url, result_stream, data_base)
        else:
            config_pytomo.LOG.info('no stats for url: %s', cache_server)
        if redirect_list:
            config_pytomo.LOG.info('redirect_list for redirect servers: %s',
                                   redirect_list)
            config_pytomo.LOG.info('these addresses are NOT taken into account')
    do_full_crawl = check_full_download(len(crawled_urls))
    # final redirect, download server for the video
    cache_server = cache_servers[-1]
    try:
        stats, redirect_list = compute_stats(url, cache_server, True,
                              do_full_crawl=do_full_crawl)
    except TypeError:
        config_pytomo.LOG.error('Error retrieving stats for: %s', cache_server)
    if stats:
        add_stats(stats, cache_server_delay, url, result_stream, data_base)
        # wait only if there were stats retrieved
        time.sleep(config_pytomo.DELAY_BETWEEN_REQUESTS)
    else:
        config_pytomo.LOG.info('no stats for url: %s', cache_server)
    if redirect_list and redirect_list != [None]:
        #assert reduce(eq, redirect_list)
        if not reduce(eq, redirect_list):
            config_pytomo.LOG.error('redirect list urls are not the same: %s',
                                    redirect_list)
        cache_server = redirect_list[0]
        stats, redirect_list = compute_stats(url, cache_server, True,
                                             do_full_crawl=do_full_crawl)
        if stats:
            add_stats(stats, cache_server_delay, url, result_stream, data_base)
            # wait only if there were stats retrieved
            time.sleep(config_pytomo.DELAY_BETWEEN_REQUESTS)
        else:
            config_pytomo.LOG.info('no stats for url: %s', cache_server)
        if redirect_list:
            config_pytomo.LOG.error('new redirect list: %s', redirect_list)
            config_pytomo.LOG.error('these addresses are NOT taken into '
                                    'account')
    if (related and len(next_urls) < config_pytomo.MAX_CRAWLED_URLS):
        try:
            related_urls = set(filter(None,
                                      lib_api.get_related_urls(url,
                                               config_pytomo.MAX_PER_PAGE,
                                               config_pytomo.MAX_PER_URL)))
        except TypeError:
            return next_urls
        next_urls = next_urls.union(related_urls)
    return next_urls

def crawl_links(input_links, result_stream=None,
                data_base=None, related=True, loop=False, hd_first=False):
    '''Wrapper to crawl each input link'''
    next_urls = set()
    # When a redirect occurs, the database should store in the
    # 'Url' field the first link that caused redirection and then statistics
    # for each cache server it gets redirected to
    # - download statistics: only for final cache server from which the video is
    #                        downloaded
    # - ping statistics: for each cache server (intermediate and final)
    config_pytomo.LOG.debug('input_links: %s', input_links)
    for url in input_links:
        next_urls = crawl_link(url, next_urls, result_stream, data_base,
                               related, loop, hd_first=hd_first)
    if not loop:
        next_urls = next_urls.difference(input_links)
    else:
        next_urls = input_links.copy()
    config_pytomo.LOG.debug('next_urls: %s', next_urls)
    return next_urls

def do_rounds(input_links, result_stream, data_base, db_file,
              image_file, related=True, loop=False, hd_first=False):
    '''Perform the rounds of crawl'''
    max_rounds = config_pytomo.MAX_ROUNDS
    for round_nb in xrange(max_rounds):
        config_pytomo.LOG.warn('Round %d started\n%s',
                               round_nb, config_pytomo.SEP_LINE)
        # Reseting the name servers at start of each crawl
        config_pytomo.EXTRA_NAME_SERVERS_CC = []
        for (name_server, dns_server_ip_address) in (
                                            config_pytomo.EXTRA_NAME_SERVERS):
            config_pytomo.EXTRA_NAME_SERVERS_CC.append(
                                ('_'.join((config_pytomo.PROVIDER, name_server)),
                                 dns_server_ip_address))
#        config_pytomo.EXTRA_NAME_SERVERS_CC = (
#                                           config_pytomo.EXTRA_NAME_SERVERS[:])
        config_pytomo.LOG.info('Name servers at round %s:',
                               config_pytomo.EXTRA_NAME_SERVERS_CC)
        #config_pytomo.LOG.debug(input_links)
        try:
            input_links = crawl_links(input_links, result_stream,
                                      data_base, related=related, loop=loop,
                                      hd_first=hd_first)
        except ValueError:
            # AO 20120926 TODO: check if this catches exception of crawled_urls
            # extraction from database
            config_pytomo.LOG.debug('not able to retrieve stats from url')
            # no sleep here: check if it's ok
            continue
        # early exit if no more links
        if not input_links:
            break
        time.sleep(config_pytomo.DELAY_BETWEEN_REQUESTS)
        config_pytomo.LOG.debug('Slept %d',
                                config_pytomo.DELAY_BETWEEN_REQUESTS)
        # The plot is redrawn everytime the database is updated
        if config_pytomo.PLOT:
            lib_plot.plot_data(db_file, config_pytomo.COLUMN_NAMES,
                               image_file)

def do_crawl(result_stream=None, db_file=None, timestamp=None,
             image_file=None, loop=False, related=True, hd_first=False):
    '''Crawls the urls given by the url_file
    up to max_rounds are performed or max_visited_urls
    '''
    if not db_file and not result_stream and not config_pytomo.SNMP:
        config_pytomo.LOG.critical('Cannot start crawl because no file can '
                                   'store output')
        return
    config_pytomo.LOG.critical('Start crawl')
    if not timestamp:
        timestamp = strftime('%Y-%m-%d.%H_%M_%S')
    data_base = None
    if db_file:
        config_pytomo.DATABASE_TIMESTAMP = db_file
        trans_table = maketrans('.-', '__')
        config_pytomo.TABLE_TIMESTAMP = '_'.join((config_pytomo.TABLE,
                                              timestamp)).translate(trans_table)
        data_base = lib_database.PytomoDatabase(
                                            config_pytomo.DATABASE_TIMESTAMP)
        data_base.create_pytomo_table(config_pytomo.TABLE_TIMESTAMP)
#    max_per_page = config_pytomo.MAX_PER_PAGE
#    max_per_url = config_pytomo.MAX_PER_URL
    config_pytomo.LOG.debug('STATIC_URL_LIST: %s',
                            config_pytomo.STATIC_URL_LIST)
    if config_pytomo.STATIC_URL_LIST:
        input_links = set(filter(None, config_pytomo.STATIC_URL_LIST))
    else:
        if config_pytomo.CRAWL_SERVICE == YOUTUBE_SERVICE:
            lib_api = lib_youtube_api
        elif config_pytomo.CRAWL_SERVICE == DAILYMOTION_SERVICE:
            lib_api = lib_dailymotion_api
        input_links = set(filter(None,
                             lib_api.get_popular_links(
                                 input_time=config_pytomo.TIME_FRAME,
                                 max_results=config_pytomo.MAX_PER_PAGE)))
        if (config_pytomo.CRAWL_SERVICE == 'youtube'
            and config_pytomo.EXTRA_COUNTRY):
            links_country = set(filter(None,
                                  lib_api.get_popular_links(
                                      input_time=config_pytomo.TIME_FRAME,
                                      max_results=config_pytomo.MAX_PER_PAGE,
                                      country=config_pytomo.EXTRA_COUNTRY)))
            input_links = input_links.union(links_country)
        config_pytomo.LOG.debug('bootstrap links: %s', input_links)
    if not input_links:
        config_pytomo.LOG.critical('Cannot find input links to crawl')
        if data_base:
            data_base.close_handle()
        return
    try:
        if loop:
            while True:
                do_rounds(input_links, result_stream, data_base, db_file,
                          image_file, related=related, loop=loop,
                          hd_first=hd_first)
        else:
            do_rounds(input_links, result_stream, data_base, db_file,
                      image_file, related=related, loop=loop, hd_first=hd_first)
            # next round input are related links of the current input_links
    #   input_links = get_next_round_urls(lib_api, input_links, max_per_page,
    #                                            max_per_url)
    except MaxUrlException:
        config_pytomo.LOG.warn('Stopping crawl because %d urls have been '
                               'crawled', config_pytomo.MAX_CRAWLED_URLS)
    if data_base:
        data_base.close_handle()
    config_pytomo.LOG.warn('Crawl finished\n' + config_pytomo.SEP_LINE)

def get_next_round_urls(lib_api, input_links,
                        max_per_page=config_pytomo.MAX_PER_PAGE,
                        max_per_url=config_pytomo.MAX_PER_URL,
                        max_round_duration=config_pytomo.MAX_ROUND_DURATION):
    ''' Return a tuple of the set of input urls and a set of related url of
    videos.
    Arguments:
        * input_links: list of the urls
        * max_per_url and max_per_page options
        * out_file_name: if provided, list is dump in it
    '''
    # keep only non-duplicated links and no links from input file
    start = time.time()
    if len(input_links) > CONTINUOUS_CRAWL_SIZE:
        related_links = []
        for url in input_links:
            time.sleep(config_pytomo.DELAY_BETWEEN_REQUESTS)
            related_links = concat(related_links,
                                   lib_api.get_related_urls(url, max_per_page,
                                                   max_per_url))
            if (time.time() - start) > max_round_duration:
                break
        related_links = set(related_links).difference(input_links)
    else:
        related_links = set(reduce(concat, (lib_api.get_related_urls(url,
                                            max_per_page, max_per_url)
                                            for url in input_links), [])
                           ).difference(input_links)
    config_pytomo.LOG.info('%d links collected by crawler',
                           len(related_links))
    config_pytomo.LOG.debug(related_links)
    return related_links


def convert_debug_level(_, __, value, parser):
    'Convert the string passed to a logging level'
    try:
        log_level = config_pytomo.NAME_TO_LEVEL[value.upper()]
    except KeyError:
        parser.error('Incorrect log level.\n'
                     "Choose from: 'DEBUG', 'INFO', 'WARNING', "
                     "'ERROR' and 'CRITICAL' (default '%s')"
                     % config_pytomo.LEVEL_TO_NAME[
                         config_pytomo.LOG_LEVEL])
        return
    setattr(parser.values, 'LOG_LEVEL', log_level)

def set_proxies(_, __, value, parser):
    'Convert the proxy passed to a dict to be handled by urllib2'
    if value:
        # remove quotes
        value = value.translate(None, '\'"')
        if not value.startswith('http://'):
            value = 'http://'.join(('', value))
        setattr(parser.values, 'PROXIES', {'http': value, 'https': value,
                                           'ftp': value})

def create_options(parser):
    'Add the different options to the parser'
    parser.add_option('-b', '--batch', dest='BATCH_MODE', action='store_true',
                      help=('Do NOT prompt user for any input'),
                      default=config_pytomo.BATCH_MODE)
    parser.add_option('-u', dest='MAX_CRAWLED_URLS', type='int',
                      help=('Max number of urls to visit (default %d)'
                            % config_pytomo.MAX_CRAWLED_URLS),
                      default=config_pytomo.MAX_CRAWLED_URLS)
    parser.add_option('-r', dest='MAX_ROUNDS', type='int',
                      help=('Max number of rounds to perform (default %d)'
                            % config_pytomo.MAX_ROUNDS),
                      default=config_pytomo.MAX_ROUNDS)
    parser.add_option('--no-loop', dest='LOOP', action='store_false',
                      default=(not config_pytomo.LOOP),
                      help=('Do not loop after completing the max nb of rounds '
                      '(default %s)' % (not config_pytomo.LOOP)))
    parser.add_option('-l', '--loop', dest='LOOP', action='store_true',
                      default=config_pytomo.LOOP,
                      help=('Loop after completing the max nb of rounds '
                      '(default %s)' % config_pytomo.LOOP))
    parser.add_option('-R', '--related', dest='RELATED',
                      action='store_true', default=config_pytomo.RELATED,
                      help=('Crawl related videos (default %s)'
                            % config_pytomo.RELATED))
    parser.add_option('--no-related', dest='RELATED',
                      action='store_false', default=config_pytomo.RELATED,
                      help=('Do NOT crawl related videos (stays with the first '
                        'urls found: either most popular or arguments given) '
                           '(default %s)' % (not config_pytomo.RELATED)))
    parser.add_option('-p', dest='MAX_PER_URL', type='int',
                      help=('Max number of related urls from each page '
                            '(default %d)' % config_pytomo.MAX_PER_URL),
                      default=config_pytomo.MAX_PER_URL)
    parser.add_option('-P', dest='MAX_PER_PAGE', type='int',
                      help=('Max number of related videos from each page '
                            '(default %d)' % config_pytomo.MAX_PER_PAGE),
                      default=config_pytomo.MAX_PER_PAGE)
    parser.add_option('-s', dest='CRAWL_SERVICE', type='string', action='store',
                      help=('Service for the most popular videos to fetch '
                            "at start of crawl: select between 'youtube', "
                            "or 'dailymotion' (default '%s')"
                            % config_pytomo.CRAWL_SERVICE),
                      default=config_pytomo.CRAWL_SERVICE)
    parser.add_option('--snmp', dest='SNMP', action='store_true',
                      default=config_pytomo.SNMP,
                      help='SNMP mode')
    parser.add_option('-t', dest='TIME_FRAME', type='string',
                      help=('Timeframe for the most popular videos to fetch '
                            "at start of crawl put 'today', or 'all_time' "
                            "(default '%s') [only for YouTube]"
                            % config_pytomo.TIME_FRAME),
                      default=config_pytomo.TIME_FRAME)
    parser.add_option('-n', dest='PING_PACKETS', type='int',
                      help=('Number of packets to be sent for each ping '
                            '(default %d)' % config_pytomo.PING_PACKETS),
                      default=config_pytomo.PING_PACKETS)
    parser.add_option('-D', dest='DOWNLOAD_TIME', type='float',
                      help=('Download time for the video in seconds '
                            '(default %f)' % config_pytomo.DOWNLOAD_TIME),
                      default=config_pytomo.DOWNLOAD_TIME)
    parser.add_option('-S', dest='DELAY_BETWEEN_REQUESTS', type='float',
                      help=('Delay between consecutive video requests in '
                            ' seconds (default %f)'
                            % config_pytomo.DELAY_BETWEEN_REQUESTS),
                      default=config_pytomo.DELAY_BETWEEN_REQUESTS)
#    parser.add_option('-B', dest='INITIAL_PLAYBACK_DURATION ', type='float',
#                      help=('Buffering video duration in seconds (default %f)'
#                            % config_pytomo.INITIAL_PLAYBACK_DURATION),
#                      default=config_pytomo.INITIAL_PLAYBACK_DURATION )
#    parser.add_option('-M', dest='MIN_PLAYOUT_BUFFER_SIZE', type='float',
#                      help=('Minimum Playout Buffer Size in seconds '
#                            '(default %f)' % config_pytomo.MIN_PLAYOUT_BUFFER),
#                      default=config_pytomo.MIN_PLAYOUT_BUFFER)
    parser.add_option('-x', '--no-log-ip', dest='LOG_PUBLIC_IP',
                      action='store_false',
                      help=('Do NOT store public IP address of the machine '
                            'in the logs'), default=config_pytomo.LOG_PUBLIC_IP)
    parser.add_option('-c', '--centralise', dest='CENTRALISE_DATA',
                      action='store_true',
                      help='Send logs to the centralisation server',
                      default=config_pytomo.CENTRALISE_DATA)
    parser.add_option('--centralisation_server',
                      dest='CENTRALISATION_SERVER',
                      default=config_pytomo.CENTRALISATION_SERVER,
                      help=('FTP server to centralise data (default %s)'
                            % config_pytomo.CENTRALISATION_SERVER))
    parser.add_option('--http-proxy', dest='PROXIES', type='string',
                      help=('in case of http proxy to reach Internet '
                            '(default %s)' % config_pytomo.PROXIES),
                      default=config_pytomo.PROXIES, action='callback',
                     callback=set_proxies)
    parser.add_option('--provider', dest='PROVIDER', type='string',
                      help='Indicate the ISP', default=config_pytomo.PROVIDER)
    parser.add_option('--download-extra-dns', dest='DOWNLOAD_FROM_EXTRA_IPS',
                      action='store_true',
                      default=config_pytomo.DOWNLOAD_FROM_EXTRA_IPS,
                      help=('Download videos from IP resolved by other DNS '
                        '(default %s)' % config_pytomo.DOWNLOAD_FROM_EXTRA_IPS))
    parser.add_option('-L', dest='LOG_LEVEL', type='string',
                      help=('The log level setting for the Logging module.'
                            "Choose from: 'DEBUG', 'INFO', 'WARNING', "
                            "'ERROR' and 'CRITICAL' (default '%s')"
                            % config_pytomo.LEVEL_TO_NAME[
                                config_pytomo.LOG_LEVEL]),
                      default=config_pytomo.LOG_LEVEL, action='callback',
                      callback=convert_debug_level)
    parser.add_option('-f', '--input-file', dest='INPUT_FILE', type='string',
                      help='File indicating the URLs to crawl (one URL per line)',
                      default=config_pytomo.INPUT_FILE)
    parser.add_option('-H', '--hd', dest='HD_FIRST',
                      action='store_true',
                      help=('Tries to fetch video in HD (implemented only for'
                            'YouTube)'),
                      default=config_pytomo.CENTRALISE_DATA)


def check_options(parser, options):
    'Check incompatible options'
    if options.TIME_FRAME not in (['today', 'week', 'month', 'all_time']):
        parser.error('Incorrect time frame.\n'
                     "Choose from: 'today', 'week', 'month', 'all_time' "
                     "(default: '%s')" % config_pytomo.TIME_FRAME)
    if options.CRAWL_SERVICE.lower() not in ([YOUTUBE_SERVICE,
                                              DAILYMOTION_SERVICE]):
        parser.error('Incorrect Service.\n'
                     "Choose from: 'youtube', 'dailymotion' "
                     "(default '%s')" % config_pytomo.CRAWL_SERVICE)

def write_options_to_config(options):
    'Write read options to config_pytomo'
    for name, value in options.__dict__.items():
        setattr(config_pytomo, name, value)

def log_ip_address():
    'Log the remote IP addresses'
    print('\nLogging the local public IP address.\n')
    # is local address of some interest??
    # check: http://stackoverflow.com/
    # questions/166506/finding-local-ip-addresses-in-python
    lib_links_extractor.configure_proxy()
    count = 0
    retries = 3
    public_ip = None
    while count < retries:
        try:
            if sys.hexversion >= int(0x2060000):
                # timeout is available only python above 2.6
                public_ip = json.load(
                    urllib2.urlopen(PUBLIC_IP_FINDER, None,
                                    config_pytomo.IPADDR_TIMEOUT))['data']['ip']
            else:
                public_ip = json.load(
                    urllib2.urlopen(PUBLIC_IP_FINDER, None,
                                    config_pytomo.URL_TIMEOUT))['data']['ip']
        #except urllib2.URLError, mes:
        except Exception, mes:
            config_pytomo.LOG.critical('Public IP address not found: %s', mes)
            count += 1
            print('Public IP address not found: %s, retrying in %i seconds'
                  % (mes, count))
            time.sleep(count)
            continue
        else:
            # Check for valid IP
            is_valid = re.match(IP_MATCH_PATTERN, public_ip)
            if is_valid:
                config_pytomo.LOG.critical('Machine has this public IP address:'
                                           ' %s', public_ip)
            else:
                config_pytomo.LOG.critical('Unable to Parse IP address: %s... '
                                           'Skipping', public_ip)
            break
    if count >= retries:
        config_pytomo.LOG.error(u'ERROR: giving up after %d retries, public IP'
                                ' not found', retries)
        print('Public IP address could not be logged.\n')

def log_md5_results(result_file, db_file):
    'Computes and stores the md5 hash of result and database files'
    if db_file:
        config_pytomo.LOG.critical('Hash of database file: %s',
                                   md5sum(db_file))
    if result_file and result_file != sys.stdout:
        config_pytomo.LOG.critical('Hash of result file: %s',
                                   md5sum(result_file))

def configure_log_file(timestamp):
    'Configure log file and indicate succes or failure'
    print('Configuring log file')
    if config_pytomo.LOG_LEVEL == logging.DEBUG:
        # to have kaa-metadata logs
        config_pytomo.LOG = logging.getLogger('metadata')
    else:
        config_pytomo.LOG = logging.getLogger('demo')
    if config_pytomo.LOG_FILE == '-':
        handler = logging.StreamHandler(sys.stdout)
        print('Logs are on standard output')
        log_file = True
    else:
        try:
            log_file = check_out_files(config_pytomo.LOG_FILE,
                                       config_pytomo.LOG_DIR, timestamp)
        except IOError:
            raise IOError('Logfile %s could not be open for writing' % log_file)
        print('Logs are there: %s' % log_file)
        # for lib_youtube_download
        config_pytomo.LOG_FILE_TIMESTAMP = log_file
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
        config_pytomo.LOG.critical('%s: %s',
                                   value, getattr(config_pytomo, value))
    return log_file

class MyTimeoutException(Exception):
    'Class to generate timeout exceptions'
    pass

def configure_alarm(timeout):
    '''Set timeout if OS support it
    Return a bool indicating if signal is supported'''
    def timeout_handler(signum, frame):
        'handle the timeout'
        raise MyTimeoutException()
    # non-posix support for signals is weak
    support_signal = hasattr(signal, 'SIGALRM') and hasattr(signal, 'alarm')
    if support_signal:
        signal.signal(signal.SIGALRM, timeout_handler)
        # triger alarm in timeout seconds
        signal.alarm(timeout)
    return support_signal

def prompt_max_crawls(support_signal, timeout):
    'Function to prompt the user to enter max_urls'
    return raw_input('\n'.join(('Please enter the max. number of videos '
                              '(press Enter for default %d): ' %
                              config_pytomo.MAX_CRAWLED_URLS,
                          ('(or wait %d seconds)' % timeout if support_signal
                               else ''), '')))

def set_max_crawls(timeout=config_pytomo.USER_INPUT_TIMEOUT, prompt=True,
                   nb_max_crawls=config_pytomo.MAX_CRAWLED_URLS):
    'Sets the max number of videos to be crawlled'
    support_signal = configure_alarm(timeout)
    try:
        if prompt:
            max_crawls = prompt_max_crawls(support_signal, timeout)
        else:
            max_crawls = nb_max_crawls
    except MyTimeoutException:
        return None
    finally:
        if support_signal:
            # alarm disabled
            signal.alarm(0)
    if max_crawls:
        try:
            config_pytomo.MAX_CRAWLED_URLS = int(max_crawls)
        except ValueError:
            config_pytomo.LOG.error('User gave non-integer value: %s',
                                    max_crawls)
    max_craw_message = ('The Max Crawls has been set to: %s'
                        % config_pytomo.MAX_CRAWLED_URLS)
    print(max_craw_message)
    config_pytomo.LOG.critical(max_craw_message)
    return max_crawls

def prompt_proxies(support_signal, timeout):
    ''' Function to prompt the user to enter the proxies it uses to connect to
    the internet'''
    return raw_input("\n".join(("Please enter the proxies you use to connect to"
                                " the internet, in the format:\n"
                                "http://proxy:8080/\n"
                                "(press Enter for default: %s): " %
                                config_pytomo.PROXIES,
                            ("(or wait %d seconds)" % timeout if support_signal
                            else ""), "")))

def set_proxies_cli(timeout=config_pytomo.USER_INPUT_TIMEOUT):
    ''' Sets the proxies needed to connect to the internet'''
    support_signal = configure_alarm(timeout)
    try:
        cli_proxies = prompt_proxies(support_signal, timeout)
    except MyTimeoutException:
        return None
    finally:
        if support_signal:
            # alarm disabled
            signal.alarm(0)
    if cli_proxies:
        try:
            #config_pytomo.PROXIES = literal_eval(cli_proxies)
            setattr(config_pytomo, 'PROXIES',
                    {'http': cli_proxies, 'https': cli_proxies,
                     'ftp': cli_proxies})
        except (ValueError, SyntaxError):
            proxies_message = ("ERROR: User gave incorrect proxy format: *%s*\n"
                               "Will use default proxies: %s\nIf you need to "
                               "configure a specific proxy, please try to run"
                               " the application again, respecting the format:"
                               "\nhttp://proxy:8080/\n" %
                               (cli_proxies, config_pytomo.PROXIES))
            config_pytomo.LOG.error(proxies_message)
            print(proxies_message)
    proxies_message = ('The Proxies have been set to: %s\n'
                        % config_pytomo.PROXIES)
    print(proxies_message)
    config_pytomo.LOG.critical(proxies_message)
    return cli_proxies

def log_provider(timeout=config_pytomo.USER_INPUT_TIMEOUT):
    'Get and logs the provider from the user or skip after timeout seconds'
    support_signal = configure_alarm(timeout)
    try:
        provider = prompt_provider(support_signal, timeout)
    except MyTimeoutException:
        return None
    finally:
        if support_signal:
            # alarm disabled
            signal.alarm(0)
    config_pytomo.LOG.critical('User has given this provider: %s', provider)
    config_pytomo.PROVIDER = provider

def prompt_provider(support_signal, timeout):
    'Function to prompt for provider'
    return raw_input(''.join((
            'Please indicate your provider/ISP (leave blank for skipping).\n',
            'Crawl will START when you PRESS ENTER',
            ((' (or after %d seconds)' % timeout) if support_signal else ''),
            '.\n')))

def prompt_start_crawl():
    'Funtion to prompt user for to accept the crawling'
    return raw_input('Are you ok to start crawling? (Y/N)\n').upper()

def main(version=None, argv=None):
    '''Program wrapper
    Setup of log part
    '''
    if not argv:
        argv = sys.argv[1:]
    usage = ('%prog [-b --batch] '
             '[-u max_crawled_url] '
             '[-r max_rounds] '
             '[-l, --loop|--no-loop] '
             '[-R --related|--no-related] '
             '[-p max_per_url] '
             '[-P max_per_page] '
             '[-s {youtube, dailymotion}] '
             '[--snmp] '
             '[-t time_frame] '
             '[-n ping_packets] '
             '[-D download_time] '
             '[-S delay_between_requests] '
             #'[-B buffering_video_duration] '
             #'[-M min_playout_buffer_size] '
             '[-x, --no-log-ip] '
             '[-c, --no-centralize] '
             '[--http-proxy=http://proxy:8080] '
             '[--provider=MY_ISP] '
             '[--download-extra-dns] '
             '[-L log_level] '
             '[-f, --input_file input_file_list] '
             '[input_urls]')
    parser = OptionParser(usage=usage)
    create_options(parser)
    (options, input_urls) = parser.parse_args(argv)
    check_options(parser, options)
    write_options_to_config(options)
    timestamp = strftime('%Y-%m-%d.%H_%M_%S')
    log_file = configure_log_file(timestamp)
    image_file = None
    if not log_file:
        return -1
    try:
        result_file = check_out_files(config_pytomo.RESULT_FILE,
                                      config_pytomo.RESULT_DIR, timestamp)
    except IOError:
        result_file = None
    if result_file:
        print( 'Text results are there: %s' % result_file)
    try:
        db_file = check_out_files(config_pytomo.DATABASE,
                                  config_pytomo.DATABASE_DIR, timestamp)
    except IOError:
        db_file = None
    if db_file:
        print('Database results are there: %s' % db_file)
    if config_pytomo.SNMP:
        set_up_snmp()
    config_pytomo.LOG.critical('Offset between local time and UTC: %d',
                               timezone)
    config_pytomo.LOG.warn('Pytomo version = %s', version)
    config_pytomo.SYSTEM = platform.system()
    config_pytomo.LOG.warn('Pytomo is running on this system: %s',
                           config_pytomo.SYSTEM)
    if config_pytomo.PLOT:
        try:
            image_file = check_out_files(config_pytomo.IMAGE_FILE,
                                    config_pytomo.IMAGE_DIR, timestamp)
        except IOError:
            image_file = None
        if image_file:
            print('Plots are here: %s' % image_file)
        else:
            print('Unable to create image_file')
    # do NOT prompt for start if BATCH_MODE on (no input expected from user)
    if not options.BATCH_MODE:
        while True:
            start_crawl = prompt_start_crawl()
            if start_crawl.startswith('N'):
                return 0
            elif start_crawl.startswith('Y'):
                break
        if not options.PROVIDER:
            log_provider(timeout=config_pytomo.USER_INPUT_TIMEOUT)
        else:
            config_pytomo.LOG.critical('Provider given at command line: %s',
                                       options.PROVIDER)
        if not options.PROXIES:
            set_proxies_cli(timeout=config_pytomo.USER_INPUT_TIMEOUT*2)
        else:
            config_pytomo.LOG.critical('Proxies given at command line: %s\n',
                                       options.PROXIES)
    set_max_crawls(timeout=config_pytomo.USER_INPUT_TIMEOUT,
                   prompt=(False if options.BATCH_MODE else True),
                   nb_max_crawls=options.MAX_CRAWLED_URLS)
    # log IP after proxies given by the user
    if config_pytomo.LOG_PUBLIC_IP:
        log_ip_address()
    print('Type Ctrl-C to interrupt crawl')
    result_stream = None
    # memory monitoring module
    if result_file:
        result_stream = open(result_file, 'w')
    if input_urls:
        config_pytomo.STATIC_URL_LIST = (config_pytomo.STATIC_URL_LIST
                                         + input_urls)
    if config_pytomo.INPUT_FILE:
        try:
            with open(config_pytomo.INPUT_FILE, 'r') as input_file:
                for line in input_file.readlines():
                    config_pytomo.STATIC_URL_LIST.append(line.strip())
        except IOError, mes:
            config_pytomo.LOG.exception(mes)
            parser.error('Problem reading input file: %s'
                         % config_pytomo.INPUT_FILE)
    config_pytomo.LOG.debug('Service for most popular links %s',
                            options.CRAWL_SERVICE)
    try:
        do_crawl(result_stream=result_stream, db_file=db_file,
                 image_file=image_file, timestamp=timestamp,
                 loop=config_pytomo.LOOP, related=config_pytomo.RELATED,
                 hd_first=config_pytomo.HD_FIRST)
    except config_pytomo.BlackListException:
        err_mes = ('Crawl detected by YouTube: '
                   'log to YouTube and enter captcha')
        config_pytomo.LOG.critical(err_mes)
        print(err_mes)
    except KeyboardInterrupt:
        print('\nCrawl interrupted by user')
        config_pytomo.LOG.critical('Crawl interrupted by user')
    except Exception, mes:
        config_pytomo.LOG.exception('Uncaught exception: %s', mes)
    config_pytomo.LOG.debug(CACHED_PREFIXES)
    if config_pytomo.PLOT:
        lib_plot.plot_data(db_file, config_pytomo.COLUMN_NAMES,
                           image_file)
    if result_file:
        result_stream.close()
    log_md5_results(result_file, db_file)
    print('Compressing the files: wait a bit')
    tarfile_name = check_out_files('to_send.tbz',
                                   config_pytomo.LOG_DIR, timestamp)
    tar_file = tarfile.open(name=tarfile_name, mode='w:bz2')
    tar_file.add(db_file, arcname=os.path.basename(db_file))
    if type(log_file) == str:
        tar_file.add(log_file, arcname=os.path.basename(log_file))
    tar_file.close()
    # upload archive on the FTP server
    if options.CENTRALISE_DATA:
        print('Trying to upload the files on the centralisation server...\n')
        ftp = lib_data_centralisation.PytomoFTP()
        if ftp.created:
            if (ftp.upload_file(tarfile_name) !=
                lib_data_centralisation.ERROR_CODE):
                print('\nFile %s has been uploaded on %s server.' %
                      (tarfile_name, config_pytomo.CENTRALISATION_SERVER))
                return 0
            else:
                print('\nWARNING! File %s was not uploaded to %s server.' %
                      (tarfile_name, config_pytomo.CENTRALISATION_SERVER))
            ftp.close_connection()
        else:
            print('\nWARNING! Could not establish connection to %s FTP server.'
                  % (config_pytomo.CENTRALISATION_SERVER))
    print('\nCrawl finished.\n%s\n\nPLEASE SEND THIS FILE BY EMAIL: '
           '(to pytomo@gmail.com)\n%s\n'
           % (SEPARATOR_LINE, tarfile_name))
    if not options.BATCH_MODE:
        raw_input('Press Enter to exit\n')
    return 0

if __name__ == '__main__':
    import doctest
    doctest.testmod()
