#!/usr/bin/env python

"""Module to download youtube video for a limited amount of time and
calculate the data downloaded within that time

    Usage:
        This module provides two classes: FileDownloader class and the
        InfoExtractor class.
        This module is not meant to be called directly.
"""

from __future__ import with_statement, absolute_import
import httplib
import math
import socket
import sys
import time
import urllib2
import tempfile
import os
from urlparse import urlsplit
#import cookielib

from . import kaa_metadata
from .kaa_metadata.core import ParseError

#from .flvlib.scripts import debug_flv
from .flvlib import tags

from . import config_pytomo
from . import lib_links_extractor

# video download is a FSM with the following states
INITIAL_BUFFERING_STATE = 0
PLAYING_STATE = 1
BUFFERING_STATE = 2
# time threshold to update maximum instantaneus throughput (if download time is
# very low, DownBytes/DownTime -> very high)
MAX_TH_MIN_UPDATE_TIME = 1e-2

class DownloadError(Exception):
    """Download Error exception.

    This exception may be thrown by FileDownloader objects if they are not
    configured to continue on errors. They will contain the appropriate
    error message.
    """
    pass

class UnavailableVideoError(Exception):
    """Unavailable Format exception.

    This exception will be thrown when a video is requested
    in a format that is not available for that video.
    """
    pass

class ContentTooShortError(Exception):
    """Content Too Short exception.

    This exception may be raised by FileDownloader objects when a file they
    download is too small for what the server announced first, indicating
    the connection was probably interrupted.
    """
    pass

def get_video_type(meta_file_name):
    "Determine the video type"
    video_type = None
    try:
        with open(meta_file_name) as meta_file:
            info = kaa_metadata.parse(meta_file)
        video_type = str(info.mime.split('/')[1])
    except ParseError, mes:
        config_pytomo.LOG.debug('Video type could not be determined: %s'
                               % mes)
    except AttributeError:
        config_pytomo.LOG.debug('mime not found')
    return video_type

class FileDownloader(object):
    """File Downloader class.

    File downloader objects are the ones responsible of downloading the
    actual video file and writing it to disk if the user has requested
    it, among some other tasks. In most cases there should be one per
    program. As, given a video URL, the downloader doesn't know how to
    extract all the needed information, task that InfoExtractors do, it
    has to pass the URL to one of them.

    For this, file downloader objects have a method that allows
    InfoExtractors to be registered in a given order. When it is passed
    a URL, the file downloader handles it to the first InfoExtractor it
    finds that reports being able to handle it. The InfoExtractor extracts
    all the information about the video or videos the URL refers to, and
    asks the FileDownloader to process the video information, possibly
    downloading the video.

    File downloaders accept a lot of parameters. In order not to saturate
    the object constructor with arguments, it receives a dictionary of
    options instead. These options are available through the params
    attribute for the InfoExtractors to use. The FileDownloader also
    registers itself as the downloader in charge for the InfoExtractors
    that are added to it, so this is a "mutual registration".

    Available options:

    quiet:            Do not print messages to stdout.
    forceurl:         Force printing final URL.
    forcetitle:       Force printing title.
    forcethumbnail:   Force printing thumbnail URL.
    forcedescription: Force printing description.
    simulate:         Do not download the video files.
    format:           Video format code.
    format_limit:     Highest quality format to try.
    outtmpl:          Template for output names.
    ignoreerrors:     Do not stop on download errors.
    ratelimit:        Download speed limit, in bytes/sec.
    nooverwrites:     Prevent overwriting files.
    retries:          Number of times to retry for HTTP error 5xx
    continuedl:       Try to continue downloads if possible.
    noprogress:       Do not print the progress bar.
    playliststart:    Playlist item to start at.
    playlistend:      Playlist item to end at.
    logtostderr:      Log messages to stderr instead of stdout.
    """
    params = None
    _ies = []
    #_pps = []
    _download_retcode = None
    _total_bytes = None
    _total_time = None
    _format_downloaded = None

    def __init__(self, download_time):
        """Create a FileDownloader object with the given options.
           Configuring log_file for doc_test
           >>> import pytomo.start_pytomo as start_pytomo
           >>> start_pytomo.configure_log_file('doc_test') #doctest: +ELLIPSIS
           Configuring log file
           Logs are there: ...
           ...
           >>> filedownloader = FileDownloader(30)
        """
        self._ies = []
        #self._pps = []
        self._download_retcode = 0
        self._num_downloads = 0
        if (config_pytomo.LOG_FILE == '-') or (not config_pytomo.LOG_FILE):
            self._screen_file = sys.stdout
        elif config_pytomo.LOG_FILE_TIMESTAMP:
            # I don't like it this way...
            self._screen_file = open(config_pytomo.LOG_FILE_TIMESTAMP, 'a')
        else:
            # not very good
            self._screen_file = sys.stdout
        self.state = BUFFERING_STATE
        self.accumulated_playback = 0.0
        self.accumulated_buffer = 0.0
        self.current_buffer = 0.0
        self.interruptions = 0
        self.current_time = None
        self.start_playback = None
        self.encoding_rate = None
        self.data_len = None
        self.data_duration = None
        self.max_instant_thp = None
        self.video_type = None
        self.redirect_url = None
        self.initial_data = None
        self.initial_rate = None
        self.initial_playback_buffer = None
        self.flv_timestamp = None
        self.previous_timestamp = None
        self.time_to_get_first_byte = None
        try:
            self.download_time = int(download_time)
        except ValueError:
            config_pytomo.LOG.exception(
                "Please provide a number as max download time. Got : %s"
                % download_time)
            self.download_time = config_pytomo.DOWNLOAD_TIME
            config_pytomo.LOG.info('Set max download_time as: %d'
                                   % self.download_time)
        if self.download_time <= 0:
            self.download_time = config_pytomo.MAX_DOWNLOAD_TIME
        #self.quiet = quiet
        #self.params = params'

    def set_total_time(self, total_time):
        """Set total time taken to actually download the video."""
        self._total_time = total_time

    def get_total_time(self):
        ' Returns the time taken to domnload the file'
        return self._total_time

    def set_total_bytes(self, total_bytes):
        """Set total bytes."""
        self._total_bytes = total_bytes

    def get_total_bytes(self):
        'The total bytes downloaded in total_time'
        return self._total_bytes

    def set_format(self, vid_format):
        """Set format."""
        self._format_downloaded = vid_format

    def get_format(self):
        'Returns the format of file downloaded'
        return self._format_downloaded

    @staticmethod
    def format_bytes(byte_counter):
        """Formatting the bytes
        #First checking to see if we catch the ValueError for FileDownloader
        >>> dwn_time = 30
        >>> filedownloader = FileDownloader(dwn_time)
        >>> FileDownloader.format_bytes(24240)
        '23.67k'
        >>> FileDownloader.format_bytes(4194304)
        '4.00M'
        >>> FileDownloader.format_bytes(None)
        'N/A'
        >>> FileDownloader.format_bytes('24240')
        '23.67k'
        >>> FileDownloader.format_bytes(0.0)
        '0.00b'
        """
        if byte_counter is None:
            return 'N/A'
        if type(byte_counter) is str:
            byte_counter = float(byte_counter)
        if byte_counter == 0.0:
            exponent = 0
        else:
            exponent = long(math.log(byte_counter, 1024.0))
        suffix = 'bkMGTPEZY'[exponent]
        converted = float(byte_counter) / float(1024**exponent)
        return '%.2f%s' % (converted, suffix)

    @staticmethod
    def calc_percent(byte_counter, data_len):
        """ Computes remaining percent of download
         >>> dwn_time = 30
         >>> filedownloader = FileDownloader(dwn_time)
         >>> filedownloader.calc_percent(1024, 2048)
         ' 50.0%'
         >>> filedownloader.calc_percent(0, None)
         '---.-%'
        """
        if data_len is None or not data_len:
            # case where length is not present in metadata or zero
            return '---.-%'
        return '%6s' % ('%3.1f%%'
                        % (float(byte_counter) / float(data_len) * 100.0))

    @staticmethod
    def calc_eta(start, now, total, current):
        """
           Computes the remaining time
          >>> start =  1302688075.6457109
           >>> now = 1302688088.907017
           >>> total = 100
           >>> current = 20
           >>> dwn_time = 30
           >>> filedownloader = FileDownloader(dwn_time)
           >>> FileDownloader.calc_eta(start, now, total, current)
           '00:53'
           >>> # case where total = None
           >>> FileDownloader.calc_eta(start, now, None, current)
           '--:--'
           >>> # Case where eta > 99 mins
           >>> now = 1302692284.52929
           >>> FileDownloader.calc_eta(start, now, total, current)
           '--:--'
        """

        if total is None:
            return '--:--'
        dif = now - start
        if current == 0 or dif < 0.001: # One millisecond
            return '--:--'
        rate = float(current) / dif
        eta = long((float(total) - float(current)) / rate)
        (eta_mins, eta_secs) = divmod(eta, 60)
        if eta_mins > 99:
            return '--:--'
        return '%02d:%02d' % (eta_mins, eta_secs)

    @staticmethod
    def calc_speed(start, now, byte_counter):
        """
        Computes download speed
       >>> start =  1302692811.61169
       >>> now = 1302692821.595638
       >>> byte_counter = 248000
       >>> dwn_time = 30
       >>> filedownloader = FileDownloader(dwn_time)
       >>> filedownloader.calc_speed(start, now, byte_counter)
       ' 24.26kb/s'
       >>> filedownloader.calc_speed(start, now, 00)
       '    ---b/s'
       """
        diff = now - start
        if byte_counter == 0 or diff < 0.001: # One millisecond
            return '%10s' % '---b/s'
        return '%10s' % ('%sb/s'
                         % FileDownloader.format_bytes(float(byte_counter)
                                                       / diff))

    @staticmethod
    def best_block_size(elapsed_time, data_block_len):
        '''Function to determine the best block size tht is to be used for the
        remaining data
       >>> dwn_time = 30
       >>> filedownloader = FileDownloader(dwn_time)
       >>> filedownloader.best_block_size(0.0001, 81943040)
       4194304L
       >>> filedownloader.best_block_size(20, 2097152)
       1048576L
       >>> filedownloader.best_block_size(2, 81943040)
       4194304L
       >>> filedownloader.best_block_size(20, 2097152)
       1048576L
       '''
        new_min = max(data_block_len / 2.0, 1.0)
        # Do not surpass 4 MB
        new_max = min(max(data_block_len * 2.0, 1.0), 4194304)
        if elapsed_time < 0.001:
            return long(new_max)
        rate = data_block_len / elapsed_time
        if rate > new_max:
            return long(new_max)
        if rate < new_min:
            return long(new_min)
        return long(rate)

    def add_info_extractor(self, add_ie):
        """Add an InfoExtractor object to the end of the list."""
        self._ies.append(add_ie)
        add_ie.set_downloader(self)

    def to_screen(self, message, skip_eol=False):
        """Print message to stdout if not in quiet mode."""
        terminator = [u'\n', u''][skip_eol]
        output = message + terminator
        self._screen_file.write(output)
        self._screen_file.flush()
        # original version in yt/dm_download
        #terminator = [u'\n', u''][skip_eol]
        #print >> self._screen_file, (u'%s%s' % (message, terminator)),
        #self._screen_file.flush()

    @staticmethod
    def to_stderr(message):
        """Print message to stderr."""
        print >> sys.stderr, message

    @staticmethod
    def trouble(message=None):
        """Determine action to take when a download problem appears.

        Depending on if the downloader has been configured to ignore
        download errors or not, this method may throw an exception or
        not when errors are found, after printing the message.
        """
        if message is not None:
            #self.to_stderr(message)
            config_pytomo.LOG.debug('trouble message: %s' % message)
        #if not self.params.get('ignoreerrors', False):
        raise DownloadError(message)
        #self._download_retcode = 1

    def report_progress(self, progress_stats):
        """Report download progress."""
        self.to_screen('\r[download] %(percent_str)s of %(data_len_str)s at \
%(speed_str)s ETA %(eta_str)s Bytes %(byte_counter)d Inst_thp \
%(instant_thp)skb/s  cur_buf %(current_buffer)f' % progress_stats,
                       skip_eol=True)

    def report_retry(self, count, retries):
        """Report retry in case of HTTP error 5xx"""
        self.to_screen(u'[download] Got server HTTP error. \
Retrying (attempt %d of %d)...' % (count, retries))

    def report_finish(self):
        """Report download finished."""
        #if self.params.get('noprogress', False):
        self.to_screen(u'\n[download] Download completed')
        #else:
            #self.to_screen(u'')

    def process_info(self, info_dict):
        """Process a single dictionary returned by an InfoExtractor."""
#        # Do nothing else if in simulate mode
#        if self.params.get('simulate', False):
#            # Forced printings
#            if self.params.get('forcetitle', False):
#                print info_dict['title']
#            if self.params.get('forceurl', False):
#                print info_dict['url']
#            if (self.params.get('forcethumbnail', False)
#                and 'thumbnail' in info_dict):
#                print info_dict['thumbnail']
#            if (self.params.get('forcedescription', False)
#                and 'description' in info_dict):
#                print info_dict['description']
#            return
        try:
            template_dict = dict(info_dict)
            template_dict['epoch'] = unicode(long(time.time()))
            template_dict['autonumber'] = unicode('%05d' % self._num_downloads)
        except (ValueError, KeyError), err:
            self.trouble(u'ERROR: invalid system charset or erroneous output \
template')
            return
        try:
            _, total_download_time = self._do_download(
                                        info_dict['url'].encode('utf-8'),
                                      )
        except (OSError, IOError), err:
            raise UnavailableVideoError
        except (httplib.HTTPException, socket.error), err:
            self.trouble(u'ERROR: unable to download video data: %s' % str(err))
            return
        #except (ContentTooShortError, ), err:
        #    self.trouble(
        #        u'ERROR: content too short (expected %s bytes and served %s)'
        #        % (err.expected, err.downloaded))
        #    return
        self.set_total_time(total_download_time)
        return total_download_time

    def download(self, url_list):
        """Download a given list of URLs."""
        for url in url_list:
            suitable_found = False
            for ie_var in self._ies:
                # Go to next InfoExtractor if not suitable
                if not ie_var.suitable(url):
                    continue
                # Suitable InfoExtractor found
                suitable_found = True
                # Extract information from URL and process it
                ie_var.extract(url)
                # Suitable InfoExtractor had been found; go to next URL
                break
            if not suitable_found:
                self.trouble(u'ERROR: no suitable InfoExtractor: %s' % url)
        return self._download_retcode

    @staticmethod
    def establish_connection(url, ip_address=None):
        """Set up the connection
        Return the data stream
        The url is the cache_url of the video.
        """
        data = None
        status_code = None
        lib_links_extractor.configure_proxy()
        parsed_uri = urlsplit(url)
        # <scheme>://<netloc>/<path>?<query>#<fragment>
        urn = '?'.join((parsed_uri.path, parsed_uri.query))
        if ip_address:
            uri = '://'.join((parsed_uri.scheme, ip_address)) + urn
            headers = dict([('Host', parsed_uri.netloc)]
                           + config_pytomo.STD_HEADERS.items())
        else:
            uri = url
            headers = config_pytomo.STD_HEADERS
        #cookie_jar = cookielib.MozillaCookieJar()
        #cookie_jar.load(config_pytomo.cookie_file)
        basic_request = urllib2.Request(uri, None, headers)
        #cookie_jar.add_cookie_header(basic_request)
        request = urllib2.Request(uri, None, headers)
        #cookie_jar.add_cookie_header(request)
        #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
        count = 0
        retries = 3
        while count <= retries:
            # Establish connection
            try:
                data = urllib2.urlopen(request,
                                       timeout=config_pytomo.URL_TIMEOUT)
                #data = opener.open(request)
                break
            except (urllib2.HTTPError, ), err:
                if (err.code < 500 or err.code >= 600) and err.code != 416:
                    # Unexpected HTTP error
                    raise
                elif err.code == 416:
                    # Unable to resume (requested range not satisfiable)
                    config_pytomo.LOG.exception(err)
                    try:
                        # Open the connection again without the range header
                        data = urllib2.urlopen(basic_request,
                                               timeout=config_pytomo.URL_TIMEOUT)
                        #data = opener.open(basic_request)
                    except (urllib2.HTTPError, ), err:
                        if err.code < 500 or err.code >= 600:
                            status_code = err.code
                            return status_code, None
                            #raise
                    else:
                        # Examine the reported length
                        #open_mode = 'wb'
                        pass
            except Exception, err:
                config_pytomo.LOG.exception(err)
                config_pytomo.LOG.debug('exception trying again to download: %s'
                                        % url)
                pass
            # Retry
            count += 1
        if count > retries:
            config_pytomo.LOG.error(u'ERROR: giving up after %d retries'
                                    % retries)
        if data:
            status_code = data.getcode()
        return status_code, data

    def compute_interruptions(self, data_block_len, current_time):
        "Compute the number of interruptions in the playback"
        if not self.encoding_rate:
            # start of download: do not keep track of the bytes
            # downloaded before getting the encoding rate because video data do
            # not appear before encoding rate!
            # NO: self.start_buffered_bytes += data_block_len
            return False
        # block size is in Bytes and encoding in bits per seconds
        self.current_buffer += 8 * data_block_len / self.encoding_rate
        if self.state == PLAYING_STATE:
            self.current_buffer -= (current_time - self.previous_timestamp)
            self.previous_timestamp = current_time
            if self.current_buffer < config_pytomo.MIN_PLAYOUT_BUFFER:
                self.interruptions += 1
                self.state = BUFFERING_STATE
                config_pytomo.LOG.debug(
                    "Entering buffering state: %d itr and buffered %f"
                    % (self.interruptions, self.current_buffer))
        elif self.current_buffer > config_pytomo.INITIAL_BUFFER:
            config_pytomo.LOG.debug(
                "Entering playing state with %f sec buffered"
                % self.current_buffer)
            self.state = PLAYING_STATE
            self.previous_timestamp = current_time
            # do not update current time if not in playing state (or just
            # switched)
        else:
            # buffering
            pass
        return True

    def compute_encoding_rate(self, meta_file_name):
        """Compute the encoding rate
        if found in the temp file, close the file and set the value in the
        object
        """
        try:
            data_duration = get_data_duration(meta_file_name)
        except ParseError, mes:
            config_pytomo.LOG.debug('data duration not yet found: %s'
                                   % mes)
            data_duration = None
        if data_duration:
            self.data_duration = data_duration
            # AO 20121030 encoding rate should be in kbps
            # (as in metadata of flv)
            # data len in Bytes
            self.encoding_rate = 8 * self.data_len / data_duration / 1000
            config_pytomo.LOG.debug("Encoding rate is: %.2fkb/s"
                                    % self.encoding_rate)

    def _do_download(self, url, ip_address=None):
        '''Module that handles the download of the file and
        calculates the time, bytes downloaded. Here the url is the cache URL
        of the video
        '''
        config_pytomo.LOG.debug('Downloading url: %s, on this ip: %s'
                                % (url, ip_address))
        #status_code = None
        connection_time = time.time()
        status_code, data = self.establish_connection(url, ip_address)
        if not data:
            config_pytomo.LOG.error('could not establish connection to url: %s'
                                    % url)
            return status_code, None
        # If there was a redirection for the cache url,
        # get the DNS resolution again.
        if status_code in config_pytomo.HTTP_REDIRECT_CODE_LIST:
            config_pytomo.LOG.info("URL redirected.")
            self.redirect_url = data.geturl()
            return status_code, None
        duration = None
        with tempfile.NamedTemporaryFile() as meta_file:
            # just to get a temporary file name in the current dir
            # cannot use the file stream directly because it is not permitted
            # to open a temporary file already open
            # and the delete parameter available in 2.7 only
            meta_file_name = meta_file.name
        try:
            duration = self.process_download_flv(data, meta_file_name,
                                                 connection_time)
            self.video_type = 'FLV'
        except tags.MalformedFLV:
            config_pytomo.LOG.info('Not FLV')
        if not self.video_type:
            self.video_type = get_video_type(meta_file_name)
            try:
                duration = self.process_download_other(data, meta_file_name,
                                                       connection_time)
            except OSError, mes:
                config_pytomo.LOG.exception(mes)
        #self.set_total_bytes(byte_counter)
        config_pytomo.LOG.info("nb of interruptions: %d" % self.interruptions)
        # Delete the file once download analysis is completed
        # AO 15112012 should try/catch because statistics are retrieved even if
        # temporary file cannot be deleted (moved from download functions)
        # check problems if file is already closed
        meta_file.close()
        try:
            os.remove(meta_file_name)
        except OSError, mes:
            config_pytomo.LOG.exception('Could not remove temporary file %s\n%s'
                                        % (meta_file_name, mes))
        return status_code, duration

    def update_without_tags(self):
        '''Estimate current video timestamp out of encoding rate and elapsed
        time'''
        if not self.encoding_rate:
            return None
        # we use flv_timestamp even if it's not an flv file
        self.flv_timestamp = self._total_bytes / self.encoding_rate * 8e-3

    def update_with_tags(self, flv_tags):
        """Fills object informations with read tags
        """
        while True:
            try:
                tag = read_next_tag_or_seek(flv_tags)
                if tag and (isinstance(tag, tags.ScriptTag)
                            and tag.name == "onMetaData"):
                    # AO 20121029 metadata encoding rate should be in kbps
                    try:
                        self.encoding_rate = tag.variable['totaldatarate']
                    except KeyError:
                        self.encoding_rate = (tag.variable['audiodatarate'] +
                                              tag.variable['videodatarate'])
                    config_pytomo.LOG.debug('Encoding rate %s'
                                            % self.encoding_rate)
                if tag and (isinstance(tag, tags.AudioTag) or
                            isinstance(tag, tags.VideoTag)):
                    if tag.timestamp < self.flv_timestamp:
                        config_pytomo.LOG.debug('decreasing timestamp found')
                    self.flv_timestamp = float(max(self.flv_timestamp,
                                                   tag.timestamp)) / 1000
            except tags.EndOfFile:
                break
            except tags.EndOfTags:
                break

    def update_state(self, elapsed_time):
        """Compute the state of the video playback (emulated) with the time
        elapsed and the flv informations collected.
        """
        if self.state == INITIAL_BUFFERING_STATE:
#            config_pytomo.LOG.debug('State: INITIAL_BUFFERING_STATE')
#            config_pytomo.LOG.debug('current_time=%s; Total_bytes=%s' %
#                                    (self.current_time, self._total_bytes))
            if (self.flv_timestamp > config_pytomo.INITIAL_BUFFER):
                self.state = PLAYING_STATE
                if config_pytomo.DEMO:
                    config_pytomo.LOG.info('\n\nStart\n')
                self.start_playback = elapsed_time
                self.initial_data = self._total_bytes
                try:
                    self.initial_rate = (self.initial_data * 8
                                         / self.current_time / 1000)
                except ZeroDivisionError:
                    self.initial_rate = 0
        elif self.state == PLAYING_STATE:
#            config_pytomo.LOG.debug('State: PLAYING_STATE')
#            config_pytomo.LOG.debug('current_time=%s; Total_bytes=%s' %
#                                    (self.current_time, self._total_bytes))
            self.accumulated_playback = self.flv_timestamp
            video_playback_time = (self.current_time - self.start_playback -
                                   self.accumulated_buffer)
            #print ("PLaying state", self.flv_timestamp, video_playback_time,
            #self.accumulated_buffer)
            if ((self.flv_timestamp - video_playback_time)
                < config_pytomo.MIN_PLAYOUT_BUFFER):
                self.state = BUFFERING_STATE
                self.interruptions += 1
                if config_pytomo.DEMO:
                    config_pytomo.LOG.info('\n\nInterruption\n')
                    #import pdb; pdb.
        elif self.state == BUFFERING_STATE:
#            config_pytomo.LOG.debug('State: BUFFERING_STATE')
#            config_pytomo.LOG.debug('current_time=%s; Total_bytes=%s' %
#                                    (self.current_time, self._total_bytes))
            self.accumulated_buffer += elapsed_time
            video_playback_time = (self.current_time - self.start_playback -
                                   self.accumulated_buffer)
            #print "BUFFERING_STATE ", self.flv_timestamp, video_playback_time
            if (self.flv_timestamp - video_playback_time
                > config_pytomo.MIN_PLAYOUT_RESTART):
                self.state = PLAYING_STATE
                if config_pytomo.DEMO:
                    config_pytomo.LOG.info('\n\nRestart\n')
#            self.compute_interruptions(data_block_len, after)
#            if self.state == PLAYING_STATE:
#                self.accumulated_playback += (after - before)
#                if not buff_state_tracker:
#                    #initial_duration = self.accumulated_buffer
#                    try:
#                        self.initial_rate = (self.initial_data * 8
#                                             / self.accumulated_buffer / 1000)
#                    except ZeroDivisionError:
#                        self.initial_rate = 0
#                    buff_state_tracker = True
#            elif self.state == BUFFERING_STATE:
#                self.accumulated_buffer += (after - before)
#                if not buff_state_tracker:
#                    self.initial_data += data_block_len
#            else:
#                config_pytomo.LOG.error("Unexpected state case")

    def process_download_other_old(self, data, meta_file_name):
        """Take care of downloading part. """
        block_size = 1024
        # content-length in bytes
        self.data_len = float(data.info().get('Content-length', None))
        config_pytomo.LOG.debug('Content-length: %s' % self.data_len)
        #meta_file = open(meta_file_name, 'ab')
        #meta_file = open(meta_file_name, 'ab+')
        tries = 0
        accumulated_playback = 0
        buff_state_tracker = False
        accumulated_buffer = 0.0
        initial_data = 0
        initial_rate = 0
        byte_counter = 0
        self.state = INITIAL_BUFFERING_STATE
        start = time.time()
        while True:
            # Download and write
            before = time.time()
            if not ((before - start) > self.download_time):
                # read in bytes
                data_block = data.read(block_size)
            else:
                break
            if (not self.encoding_rate
                and tries <= config_pytomo.MAX_NB_TRIES_ENCODING):
                self.compute_encoding_rate(meta_file_name)
                tries += 1
            data_block_len = len(data_block)
            if data_block_len == 0:
                break
            after = time.time()
            self.compute_interruptions(data_block_len, after)
            if self.state == PLAYING_STATE:
                accumulated_playback += (after - before)
                if not buff_state_tracker:
                    initial_duration = accumulated_buffer
                    try:
                        initial_rate = (initial_data * 8 / initial_duration /
                                        1000)
                    except ZeroDivisionError:
                        initial_rate = 0
                    buff_state_tracker = True
            elif self.state == BUFFERING_STATE:
                accumulated_buffer += (after - before)
                if not buff_state_tracker:
                    initial_data += data_block_len
            else:
                config_pytomo.LOG.error("Unexpected state case")
                break
            byte_counter += data_block_len
            block_size = self.best_block_size(after - before, data_block_len)
            instant_thp = (8e-3 * data_block_len / (after - before)
                           if (after - before) != 0 else None)
            self.max_instant_thp = max(self.max_instant_thp, instant_thp)
            if config_pytomo.LOG_LEVEL == config_pytomo.DEBUG:
                # Progress message
                progress_stats = {
                    'percent_str': self.calc_percent(self._total_bytes,
                                                     self.data_len),
                    'data_len_str': self.format_bytes(self.data_len),
                    'eta_str': self.calc_eta(start, time.time(), self.data_len,
                                             self._total_bytes),
                    'speed_str': self.calc_speed(start, time.time(),
                                                 self._total_bytes),
                    # in order to avoid None convertion to float in
                    # report_progress and still have information
                    'instant_thp': str(instant_thp),
                    'byte_counter': self._total_bytes,
                    'current_buffer': self.current_buffer,
                }
                self.report_progress(progress_stats)
        self.set_total_bytes(byte_counter)
        self.accumulated_playback = accumulated_playback
        self.accumulated_buffer = accumulated_buffer
        self.initial_data = initial_data
        self.initial_rate = initial_rate
        return after - start

    def process_download_other(self, data, meta_file_name, connection_time):
        """Take care of downloading part  for non flv files"""
        block_size = 1024
        # content-length in bytes
        self.data_len = float(data.info().get('Content-length', None))
        config_pytomo.LOG.debug('Content-length: %s' % self.data_len)
        #meta_file = open(meta_file_name, 'ab')
        #meta_file = open(meta_file_name, 'ab+')
        tries = 0
        self._total_bytes = 0
        self.state = INITIAL_BUFFERING_STATE
        start = time.time()
        while True:
            # Download and write
            before = time.time()
            if (before - start) > self.download_time:
                config_pytomo.LOG.debug('\nDownloaded %i seconds from video'
                                        'stopping' % (before - start))
                break
            # read in bytes
            data_block = data.read(block_size)
            if not self.time_to_get_first_byte:
                first_byte_time = time.time()
                self.time_to_get_first_byte = first_byte_time - connection_time
            if (not self.encoding_rate
                and tries <= config_pytomo.MAX_NB_TRIES_ENCODING):
                self.compute_encoding_rate(meta_file_name)
                tries += 1
            data_block_len = len(data_block)
            #config_pytomo.LOG.debug('\ndata_block_len=%s' % data_block_len)
            if data_block_len == 0:
                config_pytomo.LOG.debug('\nDowloaded complete video')
                break
            self._total_bytes += data_block_len
            self.update_without_tags()
            after = time.time()
            #config_pytomo.LOG.debug('\nbefore=%s; after=%s' % (before, after))
            if not self.data_duration:
                try:
                    self.data_duration = get_data_duration(meta_file_name)
                except ParseError, mes:
                    config_pytomo.LOG.info('no data duration: %s' % mes)
            self.current_time = after - start
            time_difference = after - before
            self.update_state(time_difference)
            block_size = self.best_block_size(time_difference, data_block_len)
            instant_thp = (8e-3 * data_block_len / (time_difference)
                           if (time_difference) != 0 else None)
            #config_pytomo.LOG.debug('max_instant_thp=%skb/s; instant_thp=%skb/s'
            #                        % (self.max_instant_thp, instant_thp))
            if time_difference > MAX_TH_MIN_UPDATE_TIME:
                self.max_instant_thp = max(self.max_instant_thp, instant_thp)
            if config_pytomo.LOG_LEVEL == config_pytomo.DEBUG:
                # Progress message
                progress_stats = {
                    'percent_str': self.calc_percent(self._total_bytes,
                                                     self.data_len),
                    'data_len_str': self.format_bytes(self.data_len),
                    'eta_str': self.calc_eta(start, time.time(), self.data_len,
                                             self._total_bytes),
                    'speed_str': self.calc_speed(start, time.time(),
                                                 self._total_bytes),
                    # in order to avoid None convertion to float in
                    # report_progress and still have information
                    'instant_thp': str(instant_thp),
                    'byte_counter': self._total_bytes,
                    'current_buffer': self.current_buffer,
                }
                self.report_progress(progress_stats)
        return after - start

    def process_download_flv(self, data, meta_file_name, connection_time):
        """Take care of downloading part
        """
        # content-length in bytes
        self.data_len = float(data.info().get('Content-length', None))
        config_pytomo.LOG.debug('Content-length: %s' % self.data_len)
        #meta_file = open(meta_file_name, 'ab')
        meta_file = open(meta_file_name, 'ab+')
        flv_tags = tags.FLV(meta_file)
        self._total_bytes = 0
        #nb_zero_data = 0
        self.state = INITIAL_BUFFERING_STATE
        #block_size = 1024
        block_size = 1
        start = time.time()
        config_pytomo.LOG.debug('start time: %s' % start)
        while True:
            # Download and write
            before = time.time()
            #config_pytomo.LOG.debug('before time: %s\n' % before)
            if (before - start) > self.download_time:
                config_pytomo.LOG.debug('Downloaded video during %i seconds, '
                                        'stopping' % (before - start))
                break
            # read in bytes
            data_block = data.read(block_size)
            if not self.time_to_get_first_byte:
                first_byte_time = time.time()
                self.time_to_get_first_byte = first_byte_time - connection_time
                block_size = 1024
            data_block_len = len(data_block)
            if data_block_len == 0:
                #nb_zero_data += 1
                #config_pytomo.LOG.debug('\nZero data block')
                #if nb_zero_data > 1:
                config_pytomo.LOG.debug('\nFinished downloading video')
                break
            write_no_seek(meta_file, data_block)
            self._total_bytes += data_block_len
            self.update_with_tags(flv_tags)
            after = time.time()
            if not self.data_duration:
                try:
                    self.data_duration = get_data_duration(meta_file_name)
                except ParseError, mes:
                    config_pytomo.LOG.info('data duration not yet found: %s'
                                           % mes)
            self.current_time = after - start
            time_difference = after - before
            self.update_state(time_difference)
            block_size = self.best_block_size(time_difference, data_block_len)
            instant_thp = (8e-3 * data_block_len / (time_difference)
                           if (time_difference) != 0 else None)
            if time_difference > MAX_TH_MIN_UPDATE_TIME:
                self.max_instant_thp = max(self.max_instant_thp, instant_thp)
            # no more progress stats to check impact on download time
#            if config_pytomo.LOG_LEVEL == config_pytomo.DEBUG:
#                # Progress message
#                progress_stats = {
#                    'percent_str': self.calc_percent(self._total_bytes,
#                                                     self.data_len),
#                    'data_len_str': self.format_bytes(self.data_len),
#                    'eta_str': self.calc_eta(start, time.time(), self.data_len,
#                                             self._total_bytes),
#                    'speed_str': self.calc_speed(start, time.time(),
#                                                 self._total_bytes),
#                    # in order to avoid None convertion to float in
#                    # report_progress and still have information
#                    'instant_thp': str(instant_thp),
#                    'byte_counter': self._total_bytes,
#                    'current_buffer': self.current_buffer,
#                    # For videos with mp4 encoding
#                }
#                self.report_progress(progress_stats)
        meta_file.close()
        return after - start

#def get_initial_playback_flv(flv_tags,
#             initial_buff_duration=config_pytomo.INITIAL_PLAYBACK_DURATION):
#    """Return the amount of bytes corresponding to the duration given by
#    initial_buff_duration by reading the flv tags of the file given by its name
#    """
#    _, initial_playback_buffer = debug_flv.debug_file(meta_file_name,
#                                        video_time=initial_buff_duration)
#    #print "initial buff", initial_playback_buffer
#    return initial_playback_buffer

class InfoExtractor(object):
    """Information Extractor class.

    Information extractors are the classes that, given a URL, extract
    information from the video (or videos) the URL refers to. This
    information includes the real video URL, the video title and simplified
    title, author and others. The information is stored in a dictionary
    which is then passed to the FileDownloader. The FileDownloader
    processes this information possibly downloading the video to the file
    system, among other possible outcomes. The dictionaries must include
    the following fields:

    id:     Video identifier.
    url:        Final video URL.
    uploader:   Nickname of the video uploader.
    title:      Literal title.
    stitle:     Simplified title.
    ext:        Video filename extension.
    format:     Video format.
    player_url: SWF Player URL (may be None).

    The following fields are optional. Their primary purpose is to allow
    youtube-dl to serve as the backend for a video search function, such
    as the one in youtube2mp3.  They are only used when their respective
    forced printing functions are called:

    thumbnail:  Full URL to a video thumbnail image.
    description:    One-line video description.

    Subclasses of this one should re-define the _real_initialize() and
    _real_extract() methods, as well as the suitable() static method.
    Probably, they should also be instantiated and added to the main
    downloader.
    """

    _ready = False
    _downloader = None

    def __init__(self, downloader=None):
        """Constructor. Receives an optional downloader."""
        self._ready = False
        self.set_downloader(downloader)


    def initialize(self):
        """Initializes an instance (authentication, etc)."""
        if not self._ready:
            self._real_initialize()
            self._ready = True

    def extract(self, url):
        """Extracts URL information and returns it in list of dicts."""
        self.initialize()
        return self._real_extract(url)

    def set_downloader(self, downloader):
        """Sets the downloader for this IE."""
        self._downloader = downloader

    def _real_initialize(self):
        """Real initialization process. Redefine in subclasses."""
        pass

    def _real_extract(self, url):
        """Real extraction process. Redefine in subclasses."""
        pass

def write_no_seek(meta_file, data_block):
    """Write the data block at the end of file but do not change position"""
    position = meta_file.tell()
    # seek 0 bytes from the end of file (2)
    meta_file.seek(0, 2)
    meta_file.write(data_block)
    meta_file.seek(position)

def read_next_tag_or_seek(flv_tags):
    """Read the next flv tag and return it
    in case of incomplete tag (not enough data) seek the file
    """
    # is this the good place to put?
    if not flv_tags.version:
        flv_tags.parse_header()
    tag = None
    position = flv_tags.f.tell()
    try:
        tag = flv_tags.get_next_tag()
    except tags.EndOfFile:
        flv_tags.f.seek(position)
        raise tags.EndOfFile
    return tag

def get_data_duration(meta_file_name):
    """Return the length (duration) of data or None
    when found, close the file
    """
    try:
        with open(meta_file_name) as meta_file:
            info = kaa_metadata.parse(meta_file)
    except IOError:
        config_pytomo.LOG.error('Unable to open tempfile for kaa_metadata')

    if (info and 'length' in info):
        data_duration = info.length
        return data_duration

def get_download_stats(cache_uri, ip_address,
                       download_time=config_pytomo.DOWNLOAD_TIME):
                       #redirect=False):
    """Return a tuple of stats for download from an url based on ip address
    Simpler version because cache url is already there: uses only _do_download
    """
    file_downloader = FileDownloader(download_time)
    try:
        status_code, download_time = (
            file_downloader._do_download(cache_uri, ip_address))
    except DownloadError, mes:
        config_pytomo.LOG.error(mes)
        return None
    if download_time:
        return (status_code, [download_time,
                file_downloader.video_type,
                file_downloader.data_duration,
                file_downloader.data_len,
                file_downloader.encoding_rate,
                file_downloader.get_total_bytes(),
                file_downloader.interruptions,
                file_downloader.initial_data,
                file_downloader.initial_rate,
                file_downloader.initial_playback_buffer,
                file_downloader.accumulated_buffer,
                file_downloader.accumulated_playback,
                file_downloader.current_buffer,
                file_downloader.time_to_get_first_byte,
                file_downloader.max_instant_thp,
                ], None)
    if status_code in config_pytomo.HTTP_REDIRECT_CODE_LIST:
        return status_code, None, file_downloader.redirect_url
    else:
        return status_code, None, None
    return None

if __name__ == '__main__':
    import doctest
    doctest.testmod()

