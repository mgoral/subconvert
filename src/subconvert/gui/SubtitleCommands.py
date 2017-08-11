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

from subconvert.parsing.Core import Subtitle
from subconvert.utils.Locale import _, P_
from subconvert.utils.SubException import SubException, SubAssert

from PyQt5.QtWidgets import QUndoCommand

# TODO/FIXME: Maybe it's a good idea to copy local subtitles saved in commands but as long as during
# empirical tests no errors are detected, we won't do it to save some time and memory.
#
# Example of incorrect behavior:
# 1. Save reference to controller.subtitles inside ChangeEncoding
# 2. Modify a subtitle by Change Subtitle
# This way a reference stored in step 1 is also modified. BUT: as long as we provide only one step
# undo/redo and as long as all modifications are done only by QUndoCommands, changes will be
# reverted to the proper state before ChangeEncoding command will be on top of UndoStack again
# (in our case: after one 'undo').

class IncorrectFilePath(SubException):
    pass

class DoubleFileEntry(SubException):
    pass

def subExcerpt(sub):
    maxChars = 20
    if len(sub.text) > maxChars:
        return "%s..." % sub.text[:maxChars]
    return sub.text

class SubtitleChangeCommand(QUndoCommand):
    """Base class for all Subconvert undo/redo actions."""
    def __init__(self, filePath, parent = None):
        super(SubtitleChangeCommand, self).__init__(parent)
        self._controller = None
        self._filePath = filePath

    def setup(self):
        """When subclassing remember to call SubtitleChangeCommand::setup() to perform generic
        checks."""
        if not isinstance(self.filePath, str):
            raise TypeError("File path is not a string!")
        if self.controller is None:
            raise ValueError("Command controller hasn't been specified!")

    @property
    def filePath(self):
        return self._filePath

    @property
    def controller(self):
        return self._controller

    @controller.setter
    def controller(self, controller):
        self._controller = controller

class ChangeSubtitle(SubtitleChangeCommand):
    def __init__(self, filePath, oldSubtitle, newSubtitle, index, parent = None):
        super(ChangeSubtitle, self).__init__(filePath, parent)
        self.setText(_("Subtitle change (%d: %s)") % (int(index + 1), subExcerpt(newSubtitle)))

        self._oldSubtitle = oldSubtitle
        self._newSubtitle = newSubtitle
        self._subNo = index

    def setup(self):
        super().setup()
        if not self.controller.fileExists(self.filePath):
            raise IncorrectFilePath("No entry to update for %s" % self.filePath)
        if not isinstance(self._subNo, int):
            raise TypeError("Subtitle number is not an int!")
        if type(self._oldSubtitle) is not Subtitle:
            raise TypeError("Old subtitle are not of type 'Subtitle'!")
        if type(self._newSubtitle) is not Subtitle:
            raise TypeError("New subtitle are not of type 'Subtitle'!")

    def redo(self):
        storage = self.controller._storage[self.filePath]
        storage.subtitles.changeSubText(self._subNo, self._newSubtitle.text)
        storage.subtitles.changeSubStart(self._subNo, self._newSubtitle.start)
        storage.subtitles.changeSubEnd(self._subNo, self._newSubtitle.end)
        self.controller.subtitlesChanged.emit(self.filePath, [self._subNo])

    def undo(self):
        storage = self.controller._storage[self.filePath]
        storage.subtitles.changeSubText(self._subNo, self._oldSubtitle.text)
        storage.subtitles.changeSubStart(self._subNo, self._oldSubtitle.start)
        storage.subtitles.changeSubEnd(self._subNo, self._oldSubtitle.end)
        self.controller.subtitlesChanged.emit(self.filePath, [self._subNo])

class ChangeData(SubtitleChangeCommand):
    def __init__(self, filePath, newData, desc = None, parent = None):
        super().__init__(filePath, parent)
        if desc is None:
            self.setText(_("Subtitle data change"))
        else:
            self.setText(desc)

        self._newData = newData.clone()
        self._oldData = None

    def setup(self):
        super().setup()
        if not self.controller.fileExists(self.filePath):
            raise IncorrectFilePath("No entry to update for %s" % self.filePath)

        #  A little hackish way to avoid passing oldData to ChangeData command (which would require
        #  unnecessary deepcopies).
        if self._oldData is None:
            self._oldData = self.controller.data(self.filePath)

        self._newData.verifyAll()

    def redo(self):
        self.controller._storage[self.filePath] = self._newData
        self.controller.fileChanged.emit(self.filePath)

    def undo(self):
        self.controller._storage[self.filePath] = self._oldData
        self.controller.fileChanged.emit(self.filePath)

class NewSubtitles(SubtitleChangeCommand):
    def __init__(self, filePath, encoding = None, parent = None):
        super().__init__(filePath, parent)
        self.setText(_("New file: %s") % os.path.basename(filePath))
        self._filePath = filePath
        self._encoding = encoding

    def setup(self):
        super().setup()
        if self.controller.fileExists(self.filePath):
            raise DoubleFileEntry("'%s' cannot be added twice" % self._filePath)
        self._newData = self.controller.createDataFromFile(self._filePath, self._encoding)

    def redo(self):
        self.controller._storage[self.filePath] = self._newData
        self.controller.fileAdded.emit(self.filePath)

    def undo(self):
        pass

class CreateSubtitlesFromData(SubtitleChangeCommand):
    def __init__(self, filePath, data, parent = None):
        super().__init__(filePath, parent)
        self.setText(_("New file (copy): %s") % os.path.basename(filePath))
        self._newData = data

    def setup(self):
        super().setup()
        if self.controller.fileExists(self.filePath):
            raise DoubleFileEntry("'%s' cannot be added twice" % self._filePath)
        self._newData.verifyAll()

    def redo(self):
        self.controller._storage[self.filePath] = self._newData
        self.controller.fileAdded.emit(self.filePath)

    def undo(self):
        pass

class RemoveFile(SubtitleChangeCommand):
    def __init__(self, filePath, parent = None):
        super().__init__(filePath, parent)
        # Dunno why we set this text...
        self.setText(_("Removal of file: %s") % os.path.basename(filePath))
        self._filePath = filePath

    def setup(self):
        super().setup()
        if not self.controller.fileExists(self.filePath):
            raise IncorrectFilePath("Cannot remove '%s'. It doesn't exist!" % self._filePath)

    def redo(self):
        history = self.controller._history[self._filePath]
        history.deleteLater() # C++ delete on next Qt event loop enter
        del self.controller._history[self._filePath] # Python delete from dict
        del self.controller._storage[self._filePath]
        self.controller.fileRemoved.emit(self._filePath)

    def undo(self):
        pass

class AddSubtitle(SubtitleChangeCommand):
    def __init__(self, filePath, subNo, subtitle, parent = None):
        super().__init__(filePath, parent)
        self._subNo = subNo
        self._subtitle = subtitle
        self.setText(_("New subtitle (%d)") % int(subNo + 1))

    def setup(self):
        super().setup()
        storage = self.controller._storage[self.filePath]
        SubAssert(storage.subtitles.size() == 0 or storage.subtitles.fps == self._subtitle.fps,
            "All subtitles must have equal fps values")

    def redo(self):
        storage = self.controller._storage[self.filePath]
        storage.subtitles.insert(self._subNo, self._subtitle)
        self.controller.subtitlesAdded.emit(self.filePath, [self._subNo])

    def undo(self):
        storage = self.controller._storage[self.filePath]
        storage.subtitles.remove(self._subNo)
        self.controller.subtitlesRemoved.emit(self.filePath, [self._subNo])

class RemoveSubtitles(SubtitleChangeCommand):
    def __init__(self, filePath, subNos, parent = None):
        super().__init__(filePath, parent)

        # we'll remove from the highest subtitle to keep things simple
        self._subNos = subNos
        self._subNos.sort(reverse = True)

    def setup(self):
        super().setup()
        storage = self.controller._storage[self.filePath]

        if len(self._subNos) == 0:
            # Just for the peace of soul
            self.setText(_("Subtitle removal"))
            return

        self.setText(P_(
            "Subtitle removal (%(sub)s)",
            "%(noOfSubs)d subtitles removal (%(sub)s)",
            len(self._subNos)) % { 
                "sub" : subExcerpt(storage.subtitles[self._subNos[-1]]),
                "noOfSubs" : len(self._subNos) 
            })

        self._subs = []
        for subNo in self._subNos:
            self._subs.append((subNo, storage.subtitles[subNo]))

    def redo(self):
        storage = self.controller._storage[self.filePath]
        for sub in self._subs:
            storage.subtitles.remove(sub[0])
        self.controller.subtitlesRemoved.emit(self.filePath, self._subNos)

    def undo(self):
        storage = self.controller._storage[self.filePath]
        for sub in reversed(self._subs):
            storage.subtitles.insert(sub[0], sub[1])
        self.controller.subtitlesAdded.emit(self.filePath,
                                            list(reversed(self._subNos)))
