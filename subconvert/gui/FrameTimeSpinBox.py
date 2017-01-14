"""
Copyright (C) 2011-2017 Michał Góral.

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

from subconvert.parsing.FrameTime import FrameTime

from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import QAbstractSpinBox
from PyQt5.QtCore import Qt


class FrameTimeSpinBox(QAbstractSpinBox):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._frameTime = None
        self._incorrectInput = False
        self.setAccelerated(True)

        # empty CustomContextMenu also blocks parent context menu from spawning
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def setFrameTime(self, frameTime):
        self._frameTime = frameTime

        fps = frameTime.fps
        self._miliStep = FrameTime(fps, time = "0:00:00.001")
        self._secondStep = FrameTime(fps, time = "0:00:01.000")
        self._minuteStep = FrameTime(fps, time = "0:01:00.000")
        self._hourStep = FrameTime(fps, time = "1:00:00.000")

        self.lineEdit().setText(self._frameTime.toStr())

    def stepBy(self, steps):
        pos = self.lineEdit().cursorPosition()
        timeStep = self._determineStep(pos)

        self._frameTime = self._frameTime + timeStep * steps

        self.lineEdit().setText(self._frameTime.toStr())
        self.lineEdit().setCursorPosition(pos)

    def stepEnabled(self):
        return (QAbstractSpinBox.StepUpEnabled | QAbstractSpinBox.StepDownEnabled)

    def frameTime(self):
        self._validateLineEdit()
        return self._frameTime

    def text(self):
        # frameTime() will first check if there are any text changes in QLineEdit
        return self.frameTime().toStr()

    def incorrectInput(self):
        return self._incorrectInput

    def _validateLineEdit(self):
        text = self.lineEdit().text()
        if text != self._frameTime.toStr():
            validator = _FrameTimeValidator(self)
            isValid = validator.validate(text, 0)[0]
            if isValid == QValidator.Acceptable:
                self._incorrectInput = False
                fps = self._frameTime.fps
                self._frameTime = FrameTime(fps, time = text)
            else:
                self._incorrectInput = True

    def _determineStep(self, position):
        textLen = len(self.lineEdit().text())

        if position in (textLen, textLen - 1, textLen - 2, textLen - 3):
            return self._miliStep
        elif position in (textLen - 4, textLen - 5, textLen - 6):
            return self._secondStep
        elif position in (textLen - 7, textLen - 8, textLen - 9):
            return self._minuteStep
        return self._hourStep


class _FrameTimeValidator(QValidator):
    def validate(self, input_, pos):
        try:
            ft = FrameTime(1, time=input_)
            return (QValidator.Acceptable, input_, pos)
        except:
            return (QValidator.Invalid, input_, pos)
