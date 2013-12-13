#!/usr/bin/env python
''' Module to upload log files on the centralised server.
Connects to FTP server anonimously.

Author: Ana Oprea
Date: 13.11.2012

Usage:
To use the functions provided in this module independently, first place yourself
just above pytomo folder. Then:
>>> import pytomo.start_pytomo as start_pytomo
>>> TIMESTAMP = 'test_timestamp'
>>> start_pytomo.configure_log_file(TIMESTAMP)
>>> from tempfile import NamedTemporaryFile
>>> f = NamedTemporaryFile(delete=False)
>>> import pytomo.lib_data_centralisation as lib_data_centralisation
>>> ftp = lib_data_centralisation.PytomoFTP()
>>> ftp.upload_file(f.name)
0
>>> ftp.close_connection()
0
>>> f.close()
>>> os.unlink(f.name)
'''
from __future__ import with_statement, absolute_import
import urllib2
import ftplib
import os
# only for logging
import logging
import sys
import time

# global config
try:
    from . import config_pytomo
except ValueError:
    import config_pytomo

# uncomment if FTP server runs on a different port
#MAIN_SERVER_PORT = 2121
DIR_TO_STORE = 'pytomo_db_dir'
STORE_CMD = 'STOR %s'
SUCCESS_CODE = 0
ERROR_CODE = 1

class PytomoFTP:
    ''' Pytomo class to implement a simple FTP client
    '''

    def __init__(self):
        ''' Connect and login to FTP server
        '''
        if not config_pytomo.LOG:
            self.logger_ftp()
        self.created = False
        if config_pytomo.PROXIES:
            proxy = urllib2.ProxyHandler(config_pytomo.PROXIES)
            opener = urllib2.build_opener(proxy)
            urllib2.install_opener(opener)
        try:
            self.py_ftp = ftplib.FTP(config_pytomo.CENTRALISATION_SERVER)
            # uncomment if FTP server runs on a different port
            #self.py_ftp = ftplib.FTP()
            #self.py_ftp.connect(MAIN_SERVER, MAIN_SERVER_PORT)
        except ftplib.all_errors, mes:
            config_pytomo.LOG.error('Could not connect to FTP server %s\n%s',
                                    config_pytomo.CENTRALISATION_SERVER, mes)
            return
        try:
            self.py_ftp.login()
        except ftplib.all_errors, mes:
            config_pytomo.LOG.error('Could not login to FTP server %s\n%s',
                                    config_pytomo.CENTRALISATION_SERVER, mes)
            return
        self.created = True

    def upload_file(self, full_filename):
        ''' Upload specific file to FTP directory
        '''
        if not self.created:
            config_pytomo.LOG.error('Connection to server %s could not be '
                                    'established, cannot upload file',
                                    config_pytomo.CENTRALISATION_SERVER)
            return ERROR_CODE
        # change directory on the FTP server
        try:
            self.py_ftp.cwd(DIR_TO_STORE)
        except ftplib.all_errors, mes:
            config_pytomo.LOG.error('Could not change directory to %s\n%s',
                                    DIR_TO_STORE, mes)
            return ERROR_CODE
        # when uploading the file, it should only be the filename, no path
        # otherwise the whole directory structure will be created on the FTP
        file_path = os.path.dirname(full_filename)
        os.chdir(file_path)
        file_to_upload = os.path.basename(full_filename)
        try:
            f_obj = open(file_to_upload, 'rb')
        except IOError:
            config_pytomo.LOG.error('Could not open %s', full_filename)
            return ERROR_CODE
        try:
            self.py_ftp.storbinary(STORE_CMD % file_to_upload, f_obj)
        except ftplib.all_errors, mes:
            config_pytomo.LOG.error('Could not upload file %s\n%s',
                                    full_filename, mes)
            return ERROR_CODE
        f_obj.close()
        return SUCCESS_CODE

    def close_connection(self):
        ''' Send quit to FTP server
        '''
        try:
            self.py_ftp.quit()
        except ftplib.all_errors, mes:
            config_pytomo.LOG.error('Could not close connection to %s\n%s',
                                    config_pytomo.CENTRALISATION_SERVER, mes)
            return ERROR_CODE
        return SUCCESS_CODE

    @staticmethod
    def logger_ftp():
        ''' Initialze the logger'''
        config_pytomo.LOG = logging.getLogger('pytomo_ftp')
        # to not have console output
        config_pytomo.LOG.propagate = False
        config_pytomo.LOG.setLevel(config_pytomo.LOG_LEVEL)
        timestamp = time.strftime("%Y-%m-%d.%H_%M_%S")
        if config_pytomo.LOG_FILE == '-':
            handler = logging.StreamHandler(sys.stdout)
        else:
            log_file = os.path.sep.join((config_pytomo. LOG_DIR,
                                '.'.join((timestamp, config_pytomo.LOG_FILE))))
            try:
                with open(log_file, 'a') as _:
                    pass
            except IOError:
                raise IOError('Logfile %s could not be open for writing' %
                                                                    log_file)
            handler = logging.FileHandler(filename=log_file)
        log_formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                  "%(levelname)s - %(message)s")
        handler.setFormatter(log_formatter)
        config_pytomo.LOG.addHandler(handler)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
