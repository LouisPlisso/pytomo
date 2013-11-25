#!/usr/bin/env python2
#
#    Pytomo: Python based tomographic tool to perform analysis of Youtube video
#    download rates.
#    Copyright (C) 2011, Louis Plissonneau, Parikshit Juluri, Mickael Meulle
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#



"""Adapted from lib_youtube_download.py to Dailymotion
Module to download Dailymotion video for a limited amount of time and
calculate the data downloaded within that time

    Usage:
        This module provides two classes: FileDownloader class and the
        InfoExtractor class.
        This module is not meant to be called directly.
"""

from __future__ import with_statement, absolute_import
import httplib
import re
import socket
import urllib
import urllib2

try:
    from . import lib_links_extractor
except ValueError:
    import lib_links_extractor
from . import config_pytomo
from . import lib_general_download
try:
    from .lib_dailymotion_api import get_id, set_id
except ValueError:
    from lib_dailymotion_api import get_id, set_id

HTTP_ERROR_FORBIDDEN_403 = 403
HTTP_REQUESTED_RANGE_NOT_SATISFIABLE_416 = 416
HTTP_INTERNAL_SERVER_ERROR_500 = 500
HTTP_SERVER_ERROR_UNKNOWN_599 = 599

class DailymotionIE(lib_general_download.InfoExtractor):
    """Information Extractor for Dailymotion"""

    _VALID_URL = (r'(?i)(?:https?://)?(?:www\.)?dailymotion\.[a-z]{2,3}/'
                  + 'video/([^_/]+)(_([^/]+))*')
    _URL_GROUP_NB = 1
    _URL_GROUP_NB_VIDEO_ID = 1
    IE_NAME = u'dailymotion'

    @staticmethod
    def suitable(url):
        """ Returns True if URL is suitable to this IE else False
        >>> die = DailymotionIE(InfoExtractor)
        >>> die.suitable('http://www.dailymotion.com/video/xscdm4_le-losc-au-pays-basque_sport?no_track=1')
        True
        >>> die.suitable('http://www.dailymotion.com')
        False
        >>> die.suitable('http://vid.ec.dmcdn.net/cdn/H264-512x384/video/xscdm4.mp4?77838fedd64fa52abe6a11b3bdbb4e62f4387ebf7cbce2147ea4becc5fe6574d7c3ec5681aa355d923bdca173f151658eefcd8763fc08a9380a7e2f26cbe49b67e583118fb414738b9d3e9db8882d33200be&ec_prebuf=20&ec_rate=68')
        True
        """
        return (re.match(DailymotionIE._VALID_URL, url) is not None)

#    def __init__(self, downloader=None):
#        InfoExtractor.__init__(self, downloader)

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        self._downloader.to_screen(u'[dailymotion] %s: Downloading webpage' %
                                   video_id)

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[dailymotion] %s: Extracting information' %
                                   video_id)

    def get_webpage(self, video_id, url):
        'Retrieve video webpage to extract further information'
        request = urllib2.Request(url)
        # AO 20121031
        request.add_header('Cookie', 'family_filter=on')
        #request.add_header('Cookie', 'family_filter=off')
        try:
            self.report_download_webpage(video_id)
            webpage = urllib2.urlopen(request,
                                      timeout=config_pytomo.URL_TIMEOUT).read()
        except (urllib2.URLError, httplib.HTTPException, socket.error), err:
            self._downloader.trouble(u'ERROR: unable retrieve video webpage: %s'
                                     % str(err))
            return
        return webpage

    def get_media_url(self, video_id, webpage):
        'Extract URL, uploader and title from webpage'
        self.report_extraction(video_id)
        mobj = re.search(r'(?i)addVariable\(\"sequence\"\s*,\s*\"([^\"]+?)\"\)',
                         webpage)
        if mobj is None:
            #self._downloader.trouble(u'ERROR: unable to extract media URL')
            config_pytomo.LOG.debug(u'Unable to extract media URL, '
                                    'trying new method')
            mobj = re.search(r'"video_url":"(.*?)",', urllib.unquote(webpage))
            if mobj:
                return urllib.unquote(mobj.group(1))
            return
        sequence = urllib.unquote(mobj.group(1))
        mobj = re.search(r',\"sdURL\"\:\"([^\"]+?)\",', sequence)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract media URL')
            return
        mediaURL = urllib.unquote(mobj.group(1)).replace('\\', '')
        return mediaURL

    def get_video_info(self, url):
        'Return the video url extracted by _real_extract'
        return self._real_extract(url)

    def _real_extract(self, url):
        'Extract id and simplified title from URL'
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return
        video_id = mobj.group(self._URL_GROUP_NB_VIDEO_ID)
        # check for new formats
        video_extension = 'flv'
        webpage = self.get_webpage(video_id, url)
        if not webpage:
            return
        mediaURL = self.get_media_url(video_id, webpage)
        if not mediaURL:
            return
        # if needed add http://www.dailymotion.com/ if relative URL
        video_url = mediaURL
#        mobj = re.search(r'<meta property="og:title" content="(?P<title>[^"]*)" />',
#                         webpage)
#        if mobj is None:
#            self._downloader.trouble(u'ERROR: unable to extract title')
#            return
#        video_title = _unescapeHTML(mobj.group('title').decode('utf-8'))
#        video_title = sanitize_title(video_title)
#        simple_title = _simplify_title(video_title)
#        mobj = re.search(r'(?im)<span class="owner[^\"]+?">[^<]+?<a [^>]+?>([^<]+?)</a></span>', webpage)
#        if mobj is None:
#            self._downloader.trouble(u'ERROR: unable to extract uploader nickname')
#            return
#        video_uploader = mobj.group(1)
        try:
            # Process video information
            self._downloader.process_info({
                'id':        video_id.decode('utf-8'),
                'url':        video_url.decode('utf-8'),
                #'uploader':    video_uploader.decode('utf-8'),
                'upload_date':    u'NA',
                #'title':    video_title,
                #'stitle':    simple_title,
                'ext':        video_extension.decode('utf-8'),
                'format':    u'NA',
                'player_url':    None,
            })
        except lib_general_download.UnavailableVideoError:
            self._downloader.trouble(u'\nERROR: unable to download video')
        return video_url

def get_dailymotion_info_extractor(download_time=config_pytomo.DOWNLOAD_TIME):
    "Return an info extractor for Dailymotion with correct mocks"
    dailymotion_ie = DailymotionIE()
    # only to have trouble/to_screen functions in case of errors
    file_downloader = lib_general_download.FileDownloader(download_time)
    file_downloader.add_info_extractor(dailymotion_ie)
    # Mock because only partial consturction of object
    dailymotion_ie.report_video_webpage_download = (lambda x:
                            config_pytomo.LOG.debug("Download webpage %s" % x))
    return dailymotion_ie

# hd_first to implement
def get_cache_url(url, redirect=False, hd_first=False):
    ''' Return the cache url of the video (Wrote mock test).
    Cache url is returned as the first redirect from dailymotion.com or as the
    video url on dailymotion.
    '''
    if redirect:
        return url
    dailymotion_ie = get_dailymotion_info_extractor(config_pytomo.DOWNLOAD_TIME)
    # AO 03122012
    # in the database, the url is saved with its complete title (lots of
    # unescaped characters), should only use ID to retrieve cache
    url = set_id(get_id(url, False))
    mobj = re.match(dailymotion_ie._VALID_URL, url)
    if not mobj:
        config_pytomo.LOG.warning('\n'.join(('url: %s not valid' % url,
                                'only Dailymotion download is implemented')))
    #video_id = mobj.group(dailymotion_ie._URL_GROUP_NB_VIDEO_ID)
    try:
        video_url = dailymotion_ie.get_video_info(url)
    except lib_general_download.DownloadError, mes:
        config_pytomo.LOG.error(mes)
        config_pytomo.LOG.debug('Video url not found for %s!' % url)
        return None
    except Exception, mes:
        config_pytomo.LOG.exception('Uncaught exception: %s' % mes)
        config_pytomo.LOG.debug('Video url not found!')
        return None
    if video_url:
        config_pytomo.LOG.debug('Video url found: %s' % video_url)
        #return video_url
        # AO 20121030 cache url is the first redirect from the dailymotion link
        response = lib_links_extractor.retrieve_header(video_url)
        if response:
            return response.geturl()
        else:
            return video_url

if __name__ == '__main__':
    import doctest
    doctest.testmod()

