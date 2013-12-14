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

import re

from subconvert.parsing.FrameTime import FrameTime
from subconvert.utils.Locale import _, P_

from PyQt4.QtGui import QListWidget, QTreeWidget, QComboBox, QAction, QIcon, QMessageBox
from PyQt4.QtGui import QAbstractSpinBox, QStyledItemDelegate, QValidator, QBrush
from PyQt4.QtCore import Qt, pyqtSignal

# define globally to avoid mistakes
AUTO_ENCODING_STR = _("[Auto]")
FPS_VALUES = [23.976, 24.0, 25.0, 29.97, 30.0]

class CustomDataRoles:
    FrameTimeRole = Qt.UserRole + 1
    ErrorFlagRole = Qt.UserRole + 2

class ActionFactory:
    def __init__(self, parent):
        self._parent = parent

    def create(self, icon=None, title=None, tip=None, shortcut=None, connection=None):
        action = QAction(self._parent)

        if icon is not None:
            try:
                action.setIcon(QIcon.fromTheme(icon))
            except TypeError:
                action.setIcon(icon)
        if title is not None:
            action.setText(title)
        if tip is not None:
            action.setToolTip(tip)
        if shortcut is not None:
            action.setShortcut(shortcut)
        if connection is not None:
            action.triggered.connect(connection)

        return action

class FrameTimeValidator(QValidator):
    def validate(self, input_, pos):
        result = re.search(r"[^0-9.:]", input_)
        if result is not None:
            return (QValidator.Invalid, input_, pos)

        spl = input_.split(":")
        if len(spl) == 3:
            miliSpl = spl[2].split(".")

            if len(spl[0]) == 0 or len(spl[1]) < 2:
                return (QValidator.Intermediate, input_, pos)

            if len(miliSpl) == 2:
                if len(miliSpl[0]) < 2 or len(miliSpl[1]) < 3:
                    return (QValidator.Intermediate, input_, pos)
                elif len(miliSpl[1]) > 3:
                    return (QValidator.Invalid, input_, pos)

                try:
                    ft = FrameTime(1, time=input_)
                    return (QValidator.Acceptable, input_, pos)
                except:
                    return (QValidator.Invalid, input_, pos)
        return (QValidator.Intermediate, input_, pos)

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

        absSteps = abs(steps) # due to FrameTime limitations
        if steps < 0:
            self._frameTime = self._frameTime - timeStep * absSteps
        else:
            self._frameTime = self._frameTime + timeStep * absSteps

        self.lineEdit().setText(self._frameTime.toStr())
        self.lineEdit().setCursorPosition(pos)

    def stepEnabled(self):
        if self._frameTime.fullSeconds > 0:
            return (QAbstractSpinBox.StepUpEnabled | QAbstractSpinBox.StepDownEnabled)
        return QAbstractSpinBox.StepUpEnabled

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
            validator = FrameTimeValidator(self)
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

class SubListItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return FrameTimeSpinBox(parent)

    def setEditorData(self, editor, index):
        frameTime = index.model().data(index, CustomDataRoles.FrameTimeRole)
        editor.setFrameTime(frameTime)

    def setModelData(self, editor, model, index):
        frameTime = editor.frameTime()
        modelFrameTime = index.model().data(index, CustomDataRoles.FrameTimeRole)

        if editor.incorrectInput() is True:
            model.setData(index, True, CustomDataRoles.ErrorFlagRole)
        elif frameTime is not None and frameTime != modelFrameTime:
            data = {
                Qt.EditRole: editor.text(),
                CustomDataRoles.FrameTimeRole: frameTime,
                CustomDataRoles.ErrorFlagRole: False,
            }
            model.setItemData(index, data)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class SubtitleList(QTreeWidget):
    """QListWidget wrapper that sends additional signals with clicked mouse button identifier"""

    mouseButtonDoubleClicked = pyqtSignal(int)
    mouseButtonClicked = pyqtSignal(int)
    keyPressed = pyqtSignal(int)

    def __init__(self, parent = None):
        super(SubtitleList, self).__init__(parent)

    def mousePressEvent(self, mouseEvent):
        super(SubtitleList, self).mousePressEvent(mouseEvent)
        self.mouseButtonClicked.emit(mouseEvent.button())

    def mouseDoubleClickEvent(self, mouseEvent):
        super(SubtitleList, self).mouseDoubleClickEvent(mouseEvent)
        self.mouseButtonDoubleClicked.emit(mouseEvent.button())

    def keyPressEvent(self, keyEvent):
        super(SubtitleList, self).keyPressEvent(keyEvent)
        self.keyPressed.emit(keyEvent.key())

class ComboBoxWithHistory(QComboBox):
    def __init__(self, parent = None):
        super(ComboBoxWithHistory, self).__init__(parent)
        self._previousText = None

    def previousText(self):
        if self._previousText:
            return self._previousText
        return self.currentText()

    def setCurrentIndex(self, index):
        previousTextCopy = self.currentText()
        try:
            self._previousText = self.currentText()
            super().setCurrentIndex(index)
        except:
            self._previousText = previousTextCopy

    def mousePressEvent(self, mouseEvent):
        self._previousText = self.currentText()
        super(ComboBoxWithHistory, self).mousePressEvent(mouseEvent)

    def keyPressEvent(self, keyEvent):
        key = keyEvent.key()
        if key in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
            self._previousText = self.currentText()
        super(ComboBoxWithHistory, self).keyPressEvent(keyEvent)

class MessageBoxWithList(QMessageBox):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._listWidget = QListWidget(self)
        self.layout().addWidget(self._listWidget, 3, 1)
        self._listWidget.hide()

    def addToList(self, val):
        self._listWidget.addItem(val)

    def listCount(self):
        return self._listWidget.count()

    def exec(self):
        if self._listWidget.count() > 0:
            self._listWidget.show()
        else:
            self._listWidget.hide()
        super().exec()

class CannotOpenFilesMsg(MessageBoxWithList):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setIcon(self.Warning)

    def setFileList(self, fileList):
        self._listWidget.clear()
        for val in fileList:
            self.addToList(val)

    def exec(self):
        fileListSize = self._listWidget.count()
        self.setText(P_(
            "An error occured when trying to open a file:",
            "Errors occured when trying to open following files:",
            fileListSize))
        super().exec()
