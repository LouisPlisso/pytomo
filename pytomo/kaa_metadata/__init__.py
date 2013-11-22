# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# kaa_metadata.__init__.py
# -----------------------------------------------------------------------------
# $Id: __init__.py 3824 2009-01-31 18:02:16Z dmeyer $
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2006 Thomas Schueppel, Dirk Meyer
#
# First Edition: Thomas Schueppel <stain@acm.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
#
# Please see the file AUTHORS for a complete list of authors.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------------

from __future__ import absolute_import

# import factory code for kaa_metadata access
from .factory import register, parse
from .version import VERSION
# not needed here, and imports a function not windows compatible
#import disc.cdrom as cdrom

from .core import (Media, MEDIA_AUDIO, MEDIA_VIDEO, MEDIA_IMAGE, MEDIA_AV,
                   MEDIA_SUBTITLE, MEDIA_CHAPTER, MEDIA_DIRECTORY,
                   MEDIA_DISC, MEDIA_GAME, EXTENSION_STREAM,
                   EXTENSION_DEVICE, EXTENSION_DIRECTORY)

if False:
    # to trick the module finder of pyinstaller
    from .video import mp4, flv, mpeg, riff
    from .audio import mp3, eyeD3
    #from .image import *
    from .misc import xmlfile

# use network functions
USE_NETWORK = 1

# Video parsers
register('video/quicktime', ('mov', 'qt', 'mp4', 'mp4a', '3gp', '3gp2', 'mk2'), 'video.mp4')
register('video/flv', ('flv',), 'video.flv')
#register('video/asf', ('asf','wmv','wma'), 'video.asf')
#register('application/mkv', ('mkv', 'mka'), 'video.mkv')
register('video/mpeg', ('mpeg', 'mpg', 'mp4', 'ts'), 'video.mpeg')
#register('application/ogg', ('ogm', 'ogg'), 'video.ogm')
#register('video/real', ('rm', 'ra', 'ram'), 'video.real')
register('video/avi', ('wav', 'avi'), 'video.riff')
#register('video/vcd', ('cue',), 'video.vcd')

# Audio parsers
#register('audio/mpeg', ('mp3',), 'audio.mp3')
# register('audio/ac3', ('ac3',), 'audio.ac3')
# register('application/adts', ('aac',), 'audio.adts')
# register('audio/m4a', ('m4a',), 'audio.m4a')
# register('application/ogg', ('ogg',), 'audio.ogg', magic='OggS\00')
# register('application/pcm', ('aif','voc','au'), 'audio.pcm')

# Disc parsers
#register('audio/cd', EXTENSION_DEVICE, 'disc.audio')
#register('video/dvd', EXTENSION_DEVICE, 'disc.dvd')
#register('video/dvd', EXTENSION_DIRECTORY, 'disc.dvd')
#register('video/dvd', ('iso',), 'disc.dvd')
#register('video/vcd', EXTENSION_DEVICE, 'disc.vcd')
#register('cd/unknown', EXTENSION_DEVICE, 'disc.data')

# Image parsers
# if 0:
    # exiv2 based generic image parser. Experimental
    # add list of all supported extensions
    # register('image/tiff', ('tif','tiff', 'jpg'), 'image.generic')
    # register('image/png', ('png',), 'image.png')
# else:
    # register('image/bmp', ('bmp', ), 'image.bmp')
    # register('image/gif', ('gif', ), 'image.gif')
    # register('image/jpeg', ('jpg','jpeg'), 'image.jpg')
    # register('image/png', ('png',), 'image.png')
    # register('image/tiff', ('tif','tiff'), 'image.tiff')

# Games parsers
#register('games/gameboy', ('gba', 'gb', 'gbc'), 'games.gameboy')
#register('games/snes', ('smc', 'sfc', 'fig'), 'games.snes')

# Misc parsers
# register('directory', EXTENSION_DIRECTORY, 'misc.directory')
#register('text/xml', ('xml', 'fxd', 'html', 'htm'), 'misc.xmlfile')

# These parsers are prone to producing false positives, so we use them
# last.  They should be fixed.
# register('text/plain', EXTENSION_STREAM, 'audio.webradio')
# register('application/flac', ('flac',), 'audio.flac')
