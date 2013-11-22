#!/usr/bin/env python
""" Module to give informations on the ASes seen per DNS in the database
"""

import sqlite3
from re import match
#from string import strip
from collections import defaultdict

DNS_RESOLVERS = ('open', 'google', 'default')


def as_ip_min_max(prefix):
    """Return a tuple with the min and max value of IP (converted to int) on
    the AS
    >>> as_ip_min_max('0.0.0.1/32')
    (1, 1)
    >>> as_ip_min_max('0.0.0.1/0')
    (0, 4294967295)
    >>> as_ip_min_max('209.85.147.0/24')
    (3512046336, 3512046591)
    >>> as_ip_min_max('209.85.147.11/24')
    (3512046336, 3512046591)
    >>> as_ip_min_max('209.85.147.0/23')
    (3512046080, 3512046591)
    >>> as_ip_min_max('209.85.147.155/23')
    (3512046080, 3512046591)
    """
    match_prefix = match("(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/(\d{1,2})",
                         prefix)
    if not match_prefix:
        return None
    ip_addr, prefix = match_prefix.groups()
    prefix = int(prefix)
    assert prefix <= 32, 'Prefix is at most 32 bits'
    bin_prefix = '0b' + ('1' * prefix) + ('0' * (32 - prefix))
    int_prefix = int(bin_prefix, 2)
    ip_addr = ip2int(ip_addr)
    min_ip = ip_addr & int_prefix
    if prefix == 32:
        max_ip = ip_addr
    else:
        max_ip = min_ip + int('0b' + '1' * (32 - prefix), 2)
    return min_ip, max_ip

def ip2int(ip_addr):
    """Return the int value of IP address
    >>> ip2int('0.0.0.1')
    1
    >>> ip2int('0.0.1.0')
    256
    >>> ip2int('0.0.1.1')
    257
    >>> ip2int('255.255.255.255')
    4294967295
    """
    ret = 0
    ip_matcher = match("(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})", ip_addr)
    if not ip_matcher:
        return 0
    for i in xrange(4):
        int_group = int(ip_matcher.groups()[i])
        assert int_group < 256, "Incorrect IP address"
        ret = (ret << 8) + int_group
    return ret

def int2ip(int_ip_addr):
    """Return the string value of an IP address in int form
    >>> int2ip(1)
    '0.0.0.1'
    >>> int2ip(256)
    '0.0.1.0'
    >>> int2ip(4294967295)
    '255.255.255.255'
    """
    bin_ip_addr = bin(int_ip_addr).split('0b')[1].rjust(32, '0')
    ip_addr = []
    for i in xrange(4):
        ip_addr.append(str(int(bin_ip_addr[8 * i:8 * (i + 1)], 2)))
    return '.'.join(ip_addr)

def construct_ip_map(goo_file='as_list_goo.txt',
                     you_eu_file='as_list_you_eu.txt'):
    """Fills the IP MAP for Google and YouTube according to extraction of BGP in
    the input text files
    """
    ip_map = {}
    for name, as_file in (('GOO', goo_file), ('YT_EU', you_eu_file)):
        with open(as_file) as input_file:
            ip_map[name] = map(as_ip_min_max, input_file.readlines())
    return ip_map

IP_MAP = construct_ip_map()

def match_ip(ip_addr):
    "Return the AS of the IP according to the IP_MAP"
    list_as_found = []
    if type(ip_addr) == str:
        ip_addr = ip2int(ip_addr)
    for as_name, int_prefixes in IP_MAP.items():
        most_specific = 2**32
        as_found = None
        for min_ip, max_ip in int_prefixes:
            if ip_addr >= min_ip and ip_addr <= max_ip:
                as_found = as_name
                if (max_ip - min_ip) < most_specific:
                    most_specific = (max_ip - min_ip)
                #print 'match on %s, %s' % tuple(map(int2ip, (min_ip, max_ip)))
        if as_found:
            list_as_found.append((most_specific, as_found))
    if len(list_as_found) > 1:
        print 'multiple ASes found for this IP: %s' % int2ip(ip_addr)
        # smallest matching prefix will be first
        list_as_found.sort()
    if not list_as_found:
        return None
    else:
        return list_as_found[0][1]

def as_data(db_file):
    """Function to plot the data in the database. Creates sub plots for
     the column names.
    """
    conn = sqlite3.connect(str(db_file),
                           detect_types=sqlite3.PARSE_DECLTYPES)
    cur = conn.cursor()
    user_table = cur.execute('select name from sqlite_master '
                             'where type = "table"').fetchall()[0][0]
    data = dict()
    #find the number of resolvers used.
    for resolver in DNS_RESOLVERS:
        cmd = ' '.join(("select IP from", user_table,
                        "where Resolver LIKE '%%%s%%';" % resolver))
        cur.execute(cmd)
        data[resolver] = [ip2int(x[0]) for x in cur.fetchall()]
    return data

def compute_stats_db(db_file):
    "Return the stats for the distribution of ASes per DNS resolver"
    data = as_data(db_file)
    output = dict()
    for resolver, ips in data.items():
        as_list = map(match_ip, ips)
        output[resolver] = [(as_name, len([x for x in as_list if x == as_name]))
                            for as_name in set(as_list)]
    return output

if __name__ == '__main__':
    import doctest
    doctest.testmod()

