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

from subconvert.utils.Locale import _, P_

from PyQt5.QtWidgets import QListWidget, QTreeWidget, QComboBox, QAction, QMessageBox
from PyQt5.QtWidgets import QStyledItemDelegate, QLineEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal

# define globally to avoid mistakes
AUTO_ENCODING_STR = _("[Auto]")
FPS_VALUES = [23.976, 24.0, 25.0, 29.97, 30.0]

class DisableSignalling:
    """
    Usage example:
    with DisableSignalling(cls.signal, self.slot):
        # do something
        pass
    """
    def __init__(self, signal, slot):
        self._signal = signal
        self._slot = slot

    def __enter__(self):
        self._signal.disconnect(self._slot)

    def __exit__(self, type, value, traceback):
        self._signal.connect(self._slot)

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

class SearchEdit(QLineEdit):
    escapePressed = pyqtSignal()
    def __init__(self, parent = None):
        super().__init__(parent)

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape:
            self.escapePressed.emit()
        super().keyPressEvent(ev)
