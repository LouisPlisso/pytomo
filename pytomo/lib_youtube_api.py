#!/usr/bin/env python
''' Function to get the most popular Youtube videos according to the time frame.
    Arguments:
        time = 'today' or 'month' or 'week' or all_time'
        max_results : In multiples of 25
    Returns: A list containing the list of videos.

   Usage: To use the functions provided in this module independently,
        first place yourself just above pytomo folder.Then:

        import pytomo.start_pytomo
        TIMESTAMP = 'test_timestamp'
        start_pytomo.configure_log_file(TIMESTAMP)

        import pytomo.lib_youtube_api as lib_youtube_api
        time = 'today' # choose from 'today' or 'month' or 'week' or all_time'
        max_results = 25
        time_frame = lib_youtube_api.get_time_frame(time)
        lib_youtube_api.get_popular_links(time_frame, max_results)
        url = 'http://www.youtube.com/watch?v=cv5bF2FJQBc'
        max_per_page = 25
        max_per_url = 10
        lib_youtube_api.get_youtube_links(url)
        lib_youtube_api.get_related_urls(url, max_per_page, max_per_url)
'''

from __future__ import with_statement, absolute_import
import random
import urllib, urllib2
import re

try:
    from . import lib_links_extractor
except (ValueError, ImportError):
    import lib_links_extractor
# global config
try:
    from . import config_pytomo
except (ValueError, ImportError):
    import config_pytomo

LINK_REG_EXP = r'/watch_videos?(.*&)?video_ids='

CHARTS_URL = ('http://www.youtube.com/charts/videos_views?p=2'
              '&gl={country}&t={time_frame}&p={page}')

# Youtube webpage limitation
MAX_VIDEO_PER_PAGE = 25

# Youtube default country for worldwide requests
GLOBAL_COUNTRY = 'US'

def get_time_frame(input_time=config_pytomo.TIME_FRAME):
    ''' Returns the time frame in the form accepted by youtube_api
    >>> from . import start_pytomo
    >>> start_pytomo.configure_log_file('doc_test') #doctest: +ELLIPSIS
    Configuring log file
    Logs are there: ...
    ...
    >>> get_time_frame('today')
    't'
    >>> get_time_frame('week')
    'w'
    >>> get_time_frame('month')
    'm'
    >>> get_time_frame('all_time')
    'a'
    >>> get_time_frame('other')
    'a'
    '''

    if input_time == 'today':
        time_frame = 't'
    elif input_time == 'week':
        time_frame = 'w'
    elif input_time == 'month':
        time_frame = 'm'
    elif input_time == 'all_time':
        time_frame = 'a'
    else:
        config_pytomo.LOG.info('Time frame not recognised. '
                               'Assuming All time Popular videos.')
        time_frame = 'a'
    return time_frame

def parse_watch_videos_link(link):
    '''Return the list of links from a list
    >>> parse_watch_videos_link('http://www.youtube.com/watch_videos?video_ids=pRpeEdMmmQ0%2CKyXW64L-XZA%2Czut0ruLWYMg%2C6O4uwy4eJhY%2CkffacxfA7G4%2CXEQv5rTRJd0%2CfhCIDe92iKQ%2C5H59Py7KApU%2CKQ6zr6kCPj8&index=1&title=Most+Popular+in+All+Categories+All+Time&feature=c4-overview&type=0&more_url=')
    ['http://youtube.com/watch?v=pRpeEdMmmQ0',
     'http://youtube.com/watch?v=KyXW64L-XZA',
     'http://youtube.com/watch?v=zut0ruLWYMg',
     'http://youtube.com/watch?v=6O4uwy4eJhY',
     'http://youtube.com/watch?v=kffacxfA7G4',
     'http://youtube.com/watch?v=XEQv5rTRJd0',
     'http://youtube.com/watch?v=fhCIDe92iKQ',
     'http://youtube.com/watch?v=5H59Py7KApU',
     'http://youtube.com/watch?v=KQ6zr6kCPj8']
    '''
    video_ids = urllib.unquote(urllib2.urlparse.urlsplit(link).query
                              ).split('video_ids=')[1].split('&')[0].split(',')
    return [''.join(('http://youtube.com/watch?v=', video_id)) for video_id in video_ids]

def get_popular_links(input_time=config_pytomo.TIME_FRAME,
                      max_results=config_pytomo.MAX_PER_PAGE,
                      country=GLOBAL_COUNTRY):
    '''Returns the most popular youtube links (world-wide).
    The number of videos returned is given as Total_pages.
    (The results returned are in no particular order).
    A set of only Youtube links from url
    '''
    config_pytomo.LOG.debug('Getting popular links')
    if not country:
        country = GLOBAL_COUNTRY
    time_frame = get_time_frame(input_time)
    if max_results > MAX_VIDEO_PER_PAGE:
        pages = int(max_results) / MAX_VIDEO_PER_PAGE
    else:
        pages = 1
    for page in xrange(pages):
        url = CHARTS_URL.format(country=country, time_frame=time_frame,
                                page=(page + 1))
        links = lib_links_extractor.get_all_links(url)
        if not links:
            config_pytomo.LOG.warning('No popular link was found')
        popular_links = set()
        matcher = re.compile(LINK_REG_EXP)
        for link in links:
            config_pytomo.LOG.debug('found link: %s' % link)
            if link.find(r'/watch?v=') >= 0:
                if link.startswith('/'):
                    link = ''.join(("http://www.youtube.com", link))
                popular_links.add(link)
                if len(popular_links) >= max_results:
                    break
            if matcher.search(link) >= 0:
                config_pytomo.LOG.debug('videos_ids input link: %s' % link)
                video_links = parse_watch_videos_link(link)
                for video_link in video_links:
                    popular_links.add(video_link)
                    if len(popular_links) >= max_results:
                        break
    config_pytomo.LOG.debug('popular links are: %s' % popular_links)
    return popular_links

def get_youtube_links(url, max_per_page):
    "Return a set of only Youtube links from url"
    if not ('youtube' in url or 'youtu.be' in url):
        config_pytomo.LOG.error("Only youtube is implemented, got url: %s"
                                % url)
        return []
    links = lib_links_extractor.get_all_links(url)
    youtube_links = set()
    config_pytomo.LOG.info("Found %d links for url %s" % (len(links), url))
    for link in links:
        if link.find("/watch") >= 0:
            if link.startswith('/'):
                link = ''.join(("http://www.youtube.com", link))
            youtube_links.add(link)
            if len(youtube_links) >= max_per_page:
                break
    config_pytomo.LOG.info("Found %d related video links for url %s"
                            % (len(youtube_links), url))
    return youtube_links

def trunk_url(url):
    ''' Return the interesting part of a Youtube url
    >>> url= 'http://www.youtube.com/watch?v=hE0207sxaPg&feature=hp_SLN&list=SL'
    >>> trunk_url(url)  #doctest: +NORMALIZE_WHITESPACE
    'http://www.youtube.com/watch?v=hE0207sxaPg'
    >>> url = 'http://www.youtube.com/watch?v=y2kEx5BLoC4& \
    ... feature=list_related&playnext=1&list=MLGxdCwVVULXfxx-61LMYHbwpcwAvZd-rI'
    >>> trunk_url(url)  #doctest: +NORMALIZE_WHITESPACE
     'http://www.youtube.com/watch?v=y2kEx5BLoC4'
    >>> url = 'http://www.youtube.com/watch?v=UC-RFFIMXlA'
    >>> trunk_url(url)  #doctest: +NORMALIZE_WHITESPACE
    'http://www.youtube.com/watch?v=UC-RFFIMXlA'
    '''
    return url.split('&', 1)[0]

def get_related_urls(url, max_per_page, max_per_url):
    "Return a set of max_links randomly chosen related urls"
    youtube_links = get_youtube_links(url, max_per_page)
    selected_links = map(trunk_url,
                         random.sample(youtube_links,
                                       min(max_per_url, len(youtube_links))))
    config_pytomo.LOG.debug("Selected %d links for url %s"
                            % (len(selected_links), url))
    return selected_links


if __name__ == '__main__':
    import doctest
    doctest.testmod()
