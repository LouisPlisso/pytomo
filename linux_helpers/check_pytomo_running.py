#!/usr/bin/env python
''' Module to test if pytomo is running and restart it if not.
It uses the "ps" shell command to check
'''
__author__  = 'Ana Oprea'
__date__    = '07.11.2012'

import sys
import os
import subprocess
import logging
from time import sleep

BASE_PATH = '/home/capture/pytomo'
PYTOMO_PKG = 'Pytomo'
CRAWL_START = 'start_crawl.py'
#WEB_START = 'start_server.py'
WEB_START = 'gunicorn pytomo.webpage:wsgi_app'
YT_SERVICE = 'youtube'
YT_WEB_PORT = '5555'
DM_SERVICE = 'dailymotion'
DM_WEB_PORT = '7777'
LOG_FILE = 'check_pytomo_running.log'
# script expects user input:
# Y/N to start crawling
# provider/ISP
# proxies in the format: {'http': 'http://proxy:8080/'}
# max. number of videos
#USER_INPUT_FILE = os.path.join(BASE_PATH, 'user.txt')
HTTP_PROXY = ' ' #http://p-goodway.rd.francetelecom.fr:3128/'

# for interactive call: do not add multiple times the handler
if 'LOG' not in locals():
    LOG = None
LOG_LEVEL = logging.DEBUG
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

LOG = configure_log(log_file=os.path.join(BASE_PATH, LOG_FILE))

def get_service_path(service):
    ''' Return the path of the Pytomo package for a service.
    >>> BASE_PATH = '/home/capture/pytomo'
    >>> PYTOMO_PKG = 'Pytomo'
    >>> service = 'youtube'
    >>> os.path.join(BASE_PATH, service, PYTOMO_PKG) == \
            get_service_path(service)
    True
    '''
    return os.path.join(BASE_PATH, service, PYTOMO_PKG)

def check_operation_running(start_cmd, service, port=None):
    ''' Verify that the pytomo processes are running using ps:
    ps -ef | awk '/start_crawl/&&/dailymotion/&&!/awk/'
    '''
    # we verify crawl or web interface
    # ps options:
    # -f to display full command name
    # -C to match python cmd
    # --col 500 to display the information on a column with of 500 char
    if port:
        operation = 'graphical web interface'
        bash_cmd = ["ps -fC python --cols 500", 
	            #"awk /%s/&&/%s/&&!/awk/" % (start_cmd.split()[0], port)]
                    '%s -b 0.0.0.0:%s' % (start_cmd, port)]
    else:
        operation = 'crawl'
        bash_cmd = ["ps -fC python --cols 500", 
	            "awk /%s/&&/%s/&&!/awk/" % (start_cmd.split()[0], service)]
    LOG.debug('bash_cmd=*%s*' % bash_cmd)
    proc1 = subprocess.Popen(bash_cmd[0].split(), stdout=subprocess.PIPE)
    try:
        proc2 = subprocess.Popen(bash_cmd[1].split(), stdin=proc1.stdout,
                                 stdout=subprocess.PIPE)
    except ValueError, mes:
        LOG.error('ERROR while running *%s*: %s' % (bash_cmd[0], mes))
    output, error = proc2.communicate()
    LOG.debug('output=*%s*' % output)
    if error:
        LOG.error('ERROR while running *%s*: %s' % (bash_cmd[1], error))
    # eliminate leading/trailing empty lines and separate lines
    nr_processes = len(output.strip().split('\n'))
    LOG.debug('nr_proc=%i' % nr_processes)
    LOG.debug('output=*%s*' % output)
    if not output:
        LOG.error('%s %s is not working! Trying to start...' % (service,
                                                                  operation))
        # call command from the Pytomo package directory to correcly have the
        # database directory
        os.chdir(get_service_path(service))
        if port:
            bash_cmd = ('%s -b 0.0.0.0:%s > /dev/null 2>&1 &'
                        % (start_cmd, port))
        else:
            start_cmd = os.path.join(get_service_path(service), start_cmd)
            bash_cmd = ('%s -s %s -b -c --http-proxy=%s > /dev/null 2>&1 &' %
                        (start_cmd, service, HTTP_PROXY))
        proc = subprocess.Popen(bash_cmd, stdout=subprocess.PIPE, shell=True)
        output, error = proc.communicate()
        LOG.debug('output=*%s*' % output)
        if error:
            LOG.error('ERROR while running *%s*: %s' % (bash_cmd, error))
    if nr_processes > 1:
        LOG.error('There are too many %s %s processes running!' % (service,
                                                                   operation))
    for process in (proc1, proc2):
        process.stdout.close()

def main(argv=None):
    ''' Program wrapper'''
    # youtube crawl and graphical web interface
    check_operation_running(CRAWL_START, YT_SERVICE)
    sleep(1)
    check_operation_running(WEB_START, YT_SERVICE, port=YT_WEB_PORT)
    sleep(1)
    # dailymotion crawl and graphical web interface
    check_operation_running(CRAWL_START, DM_SERVICE)
    sleep(1)
    check_operation_running(WEB_START, DM_SERVICE, port=DM_WEB_PORT)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    sys.exit(main())
