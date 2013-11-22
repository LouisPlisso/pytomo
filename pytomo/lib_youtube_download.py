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



"""Module to download youtube video for a limited amount of time and
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

# for python2.5 only
from cgi import parse_qs

from . import config_pytomo
from . import lib_general_download

class YoutubeIE(lib_general_download.InfoExtractor):
    """Information extractor for youtube.com."""

    _VALID_URL = (r'^((?:https?://)?(?:youtu\.be/|(?:\w+\.)?'
                  r'youtube(?:-nocookie)?\.com/(?:(?:v/)'
                  r'|(?:(?:watch(?:_popup)?(?:\.php)?)?(?:\?|#!?)(?:.+&)?'
                  r'v=))))?([0-9A-Za-z_-]+)(?(1).+)?$')
#    _VALID_URL = (r'(?:(?:(?:https?://)?(?:\w+\.)?youtube\.com/'
#                  '(?:user/)?(?!(?:attribution_link|watch)'
#                  '(?:$|[^a-z_A-Z0-9-])))|ytuser:)(?!feed/)([A-Za-z0-9_-]+)')
    _VALID_URL_CHANNEL = (r'^(?:https?://)?(?:youtu\.be|(?:\w+\.)?youtube'
                          '(?:-nocookie)?\.com)/channel/([0-9A-Za-z_-]+)')
    _TEMPLATE_URL_CHANNEL = (r'http://www.youtube.com/channel/%s/videos?'
                             'sort=da&flow=list&view=0&page=%s&gl=US&hl=en')
    _URL_GROUP_NB_VIDEO_ID = 2
    #_LANG_URL = (r'http://www.youtube.com/?' +
                 #r'hl=en&persist_hl=1&gl=US&persist_gl=1&opt_out_ackd=1')
    #_LOGIN_URL = 'https://www.youtube.com/signup?next=/&gl=US&hl=en'
    #_AGE_URL = 'http://www.youtube.com/verify_age?next_url=/&gl=US&hl=en'
    #_NETRC_MACHINE = 'youtube'
    # Listed in order of quality
    _available_formats_hd_first = ['38', '37', '22', '45', '35', '34', '43',
                                   '18', '6', '5', '17', '13']
    # Listed in usual browser way
    _available_formats = ['34', '18', '43', '35', '22', '45', '38', '5', '17',
                          '37', '6', '13']
    _hd_first = False
    _video_extensions = {
        '13': '3gp',
        '17': 'mp4',
        '18': 'mp4',
        '22': 'mp4',
        '37': 'mp4',
        # You actually don't know if this will be MOV, AVI or whatever
        '38': 'video',
        '43': 'webm',
        '45': 'webm',
    }

    @staticmethod
    def suitable(url):
        """ Returns True if URL is suitable to this IE else False
        >>> yie = YoutubeIE(InfoExtractor)
        >>> yie.suitable('http://www.youtube.com/watch?v=rERIxeYOYhI')
        True
        >>> yie.suitable('http://www.youtube.com')
        False
        >>> yie.suitable('http://www.youtube.com/watch?v=-VB2dHVNyds&amp')
        True
        >>> yie.suitable('http://www.youtube.com/watch?')
        False
        >>> yie.suitable('http://youtu.be/3VdOTTfSKyM')
        True
        """
        return (re.match(YoutubeIE._VALID_URL, url) is not None)

    def report_lang(self):
        """Report attempt to set language."""
        self._downloader.to_screen(u'[youtube] Setting language')

    def report_video_webpage_download(self, video_id):
        """Report attempt to download video webpage."""
        self._downloader.to_screen(u'[youtube] %s: Downloading video webpage'
                                   % video_id)

    def report_infopage_download(self, video_id):
        """Report attempt to download video info webpage."""
        self._downloader.to_screen(
            u'[youtube] %s: Downloading video info webpage' % video_id)

    def report_information_extraction(self, video_id):
        """Report attempt to extract video information."""
        self._downloader.to_screen(
            u'[youtube] %s: Extracting video information' % video_id)

    def get_video_info(self, video_id):
        """Get video info
        Return the video
        """
        self.report_video_webpage_download(video_id)
        video_info = None
        for el_type in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
            video_info_url = ('http://www.youtube.com/get_video_info?\
&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (video_id, el_type))
            request = urllib2.Request(video_info_url, None,
                                      config_pytomo.STD_HEADERS)
            if config_pytomo.PROXIES:
                proxy = urllib2.ProxyHandler(config_pytomo.PROXIES)
                opener = urllib2.build_opener(proxy)
                urllib2.install_opener(opener)
            try:
                video_info_webpage = urllib2.urlopen(request,
                                     timeout=config_pytomo.URL_TIMEOUT).read()
                video_info = parse_qs(video_info_webpage)
                if 'token' in video_info:
                    break
            except (urllib2.URLError, httplib.HTTPException, socket.error), err:
                self._downloader.trouble(
                    u'ERROR: unable to download video info webpage: %s'
                    % str(err))
                return
        if 'token' not in video_info:
            if 'reason' in video_info:
                self._downloader.trouble(u'ERROR: YouTube said: %s'
                                         % video_info['reason'][0].decode(
                                             'utf-8'))
            else:
                self._downloader.trouble(u'ERROR: "token" parameter not in'
                                         'video info for unknown reason')
            return None
        config_pytomo.LOG.debug(video_info.keys())
        config_pytomo.LOG.debug(video_info['token'])
        return video_info

    @staticmethod
    def get_swf(video_webpage, mobj):
        "Attempt to extract SWF player URL"
        mobj = re.search(r'swfConfig.*?"(http:\\/\\/.*?watch.*?-.*?\.swf)"',
                         video_webpage)
        if mobj is not None:
            player_url = re.sub(r'\\(.)', r'\1', mobj.group(1))
        else:
            player_url = None
        return player_url

    def get_video_url_list(self, video_id, video_token, video_info,
                           req_format=None):
        """Decide which formats to download with req_format (default is best
        quality)
        Return video url list
        """
        video_url_list = None
        #req_format = self._downloader.params.get('format', None)
        get_video_template = ('http://www.youtube.com/get_video?'
                              + 'video_id=%s&t=%s&eurl=&el=&ps=&asv=&fmt=%%s'
                              % (video_id, video_token))
        if 'fmt_url_map' in video_info:
            url_map = dict(tuple(pair.split('|', 1))
                           for pair in video_info['fmt_url_map'][0].split(','))
        elif ('url_encoded_fmt_stream_map' in video_info
              and len(video_info['url_encoded_fmt_stream_map']) >= 1):
            url_data_strs = video_info['url_encoded_fmt_stream_map'][0].\
                            split(',')
            url_data = [dict(pairStr.split('=') for pairStr in uds.split('&'))
                        for uds in url_data_strs]
            # AO 20120927 403 forbidden error on youtube since 2:30am
            #url_map = dict((ud['itag'], urllib.unquote(ud['url']))
            #               for ud in url_data)
            # fix inspired from: https://github.com/rg3/youtube-dl/issues/427
            try:
                url_map = dict((ud['itag'], urllib.unquote(ud['url']) +
                                '&signature=' + urllib.unquote(ud['sig']))
                               for ud in url_data)
            except KeyError:
                config_pytomo.LOG.warning('Could not retrieve itag, url or sig'
                                          ' to download the video')
                return None
#            format_limit = None
#            #self._downloader.params.get('format_limit', None)
#            if (format_limit is not None
#                and format_limit in self._available_formats):
#                format_list = self._available_formats[
#                    self._available_formats.index(format_limit):]
#            else:
        else:
            self._downloader.trouble(u'ERROR: no fmt_url_map or conn '
                                     'information found in video info: '
                                    '%s' % video_info)
            return None
        if self._hd_first:
            format_list = self._available_formats_hd_first
        else:
            format_list = self._available_formats
        existing_formats = [x for x in format_list if x in url_map]
        if len(existing_formats) == 0:
            self._downloader.trouble(
                u'ERROR: no known formats available for video')
            return None
        if req_format is None:
#        elif req_format is None and 'fmt_url_map' in video_info:
#            video_url_list = [(req_format, get_video_template
#                               % existing_formats[0])]
            video_url_list = [(existing_formats[0],
                               url_map[existing_formats[0]])]
            # first quality from format list (default qual)
        elif req_format == '-1':
            # All formats
            video_url_list = [(f, url_map[f]) for f in existing_formats]
        elif req_format in url_map:
            # Specific format
            video_url_list = [(req_format, url_map[req_format])]
        else:
            # Specific format
            video_url_list = [(req_format, get_video_template % req_format)]
        return video_url_list

    def _real_extract(self, url):
        "Extract informations from url"
        # Extract video id from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return
        video_id = mobj.group(self._URL_GROUP_NB_VIDEO_ID)
        try:
            video_info = self.get_video_info(video_id)
        except lib_general_download.DownloadError:
            return
        if not video_info:
            return
        # Start extracting information
        self.report_information_extraction(video_id)
        video_token = urllib.unquote_plus(video_info['token'][0])
        video_url_list = self.get_video_url_list(video_id, video_token,
                                                 video_info)
        for format_param, video_real_url in video_url_list:
            # At this point we have a new video
            self._downloader.set_format(format_param)
            # Extension
            video_extension = self._video_extensions.get(format_param, 'flv')
            # Find the video URL in fmt_url_map or conn paramters
            try:
                # Process video information
                self._downloader.process_info({
                    'id':       video_id.decode('utf-8'),
                    'url':      video_real_url.decode('utf-8'),
                    'ext':      video_extension.decode('utf-8'),
                    'format':   (format_param is None and u'NA'
                                 or format_param.decode('utf-8')),
                })
            except lib_general_download.UnavailableVideoError, _:
                self._downloader.trouble(u'ERROR: unable to download video '
                                         '(format may not be available)')

def get_youtube_info_extractor(download_time=config_pytomo.DOWNLOAD_TIME):
    "Return an info extractor for YouTube with correct mocks"
    youtube_ie = YoutubeIE()
    # only to have trouble/to_screen functions in case of errors
    config_pytomo.LOG.debug('instanciate a Youtube FileDownloader with '
                            'download_time: %s' % download_time)
    file_downloader = lib_general_download.FileDownloader(download_time)
    file_downloader.add_info_extractor(youtube_ie)
    # Mock because only partial consturction of object
    youtube_ie.report_video_webpage_download = (lambda x:
                            config_pytomo.LOG.debug("Download webpage %s" % x))
    return youtube_ie



def get_cache_url(url, redirect=False, hd_first=False):
    "Return the cache url of the video (Wrote mock test)"
    if redirect:
        return url
    youtube_ie = get_youtube_info_extractor()
    youtube_ie._hd_first = hd_first
    mobj = re.match(youtube_ie._VALID_URL, url)
#    if not mobj and 'channel' in url:
#        config_pytomo.LOG.debug('Trying channel url')
#        mobj = re.match(youtube_ie._VALID_URL_CHANNEL, url)
    if not mobj:
        config_pytomo.LOG.warning('\n'.join(('url: %s not valid' % url,
                                     'only YouTube download is implemented')))
        if config_pytomo.BLACK_LISTED in url:
            config_pytomo.LOG.error('Black listed url: %s' % url)
            raise config_pytomo.BlackListException(url)
        return None
    video_id = mobj.group(2)
    try:
        video_info = youtube_ie.get_video_info(video_id)
    except lib_general_download.DownloadError, mes:
        config_pytomo.LOG.error(mes)
        return None
    except Exception, mes:
        config_pytomo.LOG.exception('Uncaught exception: %s' % mes)
        return None
    video_token = urllib.unquote_plus(video_info['token'][0])
    # req_format='-1' for all available formats
    # req_format=None for best available format
    try:
        video_url_list = youtube_ie.get_video_url_list(video_id, video_token,
                                                       video_info,
                                                       req_format=None)
    except lib_general_download.DownloadError, mes:
        config_pytomo.LOG.error(mes)
        return None
    except Exception, mes:
        config_pytomo.LOG.exception('Uncaught exception: %s' % mes)
        return None
    if video_url_list:
        cache_url = video_url_list[0][1]
        config_pytomo.LOG.debug('Cache url found: %s' % cache_url)
        return cache_url

if __name__ == '__main__':
    #sys.exit(main())
    import doctest
    doctest.testmod()
