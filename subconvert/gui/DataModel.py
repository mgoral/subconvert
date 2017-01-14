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

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QUndoStack

from subconvert.utils.Locale import _
from subconvert.utils.SubFile import File, VideoInfo
from subconvert.utils.SubtitleData import SubtitleData
from subconvert.utils.SubException import SubException

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
    _subtitlesChanged = pyqtSignal(str, list, name = "subtitlesChanged")
    _subtitlesAdded = pyqtSignal(str, list, name = "subtitlesAdded")
    _subtitlesRemoved = pyqtSignal(str, list, name = "subtitlesRemoved")

    def __init__(self, parser, parent = None):
        super(DataController, self).__init__(parent)
        self._storage = {
            # filePath: SubtitleData
        }
        self._history = {
            # filePath: SubtitleUndoStack
        }

        self._parser = parser

    def _parseFile(self, file_, inputEncoding, fps):
        fileContent = file_.read(inputEncoding)
        return self._parser.parse(fileContent, fps)

    def createDataFromFile(self, filePath, inputEncoding = None, defaultFps = None):
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

        videoInfo = VideoInfo(defaultFps) if defaultFps is not None else file_.detectFps()

        subtitles = self._parseFile(file_, inputEncoding, videoInfo.fps)

        data = SubtitleData()
        data.subtitles = subtitles
        data.fps = videoInfo.fps
        data.inputEncoding = inputEncoding
        data.outputEncoding = inputEncoding
        data.outputFormat = self._parser.parsedFormat()
        data.videoPath = videoInfo.videoPath
        return data

    def execute(self, cmd):
        """Execute a command to modify storage[cmd.filePath]"""
        if not cmd.filePath in self._history.keys():
            self._history[cmd.filePath] = SubtitleUndoStack(self)
            try:
                self._history[cmd.filePath].push(cmd)
            except:
                self._history[cmd.filePath].deleteLater()
                del self._history[cmd.filePath]
                raise
            else:
                self._history[cmd.filePath].clear()
        else:
            self._history[cmd.filePath].push(cmd)

    def count(self):
        return len(self._storage)

    def fileExists(self, filePath):
        """Return whether there is an entry for a given filePath.
        DataController assures that when this function returns True, a proper Data is
        stored for a given filePath."""
        return filePath in self._storage.keys()

    def data(self, filePath):
        data = self._storage[filePath]
        return data.clone()

    def setCleanState(self, filePath):
        self._history[filePath].setClean()

    def isCleanState(self, filePath):
        return self._history[filePath].isClean()

    def subtitles(self, filePath):
        data = self._storage[filePath]
        return data.subtitles.clone()

    def history(self, filePath):
        #Don't worry about pushing commands by history.push(cmd). It should work.
        return self._history[filePath]

    @property
    def supportedFormats(self):
        return self._parser.formats
