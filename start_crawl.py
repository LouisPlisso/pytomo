#!/usr/bin/env python

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

"""
    start_crawl.py
    Global launcher for the pytomo package
"""

from os.path import abspath
from sys import path

# assumes the standard distribution paths
PACKAGE_NAME = 'pytomo'
PACKAGE_DIR = abspath(path[0])

if PACKAGE_DIR not in path:
    path[0:0] = [PACKAGE_DIR]

import pytomo

try:
    import setup
    version = setup.VERSION
except ImportError:
    version = None

if __name__ == '__main__':
    pytomo.start_pytomo.main(version=version)
