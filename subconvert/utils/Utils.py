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
from subprocess import Popen, PIPE
import shutil
import codecs
import re
import logging

try:
    import chardet
    IS_CHARDET = True
except ImportError:
    IS_CHARDET = False

log = logging.getLogger('subconvert.%s' % __name__)

class FileExist(Exception):
    pass

def detectEncoding(filePath, maxSize=5000, defaultEncoding="utf8"):
    """Try to detect file encoding
    'is' keyword checks objects identity and it's the key to disabling
    autodetect when '-e ascii' option is given. It seems that optparse
    creates a new object (which is logical) when given an option from
    shell and overrides a variable in program memory."""
    encoding = defaultEncoding
    if IS_CHARDET:
        minimumConfidence = 0.52
        fileSize = os.path.getsize(filePath)
        size = maxSize if fileSize > maxSize else fileSize
        with open(filePath, mode='rb',) as file_:
            enc = chardet.detect(file_.read(size))
            log.debug(_("Detecting encoding from %d bytes") % size)
            log.debug(_(" ...chardet: %s") % enc)
        if enc['confidence'] > minimumConfidence:
            encoding = enc['encoding']
            log.debug(_(" ...detected %s encoding.") % enc['encoding'])
        else:
            log.info(_("I am not too confident about encoding (most probably %s). Returning \
                default %s") % (enc['encoding'], defaultEncoding))
    return encoding

def readFile(filePath, fileEncoding=None):
    if fileEncoding is None:
        fileEncoding = detectEncoding(filePath)
    fileInput = []
    try:
        with codecs.open(filePath, mode='r', encoding=fileEncoding) as file_:
            fileInput = file_.readlines()
    except LookupError as msg:
        raise LookupError(_("Unknown encoding name: '%s'.") % fileEncoding)
    except UnicodeDecodeError:
        log.error(_("Couldn't handle '%s' with '%s' encoding.") % (filePath, fileEncoding))
        return
    return fileInput

def saveToFile(content, filePath, fileEncoding="utf8"):
    assert(len(content) > 0)

    try:
        with codecs.open(filePath, 'r', encoding=fileEncoding) as file_:
            pass
    except IOError:
        # file doesn't exist - OK
        try:
            with codecs.open(filePath, 'w', encoding=fileEncoding) as file_:
                file_.writelines(content)
        except LookupError as msg:
            raise LookupError(_("Unknown encoding name: '%s'.") % fileEncoding)
    else:
        raise FileExist

def backup(filePath):
    """Backup a file to filename_strftime (by moving it, not copying).
    Return a tuple (backed_up_filename, old_filename)"""

    backupFilePath = ''.join([filePath, datetime.datetime.now().strftime('_%y%m%d%H%M%S')])
    try:
        os.remove(backupFilePath)
        log.debug(_("'%s' exists and needs to be removed before backing up.") %
            backupFilePath.encode(locale.getpreferredencoding()))
    except OSError:
        pass
    shutil.move(filePath, backupFilePath)
    return (backupFilePath, filePath)


def detectFps(movieFile):
    """Fetch movie FPS from MPlayer output or return given default."""

    fps = 25
    command = ['mplayer',
        '-really-quiet', '-vo', 'null', '-ao', 'null', '-frames', '0', '-identify', movieFile]
    try:
        mpOut, mpErr = Popen(command, stdout=PIPE, stderr=PIPE).communicate()
        log.debug(mpOut)
        log.debug(mpErr)
        fps = re.search(r'ID_VIDEO_FPS=([\w/.]+)\s?', mpOut).group(1)
    except OSError:
        log.warning(_("Couldn't run mplayer. It has to be installed and placed in your $PATH to \
            detect FPS."))
    except AttributeError:
        log.warning(_("Couldn't get FPS info from mplayer."))
    else:
        log.info(_("Got %s FPS from '%s'.") % (fps, movieFile))

    return fps
