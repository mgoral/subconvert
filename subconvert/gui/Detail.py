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

from subconvert.utils import SubPath

from PyQt4.QtGui import QListWidget, QTreeWidget, QComboBox, QAction, QIcon, QMessageBox
from PyQt4.QtCore import Qt, pyqtSignal

# define globally to avoid mistakes
AUTO_ENCODING_STR = _("[Auto]")
FPS_VALUES = [23.976, 24.0, 25.0, 29.97, 30.0]

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

class CannotOpenFilesMsg(QMessageBox):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setIcon(self.Warning)

        self._fileListWidget = QListWidget(self)
        self.layout().addWidget(self._fileListWidget, 3, 1)
        self._fileListWidget.hide()

    def setFileList(self, fileList):
        self._fileListWidget.clear()
        self._fileListWidget.addItems(fileList)
        if self._fileListWidget.count() > 0:
            self._fileListWidget.show()
        else:
            self._fileListWidget.hide()

    def exec(self):
        fileListSize = self._fileListWidget.count()
        if fileListSize > 1:
            self.setText(_("Errors occured when trying to open following files:"))
        else:
            self.setText(_("An error occured when trying to open a file:"))
        super().exec()
