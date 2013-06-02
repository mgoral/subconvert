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

"""
Original optparse module is written by Gregory P. Ward and is
copyrighted. If you are interested in using optparse code in your
own work, please see the header of optparse.py located in your
Python standard library.
"""



import optparse
import gettext
import .SubPath

t = gettext.translation(
    domain='subconvert',
    localedir=SubPath.get_locale_path(__file__),
    fallback=True)
gettext.install('subconvert')
_ = t.ugettext

class SubOptionParser(optparse.OptionParser):
    """Customized implementation of optparse module"""

    def __init__(self, *args, **kwargs):
        self.group_general = None
        optparse.OptionParser.__init__(self, *args, **kwargs)

    def _add_help_option(self):
        if self.group_general is None:
            self.group_general = optparse.OptionGroup(self, _("General options"))
        self.group_general.add_option("-h", "--help",
            action="help",
            help=_("Show this help message and exit."))

    def _add_version_option(self):
        if self.group_general is None:
            self.group_general = optparse.OptionGroup(self, _("General options"))
        self.group_general.add_option("--version",
            action="version",
            help=_("Show program's version number and exit."))

    def set_usage(self, usage):
        if usage is None:
            self.usage = _("%prog [options]")
        elif usage is optparse.SUPPRESS_USAGE:
            self.usage = None
        else:
            self.usage = usage

class SubHelpFormatter(optparse.IndentedHelpFormatter):
    """Customized IndentedHelpFormatter"""

    def __init__(self, *args, **kwargs):
        optparse.IndentedHelpFormatter.__init__(self, *args, **kwargs)

    def format_usage(self, usage):
        return "%s\n" % usage

