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
import datetime

from subconvert.utils.Locale import _, P_
from subconvert.utils.SubException import SubException

try:
    import chardet
    IS_CHARDET = True
except ImportError:
    IS_CHARDET = False

log = logging.getLogger('Subconvert.%s' % __name__)

class SubFileError(SubException):
    pass

class VideoInfo:
    fps = 23.976 # FPS value
    videoPath = None # Video file path from which FPS has been fetched

    def __init__(self, fps, videoPath = None):
        self.fps = fps
        self.videoPath = videoPath

class File:
    """Physical file handler. Reads/writes files, detects their encoding,
    backups etc."""

    DEFAULT_ENCODING = "utf-8"
    MOVIE_EXTENSIONS = ('avi', 'mkv', 'mpg', 'mp4', 'wmv', 'rmvb', 'mov', 'mpeg')

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
                log.debug(P_(
                    "Detecting encoding from %d byte",
                    "Detecting encoding from %d bytes",
                    self._chardetSize) % self._chardetSize)
                log.debug(_(" ...chardet: %s") % enc)
            if enc['confidence'] > minimumConfidence:
                encoding = enc['encoding']
                log.debug(_(" ...detected %s encoding.") % enc['encoding'])
            else:
                log.debug(_("I am not too confident about encoding (most probably %(enc)s). "
                    "Returning default %(def)s") % {"enc": enc["encoding"], "def": encoding})
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
            vals = {"file": self._filePath, "enc": encoding}
            raise SubFileError(_("Cannot handle '%(file)s' with '%(enc)s' encoding.") % vals)
        return fileInput

    @classmethod
    def _writeFile(cls, filePath, content, encoding = None):
        """Safe file writing. Most common mistakes are checked against and reported before write
        operation. After that, if anything unexpected happens, user won't be left without data or
        with corrupted one as this method writes to a temporary file and then simply renames it
        (which should be atomic operation according to POSIX but who knows how Ext4 really works.
        @see: http://lwn.net/Articles/322823/)."""

        filePath = os.path.realpath(filePath)
        log.debug(_("Real file path to write: %s" % filePath))

        if encoding is None:
            encoding = File.DEFAULT_ENCODING

        try:
            encodedContent = ''.join(content).encode(encoding)
        except LookupError as msg:
            raise SubFileError(_("Unknown encoding name: '%s'.") % encoding)
        except UnicodeEncodeError:
            raise SubFileError(
                _("There are some characters in '%(file)s' that cannot be encoded to '%(enc)s'.")
                % {"file": filePath, "enc": encoding})

        tmpFilePath = "%s.tmp" % filePath
        bakFilePath = "%s.bak" % filePath
        with open(tmpFilePath, 'wb') as f:
            f.write(encodedContent)
            # ensure that all data is on disk.
            # for performance reasons, we skip os.fsync(f.fileno())
            f.flush()

        try:
            os.rename(filePath, bakFilePath)
        except FileNotFoundError:
            # there's nothing to move when filePath doesn't exist
            # note the Python bug: http://bugs.python.org/issue16074
            pass

        os.rename(tmpFilePath, filePath)

        try:
            os.unlink(bakFilePath)
        except FileNotFoundError:
            pass

    def overwrite(self, content, encoding = None):
        self._writeFile(self._filePath, content, encoding)

    @classmethod
    def write(cls, filePath, content, encoding = None):
        try:
            with open(filePath, 'r', encoding=encoding):
                pass
        except IOError:
            # file doesn't exist - OK
            pass
        else:
            raise IOError(_("File already exists: %s") % filePath)
        File._writeFile(filePath, content, encoding)

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

    def detectFps(self, movieFile = None, default = 23.976):
        """Fetch movie FPS from MPlayer output or return given default."""

        if movieFile is None:
            movieFile = self._searchForMovieFile()
        return File.detectFpsFromMovie(movieFile, default)

    @classmethod
    def detectFpsFromMovie(cls, movieFile, default = 23.976):
        """Fetch movie FPS from MPlayer output or return given default."""

        # initialize with a default FPS value, but not with a movieFile
        videoInfo = VideoInfo(float(default))

        command = ['mplayer',
            '-really-quiet', '-vo', 'null', '-ao', 'null', '-frames', '0', '-identify', movieFile]

        try:
            mpOut, mpErr = Popen(command, stdout=PIPE, stderr=PIPE).communicate()
            log.debug(mpOut)
            log.debug(mpErr)

            # Overwrite default (not fetched from video) values.
            # If there's any error on changing videoInfo.fps, whole videoInfo won't be changed at
            # all.
            videoInfo.fps = float(re.search(r'ID_VIDEO_FPS=([\w/.]+)\s?', str(mpOut)).group(1))
            videoInfo.videoPath = movieFile
        except OSError:
            log.warning(_("Couldn't run mplayer. It has to be installed and placed in your $PATH "
                "to detect FPS."))
        except AttributeError:
            log.warning(_("Couldn't get FPS from %(movie)s. Using default value: %(fps)s.") %
                {"movie": movieFile, "fps": videoInfo.fps})
        else:
            pass
            log.debug(P_(
                "Got %(fps)s FPS from '%(movie)s'.",
                "Got %(fps)s FPS from '%(movie)s'.",
                int(videoInfo.fps)) % {"fps": videoInfo.fps, "movie": videoInfo.videoPath})

        return videoInfo

    def _searchForMovieFile(self):
        filename = os.path.splitext(self._filePath)[0]
        for ext in self.MOVIE_EXTENSIONS:
            fileWithLowerExt = '.'.join((filename, ext))
            fileWithUpperExt = '.'.join((filename, ext.upper()))

            if os.path.isfile(fileWithLowerExt):
                return fileWithLowerExt
            elif os.path.isfile(fileWithUpperExt):
                return fileWithUpperExt
        return ""

    def __eq__(self, other):
        return self._filePath == other._filePath

    def __ne__(self, other):
        return self._filePath != other._filePath

    def __hash__(self):
        return hash(self._filePath)
