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
    start_server.py
    Global launcher for the server that displays graphs.
"""

from __future__ import with_statement, absolute_import, print_function
from os.path import abspath
import sys

# assumes the standard distribution paths
PACKAGE_NAME = 'pytomo'
PACKAGE_DIR = abspath(sys.path[0])

if PACKAGE_DIR not in sys.path:
    sys.path.append(PACKAGE_DIR)

#from pytomo import config_pytomo
from pytomo import webpage

#from pytomo import config_pytomo
#config_pytomo.LOG_FILE = '-'

def main():
    'Program wrapper'
    webpage.main()

if __name__ == '__main__':
    sys.exit(main())
