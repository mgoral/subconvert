#-*- coding: utf-8 -*-

"""
    Copyright (C) 2013 Michal Goral

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

from PyQt4.QtGui import QUndoCommand

# TODO/FIXME: Maybe it's a good idea to copy local subtitles saved in commands but as long as during
# empirical tests no errors are detected, we won't do it to save some time and memory.
#
# Example of incorrect behavior:
# 1. Save reverence to editor.subtitles inside ChangeEncoding
# 2. Modify a subtitle by Change Subtitle
# This way a reference stored in step 1 is also modified. BUT: as long as we provide only one step
# undo/redo and as long as all modifications are done only by QUndoCommands, changes will be
# reverted to the proper state before ChangeEncoding command will be on top of UndoStack again 
# (in our case: after one 'undo').

class SubtitleChangeCommand(QUndoCommand):
    """Base class for all Subconvert undo/redo actions."""
    def __init__(self, editor, text, parent = None):
        super(SubtitleChangeCommand, self).__init__(parent)
        self.setText(text)
        self._editor = editor

    @property
    def editor(self):
        return self._editor

class ChangeSubtitle(SubtitleChangeCommand):
    def __init__(self, editor, subtitle, index, parent = None):
        super(ChangeSubtitle, self).__init__(editor, _("Subtitle change"), parent)

        self._newSubtitle = subtitle
        self._subNo = index
        self._oldSubtitle = editor.subtitles[index]

    def redo(self):
        self.editor.subtitles.changeSubText(self._subNo, self._newSubtitle.text)
        self.editor.subtitles.changeSubStart(self._subNo, self._newSubtitle.start)
        self.editor.subtitles.changeSubEnd(self._subNo, self._newSubtitle.end)
        self.editor.refreshSubtitle(self._subNo)

    def undo(self):
        self.editor.subtitles.changeSubText(self._subNo, self._oldSubtitle.text)
        self.editor.subtitles.changeSubStart(self._subNo, self._oldSubtitle.start)
        self.editor.subtitles.changeSubEnd(self._subNo, self._oldSubtitle.end)
        self.editor.refreshSubtitle(self._subNo)

class ChangeEncoding(SubtitleChangeCommand):
    def __init__(self, editor, inputEncoding, outputEncoding, subtitles, parent = None):
        super(ChangeEncoding, self).__init__(editor, _("Encoding change"), parent)

        self._newInputEnc = inputEncoding
        self._newOutputEnc = outputEncoding
        self._newSubtitles = subtitles
        self._newInputBoxText = editor._inputEncodings.currentText()

        self._oldInputEnc = editor.inputEncoding
        self._oldOutputEnc = editor.outputEncoding
        self._oldSubtitles = editor.subtitles
        self._oldInputBoxText = editor._inputEncodings.previousText()

    def _updateComboBox(self, text):
        # TODO: outputEncoding when it's available
        self.editor._inputEncodings.blockSignals(True)
        index = self.editor._inputEncodings.findText(text)
        self.editor._inputEncodings.setCurrentIndex(index)
        self.editor._inputEncodings.blockSignals(False)

    def redo(self):
        self.editor._data.inputEncoding = self._newInputEnc
        self.editor._data.outputEncoding = self._newOutputEnc
        self.editor._data.subtitles = self._newSubtitles
        self._updateComboBox(self._newInputBoxText)
        self.editor.refreshSubtitles()

    def undo(self):
        self.editor._data.inputEncoding = self._oldInputEnc
        self.editor._data.outputEncoding = self._oldOutputEnc
        self.editor._data.subtitles = self._oldSubtitles
        self._updateComboBox(self._oldInputBoxText)
        self.editor.refreshSubtitles()

