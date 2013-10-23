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
from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot

from subconvert.parsing.Core import SubManager, SubParser, SubConverter, SubManager
from subconvert.parsing.Formats import *
from subconvert.utils.SubFile import File

class SubtitleData:
    subtitles = None
    fps = None
    outputFormat = None
    inputEncoding = None
    outputEncoding = None

    def empty(self):
        return (
            self.subtitles is None and
            self.fps is None and
            self.outputFormat is None and
            self.inputEncoding is None and
            self.outputEncoding is None
        )

class DataController(QObject):
    _fileAdded = pyqtSignal(str, name = "fileAdded")
    _fileRemoved = pyqtSignal(str, name = "fileRemoved")
    _fileChanged = pyqtSignal(str, name = "fileChanged")

    def __init__(self, parent = None):
        super(DataController, self).__init__(parent)
        self._storage = {
            # filePath: Data
        }
        self._parser = SubParser()
        for Format in SubFormat.__subclasses__():
            self._parser.registerFormat(Format)

    def _checkFilePath(self, filePath):
        if not isinstance(filePath, str):
            raise TypeError(_("filePath is not a string!"))

    def _addSubtitles(self, filePath, subtitles):
        if subtitles is not None:
            if type(subtitles) is not SubManager:
                raise TypeError(_("Incorrect subtitles type!"))
            self._storage[filePath].subtitles = copy.deepcopy(subtitles)

    def _addFps(self, filePath, fps):
        self._storage[filePath].fps = float(fps)

    def _addOutputFormat(self, filePath, outputFormat):
        if outputFormat is not None:
            if not issubclass(outputFormat, SubFormat):
                raise TypeError(_("Incorrect outputFormat type!"))
            self._storage[filePath].outputFormat = copy.deepcopy(outputFormat)

    def _addInputEncoding(self, filePath, inputEncoding):
        if inputEncoding is not None:
            # TODO: proper check
            if not isinstance(inputEncoding, str):
                raise TypeError(_("Incorrect inputEncoding type!"))
            self._storage[filePath].inputEncoding = inputEncoding.lower()

    def _addOutputEncoding(self, filePath, outputEncoding):
        if outputEncoding is not None:
            # TODO: proper check
            if not isinstance(outputEncoding, str):
                raise TypeError(_("Incorrect outputEncoding type!"))
            self._storage[filePath].outputEncoding = outputEncoding.lower()

    def _addData(self, filePath, data):
        """An actual function that checks and adds data given for add/update operation"""
        if type(data) is not SubtitleData:
            raise TypeError(_("Incorrect data type!"))

        self._checkFilePath(filePath)

        if self._storage.get(filePath) is None:
            self._storage[filePath] = SubtitleData()

        self._addSubtitles(filePath, data.subtitles)
        self._addFps(filePath, data.fps)
        self._addOutputFormat(filePath, data.outputFormat)
        self._addInputEncoding(filePath, data.inputEncoding)
        self._addOutputEncoding(filePath, data.outputEncoding)

    def _parseFile(self, file_, inputEncoding):
        fileContent = file_.read(inputEncoding)
        return self._parser.parse(fileContent)

    def add(self, filePath, data):
        """Add a file with a given filePath, subtitles and an output format and output encoding."""
        if filePath in self._storage:
            raise KeyError(_("Entry for '%s' cannot be added twice") % filePath)
        if not data.empty():
            self._addData(filePath, data)
            self._fileAdded.emit(filePath)

    def createDataFromFile(self, filePath, inputEncoding = None, fps = 25.0):
        """Fetch a given filePath and parse its contents.

        May raise the following exceptions:
        * RuntimeError - generic exception telling that parsing was unsuccessfull
        * IOError - failed to open a file at given filePath

        @return SubtitleData filled with non-empty, default datafields. Client should modify them
                and then perform an add/update operation"""

        file_ = File(filePath)
        if inputEncoding is None:
            inputEncoding = file_.detectEncoding()
        inputEncoding = inputEncoding.lower()

        subtitles = self._parseFile(file_, inputEncoding)
        if self._parser.isParsed:
            data = SubtitleData()
            data.subtitles = subtitles
            data.fps = fps
            data.inputEncoding = inputEncoding
            data.outputEncoding = inputEncoding
            data.outputFormat = self._parser.parsedFormat()
            return data
        else:
            raise RuntimeError(_("Unable to parse file '%s'.") % filePath)

    def update(self, filePath, data):
        """Update an already existing entry."""
        if filePath not in self._storage:
            raise KeyError(_("No entry to update for %s") % filePath)
        if not data.empty():
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

    def changeDataEncoding(self, data, encoding):
        dataCopy = copy.deepcopy(data)
        encoding = encoding.lower()
        for i, subtitle in enumerate(dataCopy.subtitles):
            encodedBits = subtitle.text.encode(dataCopy.inputEncoding)
            dataCopy.subtitles.changeSubText(i, encodedBits.decode(encoding))
        dataCopy.inputEncoding = encoding
        return dataCopy


