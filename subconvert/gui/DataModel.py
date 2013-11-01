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

from copy import deepcopy
from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt4.QtGui import QUndoStack

from subconvert.parsing.Core import SubManager, SubParser, SubConverter, SubManager
from subconvert.parsing.Formats import *
from subconvert.gui.SubtitleEditorCommands import *
from subconvert.utils.SubFile import File
from subconvert.utils.Encodings import ALL_ENCODINGS

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

    def verifySubtitles(self):
        if self.subtitles is None:
            raise TypeError("Subtitles cannot be of type 'NoneType'!")
        if type(self.subtitles) is not SubManager:
            raise TypeError(_("Subtitles are not of type 'SubManager'!"))

    def verifyFps(self):
        if not isinstance(self.fps, float):
            raise TypeError("FPS value is not a float!")

    def verifyOutputFormat(self):
        if self.outputFormat is None:
            raise TypeError("Output format cannot be of type 'NoneType'!")
        if not issubclass(self.outputFormat, SubFormat):
            raise TypeError("Output format is not of type 'SubFormat'!")

    def verifyInputEncoding(self):
        if self.inputEncoding is None:
            raise TypeError("Input encoding cannot be of type 'NoneType'!")
        if not isinstance(self.inputEncoding, str):
            raise TypeError("Input encoding is not a string!")
        if self.inputEncoding not in ALL_ENCODINGS:
            raise ValueError("Input encoding is not a supported encoding!")

    def verifyOutputEncoding(self):
        if self.outputEncoding is None:
            raise TypeError("Output encoding cannot be of type 'NoneType'!")
        if not isinstance(self.outputEncoding, str):
            raise TypeError("Output encoding is not a string!")
        if self.outputEncoding not in ALL_ENCODINGS:
            raise ValueError("Output encoding is not a supported encoding!")

    def verifyAll(self):
        self.verifySubtitles()
        self.verifyFps()
        self.verifyOutputFormat()
        self.verifyInputEncoding()
        self.verifyOutputEncoding()

class SubtitleUndoStack(QUndoStack):
    def __init__(self, parent = None):
        super().__init__(parent)

    def push(self, cmd):
        cmd.controller = self.parent()
        cmd.setup()
        super().push(cmd)

class DataController(QObject):
    _fileAdded = pyqtSignal(str, name = "fileAdded")
    _fileRemoved = pyqtSignal(str, name = "fileRemoved")
    _fileChanged = pyqtSignal(str, name = "fileChanged")

    def __init__(self, parent = None):
        super(DataController, self).__init__(parent)
        self._storage = {
            # filePath: SubtitleData
        }
        self._history = {
            # filePath: SubtitleUndoStack
        }

        self._parser = SubParser()
        for Format in SubFormat.__subclasses__():
            self._parser.registerFormat(Format)

    def _parseFile(self, file_, inputEncoding):
        fileContent = file_.read(inputEncoding)
        return self._parser.parse(fileContent)

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

    def execute(self, cmd):
        """Execute a command to modify storage[cmd.filePath]"""
        if not cmd.filePath in self._history.keys():
            self._history[cmd.filePath] = SubtitleUndoStack(self)
            self._history[cmd.filePath].push(cmd)
            self._history[cmd.filePath].clear()
        else:
            self._history[cmd.filePath].push(cmd)


    def remove(self, filePath):
        """Remove a file with a given filePath"""
        del self._storage[filePath]
        del self._history[filePath]
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
        return deepcopy(data)

    def subtitles(self, filePath):
        data = self._storage[filePath]
        return deepcopy(data.subtitles)

    def encodedData(self, filePath, encoding):
        """Returns a data from filePath with changed inputEncoding. This method does not change
        internal DataController data storage."""
        dataCopy = self.data(filePath)
        encoding = encoding.lower()
        for i, subtitle in enumerate(dataCopy.subtitles):
            encodedBits = subtitle.text.encode(dataCopy.inputEncoding)
            dataCopy.subtitles.changeSubText(i, encodedBits.decode(encoding))
        dataCopy.inputEncoding = encoding
        return dataCopy

    def history(self, filePath):
        #Don't worry about pushing commands by history.push(cmd). It should work.
        return self._history[filePath]

