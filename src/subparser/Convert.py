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
import logging
import re
import gettext
import codecs
import datetime
import shutil

from subprocess import Popen, PIPE

import subparser.SubParser as SubParser
import subparser.FrameTime as FrameTime
import subparser.Parsers

try:
    import chardet
    IS_CHARDET = True
except ImportError:
    IS_CHARDET = False


log = logging.getLogger('SubConvert.%s' % __name__)

gettext.bindtextdomain('subconvert', '/usr/lib/subconvert/locale')
gettext.textdomain('subconvert')
_ = gettext.gettext


def backup( filename ):
    """Backup a file to filename_strftime (by moving it, not copying).
    Return a tuple (backed_up_filename, old_filename)"""

    new_arg = filename + datetime.datetime.now().strftime('_%y%m%d%H%M%S')
    try:
        os.remove(new_arg)
        log.debug(_("'%s' exists and needs to be removed before backing up.") % new_arg)
    except OSError:
        pass
    shutil.move(filename, new_arg)
    return (new_arg, filename)

def mplayer_check( filename, fps ):
    """Fetch movie FPS from MPlayer output or return given default."""

    command = ['mplayer', '-really-quiet', '-vo', 'null', '-ao', 'null', '-frames', '0', '-identify',]
    command.append(filename)
    try:
        mp_out = Popen(command, stdout=PIPE).communicate()[0]
        fps = re.search(r'ID_VIDEO_FPS=([\w/.]+)\s?', mp_out).group(1)
    except OSError:
        log.warning(_("Couldn't run mplayer. It has to be installed and placed in your $PATH in order to use auto_fps option."))
    except AttributeError:
        log.warning(_("Couldn't get FPS info from mplayer."))
    else:
        log.info(_("Got %s FPS from '%s'.") % (fps, filename))
    return fps

def detect_encoding( filepath, encoding ):
    """Try to detect file encoding
    'is' keyword checks objects identity and it's the key to disabling
    autodetect when '-e ascii' option is given. It seems that optparse
    creates a new object (which is logical) when given an option from
    shell and overrides a variable in program memory."""
    if IS_CHARDET and encoding is 'ascii': 
        file_size = os.path.getsize(filepath)
        size = 2000 if file_size > 2000 else file_size
        with open(filepath, mode='r',) as file_:
            enc = chardet.detect(file_.read(size))
            log.debug(_("Detecting encoding from %d bytes") % size)
            log.debug(_(" ...chardet: %s") % enc)
        if enc['confidence'] > 0.60:
            encoding = enc['encoding']
            log.debug(_(" ...detected %s encoding.") % enc['encoding'])
        else:
            log.info(_("I am not too confident about encoding (most probably %s). Skipping check.") % enc['encoding'])
    return encoding

def convert_file(filepath, file_encoding, file_fps, output_format, output_extension = ''):
    """Convert a file to given output format (with optional output extension)."""

    cls = SubParser.GenericSubParser.__subclasses__()
    conv = None
    for c in cls:
        # Obtain user specified subclass
        if c.__OPT__ == output_format:
            filename, extension = os.path.splitext(filepath)
            extension = output_extension if output_extension else c.__EXT__
            conv = c(filename + '.' + extension, file_fps, file_encoding)
            break
    if not conv:
        raise NameError
    with codecs.open(filepath, mode='r', encoding=file_encoding) as file_:
        file_input = file_.readlines()

    lines = []
    log.info(_("Trying to parse %s...") % filepath)
    sub_pair = [0, 0]
    for cl in cls:
        if not lines:
            for parsed in cl(filepath, file_fps, file_encoding, file_input).parse():
                if not sub_pair[1] and conv.__WITH_HEADER__: # Only the first element
                    header = parsed['sub'].get('header')
                    if type(header) != dict:
                        header = {}
                    header = conv.convert_header(header)
                    if header:
                        lines.append(header.decode(conv.encoding))
                sub_pair[0] = sub_pair[1]
                sub_pair[1] = parsed
                try:
                    if sub_pair[0]:
                        if not sub_pair[0]['sub']['time_to']:
                            if sub_pair[1] is None:
                                sub_pair[1]['sub']['time_to'] = \
                                    sub_pair[1]['sub']['time_from'] + FrameTime.FrameTime(file_fps, 'ss', seconds = 2.5)
                            else:
                                sub_pair[0]['sub']['time_to'] = \
                                    sub_pair[0]['sub']['time_from'] + \
                                    (sub_pair[1]['sub']['time_from'] - sub_pair[0]['sub']['time_from']) * 0.85
                        sub = conv.convert(sub_pair[0])
                        lines.append(sub.decode(conv.encoding))
                except AssertionError:
                    log.warning(_("Correct time not asserted for subtitle %d. Skipping it...") % (sub_pair[0]['sub_no']))
                    log.debug(_(".. incorrect subtitle pair times: (%s, %s)") % (sub_pair[0]['sub']['time_from'], sub_pair[1]['sub']['time_from']))
    return (conv, lines)


