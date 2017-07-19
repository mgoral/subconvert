#-*- coding: utf-8 -*-

"""
Copyright (C) 2011, 2012, 2013 Michal Goral.

This file is part of Subconvert

Subconvert is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Subconvert is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Subconvert. If not, see <http://www.gnu.org/licenses/>.
"""

from pkg_resources import get_distribution, DistributionNotFound

__appname__ = "Subconvert"
__author__ = "Michał Góral"
__license__ = "GNU GPL 3"
__website__ = "https://github.com/mgoral/subconvert"
__transs__ = [
    "Michał Góral (English)",
    "Michał Góral (Polish)",
]

try:
    __version__ = get_distribution(__appname__.lower()).version
except DistributionNotFound:
    __version__ = '0.x.x-not-installed'
