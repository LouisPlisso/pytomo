#!/usr/bin/env python
''' Module to interact with the Dailymotion API:
    - function to get the most popular dailymotion videos according to the time
    frame (adapted from lib_youtube_api);
    - function to retrieve the related videos from the Dailymotion api in a
    list of links.

Author: Ana Oprea
Date: 04.09.2012 - modified 17.09.2012 for related links

Usage:
To use the functions provided in this module independently, first place yourself
just above pytomo folder.Then:

>>> import pytomo.start_pytomo as start_pytomo
>>> TIMESTAMP = 'test_timestamp'
>>> start_pytomo.configure_log_file(TIMESTAMP)

>>> import pytomo.lib_dailymotion_api as lib_dailymotion_api
>>> url = 'http://www.dailymotion.com/video/xkqa0p'
>>> time_f = 'today' # choose from 'today' or 'month' or 'week' or all_time'
>>> max_results = 20
>>> lib_dailymotion_api.get_popular_links(time_f, max_results)
>>> max_per_page = 25
>>> max_per_url = 10
>>> lib_dailymotion_api.get_dailymotion_links(url, max_per_page)
>>> lib_dailymotion_api.get_related_urls(url, max_per_page, max_per_url)
'''
from __future__ import with_statement, absolute_import
import urllib2
import random
from ast import literal_eval
import re
from operator import itemgetter
import time
try:
    from . import lib_links_extractor
except ValueError:
    import lib_links_extractor
# global config
try:
    from . import config_pytomo
except ValueError:
    import config_pytomo

MAX_VIDEO_PER_PAGE = 20
# dailymotion links
DM_LINK = 'http://www.dailymotion.com'
CHARTS_URL = 'http://www.dailymotion.com/{country}/{time_frame}/%{page}'
COUNTRY = 'fr'
DM_API_LINK = 'https://api.dailymotion.com/video/%s/related?fields=id,title&limit=%i'
DM_VIDEO_LINK = 'http://www.dailymotion.com/video/'
# limitation of Dailymotion API
MAX_PER_PAGE_DM_API = 100
# the page returned by the Dailymotion API with related links is not well
# formed, some words need to be replaced
TRUTH_DICT = {'true': 'True', 'false':'False'}
# parameters to be retrieved from the Dailymotion API
DM_URL_ID_FIELD = 'id'
DM_URL_TITLE_FIELD = 'title'
DM_URL_LIST_FIELD = 'list'
# text used to retrieve the correct id of a video
TEXT_TO_PARTITION_ID = 'mp4'
# number of attempts to try to retrieve the related links
MAX_ATTEMPTS = 1

def get_id(url, keep_all=True):
    ''' Return the id of a Dailymotion url.
    >>> url = 'http://www.dailymotion.com/video/xkqa0p'
    >>> get_id(url)
    'xkqa0p'
    >>> url = 'http://www.dailymotion.com/video/xkqa0p_angry-birds-theme-covered-by-pomplamoose_music'
    >>> get_id(url)
    'xkqa0p'
    >>> url = 'http://www.dailymotion.com/video/xkqa0p?background=493D27&foreground=E8D9AC&highlight=FFFFF0&autoPlay=1'
    >>> get_id(url)
    'xkqa0p'
    >>> url = 'http://vid.ak.dmcdn.net/video/986/034/42430689_mp4_h264_aac.mp4?primaryToken=1343398942_d77027d09aac0c5d5de74d5428fb9e5b'
    >>> get_id(url)
    '42430689'
    >>> url = 'http://www.dailymotion.com/video/xscdm4_le-losc-au-pays-basque_sport?no_track=1'
    >>> get_id(url)
    'xscdm4'
    >>> url = 'http://vid.ec.dmcdn.net/cdn/H264-512x384/video/xmcyww.mp4?77838fedd64fa52abe6a11b3bdbb4e62f4387ebf7cbce2147ea4becc5eee5c418aaa6598bb98a61fc95a02997247e59bfb0dcd58cdf05c1601ded04f75ae357b225da725baad5e97ea6cce6d6a12e17d1c01'
    >>> get_id(url)
    'xmcyww'
    >>> url = 'http://proxy-60.dailymotion.com/video/246/655/37556642_mp4_h264_aac.mp4?auth=1343399602-4098-bdkyfgul-eb00ad223e1964e40b327d75367b273b'
    >>> get_id(url)
    '37556642'
    >>> url = 'http://docs.python.org/tutorial/inputoutput.html'
    >>> get_id(url)
    'inputoutput.html'
    '''
    # get the url without parameters (split at '?')
    # get the last part of the url (split at '/')
    # get the last element of the split
    url_id = (url.split('?')[0]).split('/')[-1]
    if keep_all:
        return url_id
    if url_id.find(TEXT_TO_PARTITION_ID) == -1:
        return url_id.split('_')[0]
    else:
        # split at the first 'mp4' and retrieve first part
        # retrieve before last element (that is '_' or '.')
        return (url_id.partition(TEXT_TO_PARTITION_ID)[0][:-1]).split('_')[0]

# TODO: check outside this function if the ID is not a Dailymotion link
def set_id(url_id):
    ''' Return the complete link of a Dailymotion url.
    >>> url_id = 'x1y0ap'
    >>> set_id(url_id)
    'http://www.dailymotion.com/video/x1y0ap'
    '''
    return ''.join((DM_VIDEO_LINK, url_id))

def get_time_frame_global(input_time=config_pytomo.TIME_FRAME):
    ''' Returns the time frame in the form accepted by youtube_api
    >>> get_time_frame('today')
    'popular-today'
    >>> get_time_frame('week')
    'popular-week'
    >>> get_time_frame('month')
    'popular-month'
    >>> get_time_frame('all_time')
    'popular'
    '''
    if input_time == 'today':
        time_frame = 'popular-today'
    elif input_time == 'week':
        time_frame = 'popular-week'
    elif input_time == 'month':
        time_frame = 'popular-month'
    elif input_time == 'all_time':
        time_frame = 'popular'
    else:
        config_pytomo.LOG.info('Time frame not recognised. '
                               'Assuming All time Popular videos.')
        time_frame = 'popular'
    return time_frame

def get_time_frame(input_time=config_pytomo.TIME_FRAME):
    ''' Returns the time frame in the form accepted by youtube_api
    >>> get_time_frame('today')
    'popular-today'
    >>> get_time_frame('week')
    'popular-week'
    >>> get_time_frame('month')
    'popular-month'
    >>> get_time_frame('all_time')
    'popular'
    '''
    if input_time == 'today':
        time_frame = 'visited-today'
    elif input_time == 'week':
        time_frame = 'visited-week'
    elif input_time == 'month':
        time_frame = 'visited-month'
    elif input_time == 'all_time':
        time_frame = 'popular'
    else:
        config_pytomo.LOG.info('Time frame not recognised. '
                               'Assuming All time Popular videos.')
        time_frame = 'popular'
    return time_frame

def get_popular_links(input_time=config_pytomo.TIME_FRAME,
                      max_results=config_pytomo.MAX_PER_PAGE):
    '''Returns the most popular dailymotion links for France.
    The country should be set as parameter in start_pytomo if user should
    specify it.
    The number of videos returned is given as Total_pages.
    (The results returned are in no particular order).
    A set of only dailymotion links from url
    '''
    config_pytomo.LOG.debug('Getting popular links per country')
    time_frame = get_time_frame(input_time)
    if max_results > MAX_VIDEO_PER_PAGE:
        pages = int(max_results) / MAX_VIDEO_PER_PAGE
    else:
        pages = 1
    for page in xrange(pages):
        url = CHARTS_URL.format(country=COUNTRY, time_frame=time_frame,
                                page=(page + 1))
        links = lib_links_extractor.get_all_links(url)
        if not links:
            config_pytomo.LOG.warning('No popular link was found')
        popular_links = set()
        for link in links:
            if link.find(r'/video/') >= 0:
                if link.startswith('/'):
                    link = ''.join((DM_LINK, link))
                popular_links.add(link)
                if len(popular_links) >= max_results:
                    break
    return popular_links

def get_all_related_ids(url, max_per_page):
    ''' Parse and return a list of the ids of the related videos from the
    Dailymotion api:
        - use:
        https://api.dailymotion.com/video/ID/related?fields=id&limit=NR
        - example online:
        http://www.dailymotion.com/doc/api/explorer#/video/related/list
    >>> get_all_related_ids('http://www.dailymotion.com/video/xv7ent', 20)
    ['xv8xoj', 'xvajbn', 'xvbhdi', 'xvam4y', 'xv8x1t', 'xv8sn2', 'xvbx1x',
     'xv7gkf', 'xv5cnr', 'xvajng', 'xv9ir4', 'xvakfr', 'xv9hjr', 'xvbwax',
     'xv8ttw', 'xv75ou', 'xv587j', 'xvakwj', 'xv8xqp', 'xv9ihm']
    '''
    # get the API link for only the URL id, cut the title
    url_dm_api = DM_API_LINK % (get_id(url, False),
                                min(max_per_page, MAX_PER_PAGE_DM_API))
    # added to solve timeout error when calling function from start_pytomo
    if config_pytomo.PROXIES:
        proxy = urllib2.ProxyHandler(config_pytomo.PROXIES)
        opener = urllib2.build_opener(proxy)
    else:
        opener = urllib2.build_opener()
    urllib2.install_opener(opener)
    request = urllib2.Request(url_dm_api, None, config_pytomo.STD_HEADERS)
    for attempt in xrange(MAX_ATTEMPTS):
        try:
            data = opener.open(request)
            break
        except urllib2.URLError, mes:
            sleep_secs = attempt ** 2
            config_pytomo.LOG.debug('ERROR: %s.\nRetrying in %s seconds...' %
                                    (mes, sleep_secs))
            time.sleep(sleep_secs)
    # data is malformed as a python structure because it contains 'true'
    # instead of True as bolean value, same for false
    pattern = re.compile("|".join(TRUTH_DICT.keys()))
    # TODO check error in case of readline()
    try:
        well_formed_data = pattern.sub(lambda m: TRUTH_DICT[m.group(0)],
                                       data.readline())
    except UnboundLocalError:
        config_pytomo.LOG.debug('Could not retrieve related links data')
        return None
    # parse the string in a dictionary
    try:
        related_dict = literal_eval(well_formed_data)
    except (ValueError, IndentationError, SyntaxError):
        config_pytomo.LOG.error('The data for related links of %s cannot be'
                                'parsed, malformed string' % url)
        return []
    try:
        list_dict = related_dict[DM_URL_LIST_FIELD]
    except KeyError:
        config_pytomo.LOG.error('The list of related links of %s cannot be'
                                ' retrieved' % url)
        return []
    try:
        id_title_list = map(itemgetter(DM_URL_ID_FIELD, DM_URL_TITLE_FIELD),
                            list_dict)
    except KeyError:
        config_pytomo.LOG.error('The id or title list of related links of %s '
                                'cannot be retrieved' % url)
        return []
    return ['_'.join((url_id, url_title))
            for (url_id, url_title) in id_title_list]

def get_dailymotion_links(url, max_per_page):
    ''' Return a set of only Dailymotion links from url'''
    # TODO: temporary, the proxy links shouldn't be urls
    if not ('dailymotion' in url or 'dmcdn' in url):
        config_pytomo.LOG.error("Only dailymotion is implemented, got url: %s"
                                % url)
        return None
    ids = get_all_related_ids(url, max_per_page)
    if ids:
        dailymotion_links = set()
        config_pytomo.LOG.info("Found %d links for url %s" % (len(ids), url))
        for url_id in ids:
            dailymotion_links.add(set_id(url_id))
        config_pytomo.LOG.info("Found %d related video links for url %s"
                                % (len(dailymotion_links), url))
        return dailymotion_links
    return None

def get_related_urls(url, max_per_page, max_per_url):
    ''' Return a set of max_links randomly chosen related urls'''
    dailymotion_links = get_dailymotion_links(url, max_per_page)
    try:
        selected_links = random.sample(dailymotion_links,
                                       min(max_per_url, len(dailymotion_links)))
    except TypeError:
        config_pytomo.LOG.debug('Could not retrieve related urls for %s' % url)
        return None
    config_pytomo.LOG.debug("Selected %d links for url %s"
                            % (len(selected_links), url))
    return selected_links

if __name__ == '__main__':
    import doctest
    doctest.testmod()
