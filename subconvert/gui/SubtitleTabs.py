"""
Copyright (C) 2013 Michal Goral.

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
import gettext
import logging
import pkgutil
import encodings
from copy import deepcopy

from PyQt4.QtGui import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QIcon, QListWidgetItem
from PyQt4.QtGui import QTableView, QHeaderView,QStandardItemModel, QStandardItem, QSizePolicy
from PyQt4.QtGui import QMessageBox, QUndoStack
from PyQt4.QtCore import pyqtSignal, pyqtSlot, Qt

from subconvert.parsing.FrameTime import FrameTime
from subconvert.utils import SubPath
from subconvert.utils.SubFile import File
from subconvert.gui.Detail import ClickableListWidget, ComboBoxWithHistory
from subconvert.gui.DataModel import SubtitleData
from subconvert.gui.SubtitleEditorCommands import *

log = logging.getLogger('subconvert.%s' % __name__)

t = gettext.translation(
    domain='subconvert',
    localedir=SubPath.getLocalePath(__file__),
    fallback=True)
gettext.install('subconvert')
_ = t.gettext

# define globally to avoid mistakes
AUTO_ENCODING_STR = _("[Auto]")

def pythonEncodings():
    # http://stackoverflow.com/questions/1707709/list-all-the-modules-that-are-part-of-a-python-package/1707786#1707786
    false_positives = set(["aliases"])
    found = set(name for imp, name, ispkg in pkgutil.iter_modules(encodings.__path__) if not ispkg)
    found.difference_update(false_positives)
    found = list(found)
    found.sort()
    return found

class SubTab(QWidget):
    def __init__(self, displayName, isStaticTab, parent = None):
        super(SubTab, self).__init__(parent)
        self._displayName = displayName
        self._isStaticTab = isStaticTab

    @property
    def isStatic(self):
        return self._isStaticTab

    @property
    def name(self):
        return self._displayName

class FileList(SubTab):
    requestOpen = pyqtSignal(str, bool)

    def __init__(self, name, subtitleData, parent = None):
        super(FileList, self).__init__(name, True, parent)
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        self.__fileList = ClickableListWidget()
        mainLayout.addWidget(self.__fileList)

        self.__fileList.mouseButtonDoubleClicked.connect(self.handleDoubleClick)
        self.__fileList.mouseButtonClicked.connect(self.handleClick)
        self._subtitleData = subtitleData

        self.setLayout(mainLayout)

    def addFile(self, filePath):
        if not self._subtitleData.fileExists(filePath):
            data = self._subtitleData.createDataFromFile(filePath)
            icon = QIcon(":/img/initial_list.png")
            item = QListWidgetItem(icon, filePath)
            item.setToolTip(filePath)

            self._subtitleData.add(filePath, data)
            self.__fileList.addItem(item)

    def removeFile(self):
        item = self.__fileList.takeItem(self.__fileList.currentRow())
        item = None

    def getCurrentFile(self):
        return self.__fileList.currentItem()

    def handleClick(self, button):
        item = self.__fileList.currentItem()
        if item is not None and button == Qt.MiddleButton:
            self.requestOpen.emit(item.text(), True)

    def handleDoubleClick(self, button):
        item = self.__fileList.currentItem()
        if item is not None and button == Qt.LeftButton:
            self.requestOpen.emit(item.text(), False)

class SubtitleEditor(SubTab):
    def __init__(self, filePath, subtitleData, parent = None):
        name = os.path.split(filePath)[1]
        super(SubtitleEditor, self).__init__(name, False, parent)
        self.__initWidgets()

        self._filePath = filePath
        self._subtitleData = subtitleData
        self._undoStack = QUndoStack(self)

        self.updateSubtitles()

        # Some signals
        self._subtitleData.fileChanged.connect(self.fileChanged)
        self._inputEncodings.currentIndexChanged.connect(self._changeEncodingFromIndex)
        self._model.itemChanged.connect(self._subtitleChanged)

    def __initWidgets(self):
        minimalSizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Encodings combo box
        # TODO: show only encodings selected by user in preferences
        self._inputEncodings = ComboBoxWithHistory(self)
        self._inputEncodings.addItem(AUTO_ENCODING_STR)
        self._inputEncodings.addItems(pythonEncodings())
        self._inputEncodings.setToolTip(_("Change input file encoding"))
        self._inputEncodings.setEditable(True)

        # List of subtitles
        self._model = QStandardItemModel(0, 3, self)
        self._model.setHorizontalHeaderLabels([_("Begin"), _("End"), _("Subtitle")])
        self._subList = QTableView(self)
        self._subList.setModel(self._model)
        self._subList.horizontalHeader().setResizeMode(2, QHeaderView.Stretch)

        # Top toolbar
        toolbar = QHBoxLayout()
        toolbar.setAlignment(Qt.AlignLeft)
        toolbar.addWidget(self._inputEncodings)
        toolbar.addStretch(1)

        # Main layout
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.addLayout(toolbar, 0, 0, 1, 1) # stretch to the right
        grid.addWidget(self._subList, 1, 0)
        self.setLayout(grid)

    def _createRow(self, sub):
        timeStart = QStandardItem(sub.start.toStr())
        timeEnd = QStandardItem(sub.end.toStr())
        text = QStandardItem(sub.text)
        return [timeStart, timeEnd, text]

    def _subtitleChanged(self, item):
        modelIndex = item.index()
        column = modelIndex.column()
        subNo = modelIndex.row()

        # TODO: timeStart and timeEnd might be displayed in a frame format in a bright future.
        # Check it and create FrameTime properly in that case.
        # TODO: Maybe add column numbers to some kind of enum to avoid magic numbers?
        try:
            subtitle = self._data.subtitles[subNo]
            if 0 == column:
                timeStart = FrameTime(time=item.text(), fps = self._data.subtitles.fps)
                subtitle.change(start = timeStart)
            elif 1 == column:
                timeEnd = FrameTime(time=item.text(), fps = self._data.subtitles.fps)
                subtitle.change(end = timeEnd)
            elif 2 == column:
                subtitle.change(text = item.text())
        except Exception as msg:
            # TODO: highlight incorrect column or field with a color on any error
            log.error(msg)

        command = ChangeSubtitle(self, subtitle, subNo)
        self._undoStack.push(command)

    @pyqtSlot(int)
    def _changeEncodingFromIndex(self, index):
        encoding = self._inputEncodings.itemText(index)
        self.changeEncoding(encoding)

    def changeEncoding(self, encoding):
        if encoding == AUTO_ENCODING_STR:
            file_ = File(self._filePath)
            encoding = file_.detectEncoding()

        # Operate on a copy so we can fallback to the old subtitles in case wrong encoding has been
        # chosen
        subtitlesCopy = deepcopy(self._data.subtitles)
        try:
            for i, subtitle in enumerate(subtitlesCopy):
                encodedBits = subtitle.text.encode(self._data.inputEncoding)
                subtitlesCopy.changeSubText(i, encodedBits.decode(encoding))
        except UnicodeDecodeError:
            message = QMessageBox(
                QMessageBox.Warning,
                _("Decoding error"),
                _("Cannot decode subtitles to '%s' encoding.\nPlease try different encoding.") % encoding,
                QMessageBox.Ok, self
            )
            message.exec()
        except LookupError:
            message = QMessageBox(
                QMessageBox.Warning, _("Unknown encoding"), _("Unknown encoding: '%s'") % encoding,
                QMessageBox.Ok, self
            )
            message.exec()
            # TODO: turn of signal handling for a sec. and set previous encoding
            addedIncorrectEncodingIndex = self._inputEncodings.findText(encoding)
            self._inputEncodings.removeItem(addedIncorrectEncodingIndex)
        else:
            # TODO: outputEncoding
            command = ChangeEncoding(self, encoding, encoding, subtitlesCopy)
            self._undoStack.push(command)

    def fileChanged(self, filePath):
        if filePath == self._filePath:
            self.updateSubtitles()

    def refreshSubtitle(self, subNo):
        sub = self._data.subtitles[subNo]
        self._model.removeRow(subNo)
        self._model.insertRow(subNo, self._createRow(sub))

    def refreshSubtitles(self):
        self._model.removeRows(0, self._model.rowCount())
        for sub in self._data.subtitles:
            self._model.appendRow(self._createRow(sub))

    def updateSubtitles(self):
        # TODO: Should it save current subtitles so that user can undo or should it inform via
        # a messagebox that this change cannot be reverted?
        self._undoStack.clear()
        self._data = self._subtitleData.data(self._filePath)
        self.refreshSubtitles()

    def saveContent(self):
        # TODO: check if subtitleData.fileExists(filePath) ???
        self._subtitleData.fileChanged.disconnect(self.fileChanged)
        self._subtitleData.update(self._filePath, self._data)
        self._subtitleData.fileChanged.connect(self.fileChanged)

    @property
    def filePath(self):
        return self._filePath

    @property
    def subtitles(self):
        return self._data.subtitles

    @property
    def history(self):
        return self._undoStack

    @property
    def inputEncoding(self):
        return self._data.inputEncoding

    @property
    def outputEncoding(self):
        return self._data.outputEncoding
