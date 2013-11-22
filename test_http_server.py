#!/usr/bin/env python
from __future__ import absolute_import

import urllib2
from pytomo import lib_youtube_download
from pytomo import start_pytomo


start_pytomo.configure_log_file('http_test')

ip_address_uri = ("http://173.194.5.107/videoplayback?sparams=id%2Cexpire%2Cip%2Cipbits%2Citag%2Calgorithm%2Cburst%2Cfactor&algorithm=throttle-factor&itag=34&ipbits=8&burst=40&sver=3&signature=CE60F2B393D8E55A0B8529FCB0AAEDEC876A2C8C.9DAE7AE311AD2D4AE8094715551F8E2482DEA790&expire=1304107200&key=yt1&ip=193.0.0.0&factor=1.25&id=39d17ea226880992")

info = {'accept-ranges': 'bytes',
         'cache-control': 'private, max-age=20576',
         'connection': 'close',
         'Content-length': '16840065',
         'content-type': 'video/x-flv',
         'date': 'Fri, 29 Apr 2011 14:12:04 GMT',
         'expires': 'Fri, 29 Apr 2011 19:55:00 GMT',
         'last-modified': 'Fri, 18 Jun 2010 12:05:11 GMT',
         'server': 'gvs 1.0',
         'via': '1.1 goodway (NetCache NetApp/6.1.1), 1.1 s-proxy (NetCache NetApp/ 5.6.2R2)',
         'x-content-type-options': 'nosniff'}


def mock_response(req):
    if req.get_full_url() == ip_address_uri:
        mock_file = open('test_pytomo/OdF-oiaICZI.flv')
        resp = urllib2.addinfourl(mock_file,info ,
                                  req.get_full_url())
        resp.code = 200
        resp.msg = "OK"
        return resp

class MyHTTPHandler(urllib2.HTTPHandler):
    def http_open(self, req):
        print "mock opener"
        return mock_response(req)

my_opener = urllib2.build_opener(MyHTTPHandler)
urllib2.install_opener(my_opener)


filedownloader = lib_youtube_download.FileDownloader(30)
h = filedownloader._do_download(ip_address_uri)
print h
#
#response  = urllib2.urlopen(ip_address_uri)
#print response.read()
#print response.code
#print response.msg
