#!/usr/bin/env python2

import re

from .lib_general_download import FileDownloader
from . import config_pytomo
from . import lib_links_extractor

PATTERN_API_URL = 'api.dmcloud.net'
PATTERN_MP4_URL = 'mp4_url'
HD_ADD_ON = '_hd'
PATTERN_CDN_URL = 'cdn.dmcloud.net'
HTML_API_LSTRIP = 'src="'
HTML_API_RSTRIP = '"'
HTML_CDN_STRIP = '",'

#TODO: edgecast proxy?
REGEXP_VIDEO_URL = '(http://proxy-\d\d.dmcloud.net/\w{24}/\w{24}/mp4_h264_aac)(.*)'

establish_connection = FileDownloader.establish_connection

def transform_link_hd(url):
    '''Return a video url corresponding to HD link
    >>> transform_link_hd('http://proxy-03.dmcloud.net/4f84ab1b06361d40e7000125/501646dff325e1778d0000c6/mp4_h264_aac-1343630420.flv?auth=1355226445-1-eiswpfhh-3ef0569686549e129d4038a78a28cac6')
    'http://proxy-03.dmcloud.net/4f84ab1b06361d40e7000125/501646dff325e1778d0000c6/mp4_h264_aac_hd-1343630420.flv?auth=1355226445-1-eiswpfhh-3ef0569686549e129d4038a78a28cac6'
    >>> transform_link_hd('http://proxy-03.dmcloud.net/4f84ab1b06361d40e7000125/501646dff325e1778d0000c6/mp4_h264_aac_hd-1343630420.flv?auth=1355226445-1-eiswpfhh-3ef0569686549e129d4038a78a28cac6&start=5')
    'http://proxy-03.dmcloud.net/4f84ab1b06361d40e7000125/501646dff325e1778d0000c6/mp4_h264_aac_hd-1343630420.flv?auth=1355226445-1-eiswpfhh-3ef0569686549e129d4038a78a28cac6&start=5'
    '''
    config_pytomo.LOG.debug('in url for hd: %s' % url)
    if PATTERN_MP4_URL + HD_ADD_ON in url:
        return url
    url_groups = re.match(REGEXP_VIDEO_URL, url)
    if url_groups:
        hd_url = ''.join((url_groups.group(1), HD_ADD_ON, url_groups.group(2)))
        config_pytomo.LOG.debug('hd url: %s' % hd_url)
        return hd_url

def get_cache_url(url, hd_first=True):
    '''Return the url of the video
    for galerie video, just do a grep on api.dmcloud.net
    '''
    status_code, data = establish_connection(url)
    if not data:
        config_pytomo.LOG.error('could not establish connection to url: %s'
                                % url)
        return status_code, None
    # If there was a redirection for the cache url,
    # get the DNS resolution again.
    if status_code in config_pytomo.HTTP_REDIRECT_CODE_LIST:
        config_pytomo.LOG.info('URL redirected')
        #self.redirect_url = data.geturl()
        return status_code, None
    tmp_url = None
    for line in data.readlines():
        if PATTERN_API_URL in line:
            for item in line.split():
                if PATTERN_API_URL in item:
                    if tmp_url:
                        config_pytomo.LOG.error('multiple match for %s'
                                                % PATTERN_API_URL)
                    tmp_url = item.lstrip(HTML_API_LSTRIP).rstrip(HTML_API_RSTRIP)
    if tmp_url:
        status_code, data = establish_connection(tmp_url)
    if not data:
        config_pytomo.LOG.error('could not establish connection to url: %s'
                                % tmp_url)
        return status_code, None
    # If there was a redirection for the cache url,
    # get the DNS resolution again.
    if status_code in config_pytomo.HTTP_REDIRECT_CODE_LIST:
        config_pytomo.LOG.info('URL redirected')
        #self.redirect_url = data.geturl()
        return status_code, None
    video_url = None
    for line in data.readlines():
        if PATTERN_MP4_URL:
            for item in line.split():
                if PATTERN_CDN_URL in item:
                    video_url = item.strip(HTML_CDN_STRIP)
    if video_url:
        # skip the first redirect for cdn.dmcloud.net
        config_pytomo.LOG.debug('Video url found: %s' % video_url)
        response = lib_links_extractor.retrieve_header(video_url)
        if response:
            video_url = response.geturl()
        if hd_first:
            return transform_link_hd(video_url)
        return video_url

if __name__ == '__main__':
    import doctest
    doctest.testmod()
