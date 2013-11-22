#!/usr/bin/env python
"""Module to retrieve the IP address of a URL out of a set of nameservers

   Usage: To use the functions provided in this module independently,
   first place yourself just above pytomo folder.Then:

   import pytomo.start_pytomo
   TIMESTAMP = 'test_timestamp'
   start_pytomo.configure_log_file(TIMESTAMP)

   import pytomo.lib_dns as lib_dns
   url = 'www.example.com'
   lib_dns.get_ip_addresses(url)

   lib_dns.get_default_name_servers()

"""

from __future__ import with_statement, absolute_import

from urlparse import urlsplit
import sys
import time

from .dns import resolver as dns_resolver
from .dns import exception as dns_exception

from . import config_pytomo

def get_default_name_servers():
    """Return a list of IP addresses of default name servers
    >>> get_default_name_servers()
    ... # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    '...............'
    >>> # Check for string of the format 'x.x.x.x'
    """
    default_resolver = dns_resolver.get_default_resolver()
    # find out the exception to catch in case of error
    return default_resolver.nameservers[0]

def reduce_addresses(data):
    '''Return a reduced list of IP addresses and resolvers
    >>> reduce_addresses([('1.1.1.1', 'default'), ('2.2.2.2', 'open'),
                          ('1.1.1.1', 'goo')])
    [('1.1.1.1', 'default_goo'), ('2.2.2.2', 'open')]
    '''
    result = dict()
    req_times = dict()
    for ip_address, resolver, req_duration in data:
        if ip_address in result:
            result[ip_address] = result[ip_address] + '_' + resolver
            req_times[ip_address] = min(req_times[ip_address], req_duration)
        else:
            result[ip_address] = resolver
            req_times[ip_address] = req_duration
    return [(ip, result[ip], req_times[ip]) for ip in result]

def get_ip_addresses(url):
    """
    Return a list of tuples with the IP address and the resolver used
    """
    if not url.startswith('http://'):
        url = 'http://'.join(('', url))
    hostname = urlsplit(url).netloc
    results = []
    # Set the DNS Server
    resolver = dns_resolver.Resolver()
    #Set the lifetime of the DNS query. The default is 30 seconds.
    if config_pytomo.DNS_TIMEOUT:
        resolver.lifetime = config_pytomo.DNS_TIMEOUT
    default_resolver = ('%s_default' % config_pytomo.PROVIDER,
                        get_default_name_servers())
    dns_servers = ([default_resolver] +
                  config_pytomo.EXTRA_NAME_SERVERS_CC)
    for (name, server) in dns_servers:
        config_pytomo.LOG.debug("DNS resolution using %s on this address %s"
                                % (name, server))
        start_resol_time = time.time()
        resolver.nameservers = [server]
        try:
            rdatas = resolver.query(hostname)
            end_resol_time = time.time()
        except dns_resolver.Timeout:
            config_pytomo.LOG.info("DNS timeout for %s" % name)
            rdatas = None
            # If we get a timeout then we ignore the DNS server for the rest of
            # the current round.
            for i, (lname, _) in enumerate(
                                config_pytomo.EXTRA_NAME_SERVERS_CC):
                if lname == name:
                    del config_pytomo.EXTRA_NAME_SERVERS_CC[i]
                    config_pytomo.LOG.info("Ignoring %s for current round of "
                                           "crawl" %name)
            continue
        except dns_exception.DNSException, mes:
            config_pytomo.LOG.exception('Uncaught DNS Exception: %s' % mes)
            rdatas = None
            continue
        except Exception, mes:
            config_pytomo.LOG.exception('Uncaught non-DNS Exception: %s' % mes)
            rdatas = None
            continue
        if rdatas:
            try:
                address = rdatas[0].address
            except AttributeError, mes:
                config_pytomo.LOG.error('DNS failed: %s' % mes)
                continue
            config_pytomo.LOG.debug("URL %s resolved as: %s"
                                    % (hostname, address))
            results.append((address, '_'.join((name, server)),
                            end_resol_time - start_resol_time))
    return reduce_addresses(results)

if __name__ == '__main__':
    import logging
    config_pytomo.LOG = logging.getLogger('dns_test')
    config_pytomo.LOG.setLevel(config_pytomo.LOG_LEVEL)
    HANDLER = logging.StreamHandler(sys.stdout)
    LOG_FORMATTER = logging.Formatter("%(asctime)s - %(filename)s:%(lineno)d - "
                                      "%(levelname)s - %(message)s")
    HANDLER.setFormatter(LOG_FORMATTER)
    config_pytomo.LOG.addHandler(HANDLER)
    import doctest
    doctest.testmod()
    get_ip_addresses(sys.argv[1])

