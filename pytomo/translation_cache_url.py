#!/usr/bin/env python
'''Translate new cache url format into human readable airport codes

based on Maurizio M. Munafo perl code:
    $name =~ tr/0-9a-z/uzpkfa50vqlgb61wrmhc72xsnid83ytoje94/;
'''

import re
from string import maketrans, lowercase
import sys
import os
import logging
from optparse import OptionParser, SUPPRESS_HELP

# for interactive call: do not add multiple times the handler
if 'LOG' not in locals():
    LOG = None
LOG_LEVEL = logging.ERROR
FORMATER_STRING = ('%(asctime)s - %(filename)s:%(lineno)d - '
                   '%(levelname)s - %(message)s')

def configure_log(level=LOG_LEVEL, log_file=None):
    'Configure logger'
    if LOG:
        LOG.setLevel(level)
        return LOG
    log = logging.getLogger('%s log' % os.path.basename(__file__))
    if log_file:
        handler = logging.FileHandler(filename=log_file)
    else:
        handler = logging.StreamHandler(sys.stderr)
    log_formatter = logging.Formatter(FORMATER_STRING)
    handler.setFormatter(log_formatter)
    log.addHandler(handler)
    log.setLevel(level)
    return log


try:
    from . import config_pytomo
except ValueError:
    class module_mock(object):
        '''Mock for running as stand alone tool'''
        def __init__(self):
            self.LOG = configure_log()
    config_pytomo = module_mock()

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
                  r'(\w{6,7}-\w{4}|(?:-|\w){8})(---v\d{1,2}---lscache\d){0,1}'
                             r'(\.c\.youtube|\.googlevideo)(\.com)')
TRANSLATION = maketrans(''.join(map(str, range(10))) + lowercase,
                               'uzpkfa50vqlgb61wrmhc72xsnid83ytoje94')

def translate_cache_url(url):
    ''' Return decrypted cache url name, using monoalphabetic cipher:
        digits, letters -> uzpkfa50vqlgb61wrmhc72xsnid83ytoje94
    Assumes all cache servers that match pattern are encrypted, otherwise
    it returns original address. Unencrypted cache urls still exist, they do
    not contain *--sn* (http://r3---orange-mrs2.c.youtube.com/).
    >>> url = 'http://o-o---preferred---sn-25g7rn7k---v18---lscache1.c.youtube.com/'
    >>> translate_cache_url(url)
    'http://o-o---preferred---par08s07---v18---lscache1.c.youtube.com'
    >>> url = 'http://o-o---preferred---sn-vg5obx-hgnl---v16---lscache6.c.youtube.com'
    >>> translate_cache_url(url)
    'http://o-o---preferred---orange-mrs2---v16---lscache6.c.youtube.com'
    >>> url = 'http://r10---sn-25g7rn7l.c.youtube.com/'
    >>> translate_cache_url(url)
    'http://r10---par08s02.c.youtube.com'
    >>> url = 'http://r3---orange-mrs2.c.youtube.com/'
    >>> translate_cache_url(url)
    'http://r3---orange-mrs2.c.youtube.com/'
    >>> url = 'http://r6---sn-5up-u0ol.c.youtube.com'
    >>> translate_cache_url(url)
    'http://r6---ati-tun2.c.youtube.com'
    >>> url = 'http://r1---sn-gxo5uxg-jqbe.googlevideo.com'
    >>> translate_cache_url(url)
    'http://r1---renater-cdg1.googlevideo.com'
    '''
    match = CACHE_URL_REGEXP.match(url)
    config_pytomo.LOG.debug('translating url: %s' % url)
    if not match:
        config_pytomo.LOG.debug('no match')
        new_url = url
    else:
        groups = match.groups()
        assert len(groups) == 8
        groups = filter(None, groups)
        new_url = (''.join((groups[0:3])) + groups[4].translate(TRANSLATION) +
                   ''.join((groups[5:])))
    config_pytomo.LOG.debug('url translated as: %s' % new_url)
    return new_url


def main(argv=None):
    'Program wrapper'
    if argv is None:
        argv = sys.argv[1:]
    usage = '%prog [-v] url_input_files'
    parser = OptionParser(usage=usage)
    parser.add_option('--debug', action='store_true', dest='debug',
                      default=False, help=SUPPRESS_HELP)
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                      default=False, help='run in verbose mode')
    (options, args) = parser.parse_args(argv)
    if options.verbose:
        config_pytomo.LOG.setLevel(logging.INFO)
    if options.debug:
        config_pytomo.LOG.setLevel(logging.DEBUG)
    for in_file in args:
        with open(in_file) as input_file:
            for url in input_file.readlines():
                print translate_cache_url(url.strip())

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    sys.exit(main())
