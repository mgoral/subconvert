#-*- coding: utf-8 -*-

"""
    This file is part of Subconvert.

    Subconvert is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Subconvert is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Subconvert.  If not, see <http://www.gnu.org/licenses/>.
"""

import copy
from PyQt4 import QtGui, QtCore, Qt

from subconvert.parsing.Core import SubManager, SubParser, SubConverter, SubManager
from subconvert.parsing.Formats import *
from subconvert.utils.SubFile import File

class Data:
    subtitles = None
    outputFormat = None
    outputEncoding = None

class DataController(QtCore.QObject):
    _fileAdded = QtCore.pyqtSignal(str, name = "fileAdded")
    _fileRemoved = QtCore.pyqtSignal(str, name = "fileRemoved")
    _fileChanged = QtCore.pyqtSignal(str, name = "fileChanged")

    def __init__(self, parent = None):
        super(DataController, self).__init__(parent)
        self._storage = {
            # filePath: Data
        }

    def _checkFilePath(self, filePath):
        if not isinstance(filePath, str):
            raise TypeError(_("filePath is not a string!"))

    def _checkSubtitles(self, subtitles):
        if type(subtitles) is not SubManager:
            raise TypeError(_("Incorrect subtitles type!"))

    def _checkOutputFormat(self, outputFormat):
        if not issubclass(outputFormat, SubFormat):
            raise TypeError(_("Incorrect outputFormat type!"))

    def _checkOutputEncoding(self, outputEncoding):
        # TODO: proper check
        if not isinstance(outputEncoding, str):
            raise TypeError(_("Incorrect outputEncoding type!"))

    def addFile(self, filePath, subtitles, outputFormat=SubRip, outputEncoding=File.DEFAULT_ENCODING):
        """Add a file with a given filePath, subtitles and an output format and output encoding."""
        self._checkFilePath(filePath)
        self._checkSubtitles(subtitles)
        self._checkOutputFormat(outputFormat)
        self._checkOutputEncoding(outputEncoding)

        if self._storage.get(filePath) is not None:
            raise KeyError(_("Entry for '%s' cannot be added twice") % filePath)

        data = Data()
        data.subtitles = copy.deepcopy(subtitles)
        data.outputEncoding = outputEncoding
        data.outputFormat = outputFormat
        self._storage[filePath] = data
        self._fileAdded.emit(filePath)

    def fileExists(self, filePath):
        """Return whether there is an entry for a given filePath.
        DataController assures that when this function returns True, a proper Data is
        stored for a given filePath."""
        return filePath in self._storage.keys()

    def removeFile(self, filePath):
        """Remove a file with a given filePath"""
        del self._storage[filePath]
        self._fileRemoved.emit(item.text())

    def changeSubtitles(self, filePath, subtitles):
        """Replace stored subtitles with a given ones."""
        self._checkSubtitles(subtitles)
        self._storage[filePath].subtitles = copy.deepcopy(subtitles)
        self._fileChanged.emit(filePath)

    def subtitles(self, filePath):
        data = self._storage[filePath]
        return copy.deepcopy(data.subtitles)

