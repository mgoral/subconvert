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
import logging
import pkgutil
import encodings
from copy import deepcopy

from PyQt4.QtGui import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QIcon, QListWidgetItem
from PyQt4.QtGui import QTableView, QHeaderView,QStandardItemModel, QStandardItem, QSizePolicy
from PyQt4.QtGui import QMessageBox, QAbstractItemView, QAction, QMenu, QCursor
from PyQt4.QtGui import QFileDialog
from PyQt4.QtCore import pyqtSignal, pyqtSlot, Qt

from subconvert.parsing.FrameTime import FrameTime
from subconvert.utils.Locale import _
from subconvert.utils.Encodings import ALL_ENCODINGS
from subconvert.utils.SubFile import File
from subconvert.utils.SubSettings import SubSettings
from subconvert.utils.PropertyFile import loadPropertyFile
from subconvert.gui.FileDialogs import FileDialog
from subconvert.gui.Detail import AUTO_ENCODING_STR
from subconvert.gui.Detail import ActionFactory, SubtitleList, ComboBoxWithHistory
from subconvert.gui.DataModel import SubtitleData
from subconvert.gui.SubtitleCommands import *

log = logging.getLogger('subconvert.%s' % __name__)

class SubTab(QWidget):
    def __init__(self, displayName, isStaticTab, parent = None):
        super(SubTab, self).__init__(parent)
        self._creator = parent
        self._displayName = displayName
        self._isStaticTab = isStaticTab

    @property
    def creator(self):
        return self._creator

    @property
    def isStatic(self):
        return self._isStaticTab

    @property
    def name(self):
        return self._displayName

    def updateTab(self):
        pass

class FileList(SubTab):
    requestOpen = pyqtSignal(str, bool)

    def __init__(self, name, subtitleData, parent = None):
        super(FileList, self).__init__(name, True, parent)
        self._subtitleData = subtitleData
        self._settings = SubSettings()

        self.__initGui()
        self.__connectSignals()

    def __initGui(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        self.__fileList = SubtitleList()
        self.__fileList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        mainLayout.addWidget(self.__fileList)

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.setLayout(mainLayout)

    def __initContextMenu(self):
        self._contextMenu = QMenu()
        af = ActionFactory(self)

        pfileMenu = self._contextMenu.addMenu(_("Use Subtitle Properties"))
        for pfile in self._settings.getLatestPropertyFiles():
            # A hacky way to store pfile in lambda
            action = af.create(
                title = pfile,
                connection = lambda _, pfile=pfile: self._useSubProperties(pfile)
            )
            pfileMenu.addAction(action)
        pfileMenu.addSeparator()
        pfileMenu.addAction(af.create(
            title = _("Open file"), connection = self._chooseSubProperties))

    def __connectSignals(self):
        self.__fileList.mouseButtonDoubleClicked.connect(self.handleDoubleClick)
        self.__fileList.mouseButtonClicked.connect(self.handleClick)
        self.__fileList.keyPressed.connect(self.handleKeyPress)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def addFile(self, filePath, encoding):
        # TODO: separate reading file and adding to the list.
        # TODO: there should be readDataFromFile(filePath, properties=None), which should set
        # TODO: default properties from Subtitle Properties File
        if not self._subtitleData.fileExists(filePath):
            if encoding == AUTO_ENCODING_STR:
                data = self._subtitleData.createDataFromFile(filePath)
            else:
                data = self._subtitleData.createDataFromFile(filePath, encoding)
            icon = QIcon(":/img/initial_list.png")
            item = QListWidgetItem(icon, filePath)
            item.setToolTip(filePath)

            command = NewData(filePath, data)
            self._subtitleData.execute(command)
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

    def handleKeyPress(self, key):
        items = self.__fileList.selectedItems()
        if key in (Qt.Key_Enter, Qt.Key_Return):
            for item in items:
                self.requestOpen.emit(item.text(), False)

    def showContextMenu(self):
        self.__initContextMenu() # redraw menu
        self._contextMenu.exec(QCursor.pos())

    def changeSelectedSubtitleProperties(self, subProperties):
        # TODO: indicate the change somehow
        items = self.__fileList.selectedItems()
        for item in items:
            filePath = item.text()
            data = self._subtitleData.data(filePath)
            data = self._updateDataWithProperties(filePath, data, subProperties)
            command = ChangeData(filePath, data)
            self._subtitleData.execute(command)

    def _chooseSubProperties(self):
        fileDialog = FileDialog(
            parent = self,
            caption = _("Open Subtitle Properties"),
            directory = self._settings.getPropertyFilesPath(),
            filter = _("Subtitle Properties (*.spf);;All files (*)")
        )
        fileDialog.setFileMode(QFileDialog.ExistingFile)

        if fileDialog.exec():
            filename = fileDialog.selectedFiles()[0]
            self._useSubProperties(filename)

    def _useSubProperties(self, propertyPath):
        if propertyPath:
            try:
                subProperties = loadPropertyFile(propertyPath)
            except:
                log.error(_("Cannot read %s as Subtitle Property file.") % propertyPath)
                return

            # Don't change the call order. We don't want to change settings or redraw context menu
            # if something goes wrong.
            self.changeSelectedSubtitleProperties(subProperties)
            self._settings.addPropertyFile(propertyPath)

    def _updateDataWithProperties(self, filePath, data, subProperties):
        subtitleFile = File(filePath)

        if subProperties.inputEncoding == AUTO_ENCODING_STR:
            subProperties.inputEncoding = subtitleFile.detectEncoding()
        data = self._subtitleData.encodedData(filePath, subProperties.inputEncoding)

        data.outputFormat = subProperties.outputFormat

        if subProperties.autoFps:
            data.fps = subtitleFile.detectFps()
        else:
            data.fps = subProperties.fps

        if subProperties.changeEncoding:
            data.outputEncoding = subProperties.outputEncoding
        else:
            data.outputEncoding = subProperties.inputEncoding
        return data


class SubtitleEditor(SubTab):
    def __init__(self, filePath, subtitleData, parent = None):
        name = os.path.split(filePath)[1]
        super(SubtitleEditor, self).__init__(name, False, parent)
        self.__initWidgets()
        self.__initContextMenu()

        self._filePath = filePath
        self._subtitleData = subtitleData
        self._subtitleDataChanged = False

        self.refreshSubtitles()

        # Some signals
        self._subtitleData.fileChanged.connect(self.fileChanged)
        self._model.itemChanged.connect(self._subtitleChanged)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def __initWidgets(self):
        minimalSizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # List of subtitles
        self._model = QStandardItemModel(0, 3, self)
        self._model.setHorizontalHeaderLabels([_("Begin"), _("End"), _("Subtitle")])
        self._subList = QTableView(self)
        self._subList.setModel(self._model)
        self._subList.horizontalHeader().setResizeMode(2, QHeaderView.Stretch)

        # Top toolbar
        toolbar = QHBoxLayout()
        toolbar.setAlignment(Qt.AlignLeft)
        #toolbar.addWidget(someWidget....)
        toolbar.addStretch(1)

        # Main layout
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.addLayout(toolbar, 0, 0, 1, 1) # stretch to the right
        grid.addWidget(self._subList, 1, 0)
        self.setLayout(grid)

    def __initContextMenu(self):
        self._contextMenu = QMenu()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        af = ActionFactory(self)

        encodingsMenu = self._contextMenu.addMenu(_("&Encoding"))
        for encoding in ALL_ENCODINGS:
            action = af.create(
                title = encoding,
                connection = lambda _, encoding=encoding: self.changeEncoding(encoding)
            )
            encodingsMenu.addAction(action)

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
            oldSubtitle = self.subtitles[subNo]
            newSubtitle = deepcopy(oldSubtitle)
            if 0 == column:
                timeStart = FrameTime(time=item.text(), fps = self.data.subtitles.fps)
                newSubtitle.change(start = timeStart)
            elif 1 == column:
                timeEnd = FrameTime(time=item.text(), fps = self.data.subtitles.fps)
                newSubtitle.change(end = timeEnd)
            elif 2 == column:
                newSubtitle.change(text = item.text())
        except Exception as msg:
            # TODO: highlight incorrect column or field with a color on any error
            log.error(msg)
        else:
            command = ChangeSubtitle(self.filePath, oldSubtitle, newSubtitle, subNo)
            self.execute(command)
        self.refreshSubtitle(subNo)

    def showContextMenu(self):
        self._contextMenu.exec(QCursor.pos())

    def changeEncoding(self, encoding):
        if encoding != self.inputEncoding:
            try:
                encodedData = self._subtitleData.encodedData(self.filePath, encoding)
            except UnicodeDecodeError:
                message = QMessageBox(
                    QMessageBox.Warning,
                    _("Decoding error"),
                    _("Cannot decode subtitles to '%s' encoding.\nPlease try different encoding.") % encoding,
                    QMessageBox.Ok, self
                )
                message.exec()
            except LookupError:
                message = QMessageBox(QMessageBox.Warning,
                    _("Unknown encoding"), _("Unknown encoding: '%s'") % encoding,
                    QMessageBox.Ok, self
                )
                message.exec()
            else:
                # TODO: outputEncoding
                command = ChangeData(self.filePath, encodedData)
                self.execute(command)
                self.refreshSubtitles()

    def fileChanged(self, filePath):
        if filePath == self._filePath:
            # Postpone updating subtitles until this tab is visible.
            self._subtitleDataChanged = True
            if self.creator.currentPage() is self:
                self.refreshSubtitles()
                #self.updateTab()

    def refreshSubtitle(self, subNo):
        sub = self.subtitles[subNo]
        self._model.removeRow(subNo)
        self._model.insertRow(subNo, self._createRow(sub))

    def refreshSubtitles(self):
        self._model.removeRows(0, self._model.rowCount())
        for sub in self.subtitles:
            self._model.appendRow(self._createRow(sub))

    def updateTab(self):
        self.refreshSubtitles()

    def execute(self, cmd):
        # TODO: check if subtitleData.fileExists(filePath) ???
        self._subtitleData.fileChanged.disconnect(self.fileChanged)
        self._subtitleData.execute(cmd)
        self._subtitleData.fileChanged.connect(self.fileChanged)

    @property
    def filePath(self):
        return self._filePath

    @property
    def data(self):
        return self._subtitleData.data(self.filePath)

    @property
    def subtitles(self):
        return self.data.subtitles

    @property
    def history(self):
        return self._subtitleData.history(self.filePath)

    @property
    def inputEncoding(self):
        return self.data.inputEncoding

    @property
    def outputEncoding(self):
        return self.data.outputEncoding
