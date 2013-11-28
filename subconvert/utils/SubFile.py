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

import os
from subprocess import Popen, PIPE
import shutil
import codecs
import re
import logging

from subconvert.utils.Locale import _

try:
    import chardet
    IS_CHARDET = True
except ImportError:
    IS_CHARDET = False

log = logging.getLogger('subconvert.%s' % __name__)

class SubFileError(Exception):
    pass

class File:
    """Physical file handler. Reads/writes files, detects their encoding,
    backups etc."""

    DEFAULT_ENCODING = "utf-8"

    def __init__(self, filePath):
        # Will raise IOError if file doesn't exist
        with open(filePath): pass

        self._filePath = filePath

        defaultChardetSize = 5000
        fileSize = os.path.getsize(self._filePath)
        self._chardetSize = defaultChardetSize if fileSize > defaultChardetSize else fileSize

    @property
    def path(self):
        return self._filePath

    @classmethod
    def exists(cls, filePath):
        try:
            with open(filePath):
                return True
        except IOError:
            return False

    def detectEncoding(self):
        encoding = self.DEFAULT_ENCODING

        if IS_CHARDET:
            minimumConfidence = 0.52
            with open(self._filePath, mode='rb',) as file_:
                enc = chardet.detect(file_.read(self._chardetSize))
                log.debug(_("Detecting encoding from %d bytes") % self._chardetSize)
                log.debug(_(" ...chardet: %s") % enc)
            if enc['confidence'] > minimumConfidence:
                encoding = enc['encoding']
                log.debug(_(" ...detected %s encoding.") % enc['encoding'])
            else:
                log.info(_("I am not too confident about encoding (most probably %s). Returning \
                    default %s") % (enc['encoding'], encoding))
        return encoding

    def read(self, encoding = None):
        if encoding is None:
            encoding = self.detectEncoding()

        fileInput = []
        try:
            with open(self._filePath, mode='r', encoding=encoding) as file_:
                fileInput = file_.readlines()
        except LookupError as msg:
            raise SubFileError(_("Unknown encoding name: '%s'.") % encoding)
        except UnicodeDecodeError:
            log.error(_("Couldn't handle '%s' with '%s' encoding.") % (self._filePath, encoding))
            return
        return fileInput

    def _writeFile(self, filePath, content, encoding = None):
        """Safe file writing. Most common mistakes are checked against and reported before write 
        operation. After that, if anything unexpected happens, user won't be left without data or 
        with corrupted one as this method writes to a temporary file and then simply renames it
        (which should be atomic operation according to POSIX but who knows how Ext4 really works.
        @see: http://lwn.net/Articles/322823/)."""

        if encoding is None:
            encoding = self.DEFAULT_ENCODING

        try:
            encodedContent = ''.join(content).encode(encoding)
        except LookupError as msg:
            raise SubFileError(_("Unknown encoding name: '%s'.") % encoding)
        except UnicodeEncodeError:
            raise SubFileError(
                _("There are some characters in '%s' that cannot be encoded to '%s'.")
                % (filePath, encoding))

        tmpFilePath = "%s.tmp" % filePath
        bakFilePath = "%s.bak" % filePath
        with open(tmpFilePath, 'wb') as file_:
            file_.write(encodedContent)

        os.rename(filePath, bakFilePath)
        os.rename(tmpFilePath, filePath)
        os.unlink(bakFilePath)

    def overwrite(self, content, encoding = None):
        assert(len(content) > 0)
        self._writeFile(self._filePath, content, encoding)

    @classmethod
    def write(cls, filePath, content, encoding = None):
        try:
            with open(filePath, 'r', encoding=encoding):
                pass
        except IOError:
            # file doesn't exist - OK
            self._writeFile(filePath, content, encoding)
        else:
            raise IOError(_("File already exists: %s") % filePath)

    def backup(self):
        backupFilePath = ''.join(
            [self._filePath, datetime.datetime.now().strftime('_%y%m%d%H%M%S')]
        )
        try:
            os.remove(backupFilePath)
            log.debug(_("'%s' exists and needs to be removed before backing up.") %
                backupFilePath.encode(locale.getpreferredencoding()))
        except OSError:
            pass
        shutil.copyfile(self._filePath, backupFilePath)
        return backupFilePath

    def detectFps(self, movieFile = None):
        """Fetch movie FPS from MPlayer output or return given default."""

        # TODO: search for known movie file extensions
        if movieFile is None:
            movieFile = ""

        fps = 25.0
        command = ['mplayer',
            '-really-quiet', '-vo', 'null', '-ao', 'null', '-frames', '0', '-identify', movieFile]
        try:
            mpOut, mpErr = Popen(command, stdout=PIPE, stderr=PIPE).communicate()
            log.debug(mpOut)
            log.debug(mpErr)
            fps = float(re.search(r'ID_VIDEO_FPS=([\w/.]+)\s?', str(mpOut)).group(1))
        except OSError:
            log.warning(_("Couldn't run mplayer. It has to be installed and placed in your $PATH \
                to detect FPS."))
        except AttributeError:
            log.warning(_("Couldn't get FPS info from mplayer."))
        else:
            log.info(_("Got %s FPS from '%s'.") % (fps, movieFile))

        return fps

    def __eq__(self, other):
        return self._filePath == other._filePath

    def __ne__(self, other):
        return self._filePath != other._filePath

    def __hash__(self):
        return hash(self._filePath)
