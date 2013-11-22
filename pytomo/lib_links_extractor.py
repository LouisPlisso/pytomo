#!/usr/bin/env python
''' Module to retrieve all links from a web page.
    Usage:
        import pytomo.lib_cache_url as lib_cache_url
        import pytomo.start_pytomo as start_pytomo
        log_file = 'test_cache_url'
        start_pytomo.configure_log_file(log_file)

        url = 'http://www.youtube.com/charts/videos_views'
        all_links = lib_cache_url.get_all_links(url)
'''
from __future__ import with_statement, absolute_import

import sys
import htmllib
import formatter
import urllib2
import logging
import socket
from optparse import OptionParser
from httplib import BadStatusLine
from collections import namedtuple
# global config
try:
    from . import config_pytomo
except ValueError:
    import config_pytomo

CONTENT_TYPE_HEADER = 'Content-type'
TEXT_HTML_TYPE = 'text/html'

class LinksExtractor(htmllib.HTMLParser):
    ''' Simple HTML parser to obtain the urls from webpage'''
    # derive new HTML parser
    def __init__(self, format_page):
        # class constructor
        htmllib.HTMLParser.__init__(self, format_page)
        # base class constructor
        self.links = []

    def start_a(self, attrs) :
        # override handler of <A ...>...</A> tags
        # process the attributes
        if len(attrs) > 0 :
            for attr in attrs :
                if attr[0] == "href" :
                    # ignore all non HREF attributes
                    self.links.append(attr[1])
                    # save the link info in the list

    def get_links(self) :
        ''' Return the list of extracted links'''
        return self.links


class HeadRequest(urllib2.Request):
    ''' Class to return only the header of a request'''
    def get_method(self):
        return "HEAD"

NoRedirectResponse = namedtuple('NoRedirectResponse', ['code', 'location'])

class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    'Class to not follow redirects'
    def http_error_x(self, req, fp, code, msg, headers):
        return NoRedirectResponse(code, headers['location'])

for redirect_code in config_pytomo.HTTP_REDIRECT_CODE_LIST:
    setattr(NoRedirectHandler, 'http_error_%d' % redirect_code,
            NoRedirectHandler.http_error_x)


def configure_proxy():
    ''' Set the proxy according to the default'''
    if config_pytomo.PROXIES:
        proxy = urllib2.ProxyHandler(config_pytomo.PROXIES)
        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)

def retrieve_header(url, follow_redirect=True):
    ''' Return only the response header of an url'''
    if follow_redirect:
        opener = urllib2.build_opener()
    else:
        opener = urllib2.build_opener(NoRedirectHandler)
    request = HeadRequest(url, None, config_pytomo.STD_HEADERS)
    try:
        #response = urllib2.urlopen(request, timeout=config_pytomo.URL_TIMEOUT)
        response = opener.open(request, timeout=config_pytomo.URL_TIMEOUT)
    except urllib2.URLError, mes:
        config_pytomo.LOG.warn('URLError in getting HEAD of this url: %s'
                               '\nError message: %s' % (url, mes))
        return None
    except BadStatusLine, mes:
        config_pytomo.LOG.warn('BadStatusLine in getting HEAD of this url: %s'
                               '\nError message: %s' % (url, mes))
        return None
    except Exception, mes:
        config_pytomo.LOG.exception('Unexpected exception: %s' % mes)
        return None
    return response

def retrieve_content_type_header(response):
    ''' Retrieve the LAST "Content-type" header of an HTTP response'''
    if response:
        try:
            return response.headers.getheader(CONTENT_TYPE_HEADER)
        except AttributeError, mes:
            config_pytomo.LOG.warn('Problem in getting "Content-type" header.'
                               '\nError message: %s' % mes)
            return None
    else:
        return None

def get_all_links(url):
    ''' Parse and return a list of the links from the HTMLParser'''
    # create default formatter
    format_page = formatter.NullFormatter()
    # create new parser object
    htmlparser = LinksExtractor(format_page)
    configure_proxy()
    response = retrieve_header(url)
    if response:
        content_type = retrieve_content_type_header(response)
        if content_type:
            if TEXT_HTML_TYPE in content_type:
                try:
                    data = urllib2.urlopen(urllib2.Request(url, None,
                                           config_pytomo.STD_HEADERS),
                                           timeout=config_pytomo.URL_TIMEOUT)
                # socket.error is a child of IOError only in 2.6
                except (socket.error, IOError), mes:
                    config_pytomo.LOG.warn('Problem in getting links of this'
                                            ' url: %s'
                                            '\nError message: %s' % (url, mes))
                    return []
                except Exception, mes:
                    config_pytomo.LOG.exception('Unexpected exception: %s'
                                                % mes)
                    return []
                try:
                    htmlparser.feed(data.read())
                except Exception, mes:
                    # most probably an exception trying to parse a redirect URL
                    # should catch only htmllib.HTMLParseError but try to be on
                    # the safe side...
                    config_pytomo.LOG.exception('feed exception: %s' % mes)
                    return []
                # parse the file saving the info about links
                htmlparser.close()
                return htmlparser.get_links()
    return []

def main(argv=None):
    "Program wrapper"
    if argv is None:
        argv = sys.argv[1:]
    usage = "%prog [-w out_file] [-v] url"
    parser = OptionParser(usage=usage)
    parser.add_option("-w", dest = "out_file_name", default="-",
            help = "output file or stdout if FILE is - (default case)")
    parser.add_option("-v", "--verbose", dest = "verbose",
            action="store_true", default=False,
            help = "run as verbose mode")
    (options, args) = parser.parse_args(argv)
    if len(args) != 1:
        parser.error("Incorrect number of arguments, provide an url")
    if options.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    config_pytomo.LOG = logging.getLogger('lib_cache_url')
    # to not have console output
    config_pytomo.LOG.propagate = False
    config_pytomo.LOG.setLevel(log_level)
    if options.out_file_name == '-':
        handler = logging.StreamHandler(sys.stdout)
    else:
        try:
            with open(options.out_file_name, 'w') as _:
                pass
        except IOError:
            parser.error("Problem opening file: %s" % options.out_file_name)
        handler = logging.FileHandler(filename=options.out_file_name)
    log_formatter = logging.Formatter("%(asctime)s - %(filename)s - "
                                      "%(levelname)s - %(message)s")
    handler.setFormatter(log_formatter)
    config_pytomo.LOG.addHandler(handler)
    print('From "%s" the extracted links are:\n %s' % (args[0],
                                                       get_all_links(args[0])))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    sys.exit(main())
