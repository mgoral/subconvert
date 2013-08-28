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

class SubtitleData:
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

    def _addData(self, filePath, data):
        """An actual function that checks and adds data given for add/update operation"""
        if type(data) is not SubtitleData:
            raise TypeError(_("Incorrect data type!"))

        self._checkFilePath(filePath)
        self._checkSubtitles(data.subtitles)
        self._checkOutputFormat(data.outputFormat)
        self._checkOutputEncoding(data.outputEncoding)

        insertData = copy.deepcopy(data)
        self._storage[filePath] = insertData

    def add(self, filePath, data):
        """Add a file with a given filePath, subtitles and an output format and output encoding."""
        if filePath in self._storage:
            raise KeyError(_("Entry for '%s' cannot be added twice") % filePath)
        self._addData(filePath, data)
        self._fileAdded.emit(filePath)

    def update(self, filePath, data):
        """Update an already existing entry."""
        if filePath not in self._storage:
            raise KeyError(_("No entry to update for %s") % filePath)
        self._addData(filePath, data)
        self._fileChanged.emit(filePath)

    def remove(self, filePath):
        """Remove a file with a given filePath"""
        del self._storage[filePath]
        self._fileRemoved.emit(item.text())

    def count(self):
        return len(self._storage)

    def fileExists(self, filePath):
        """Return whether there is an entry for a given filePath.
        DataController assures that when this function returns True, a proper Data is
        stored for a given filePath."""
        return filePath in self._storage.keys()

    def data(self, filePath):
        data = self._storage[filePath]
        return copy.deepcopy(data)

    def subtitles(self, filePath):
        data = self._storage[filePath]
        return copy.deepcopy(data.subtitles)

