#-*- coding: utf-8 -*-

"""
This file is part of SubConvert.

SubConvert is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SubConvert is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SubConvert.  If not, see <http://www.gnu.org/licenses/>.
"""


import os

def get_install_path(given_path, split_string='subconvert'):
    try:
        ret_list = os.path.dirname(given_path).split(split_string)
    except AttributeError:
        return ''
    if len(ret_list) < 2:
        return os.path.dirname(given_path)
    return ret_list[0]

def get_locale_path(given_path, locale_name='subconvert'):
    install_path = get_install_path(given_path, locale_name)
    if install_path:
        return "%s/%s" % ( install_path, "locale")
    return "./locale/"

def get_dirname(filename):
    return os.path.split(os.path.abspath(filename))[0]

