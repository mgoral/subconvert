#-*- coding: utf-8 -*-

"""
Copyright (C) 2011-2015 Michal Goral.

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
import encodings
import bisect

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QTreeWidgetItem
from PyQt5.QtWidgets import QTableView, QHeaderView, QSizePolicy, QPushButton
from PyQt5.QtWidgets import QMessageBox, QAbstractItemView, QAction, QMenu, QFileDialog
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel, QCursor
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QTimer

from subconvert.parsing.FrameTime import FrameTime
from subconvert.parsing.Core import Subtitle
from subconvert.utils.Locale import _
from subconvert.utils.Encodings import ALL_ENCODINGS
from subconvert.utils.SubSettings import SubSettings
from subconvert.utils.PropertyFile import SubtitleProperties, PropertiesFileApplier
from subconvert.utils.SubFile import File
from subconvert.utils.SubtitleSearch import SearchIterator, matchText
from subconvert.gui.FileDialogs import FileDialog
from subconvert.gui.Detail import ActionFactory, SubtitleList, FPS_VALUES
from subconvert.gui.Detail import DisableSignalling, SearchEdit
from subconvert.gui.OffsetDialog import OffsetDialog
from subconvert.gui.SubtitleCommands import *
from subconvert.gui.SubModel import SubListItemDelegate, CustomDataRoles, createRow

log = logging.getLogger('Subconvert.%s' % __name__)

class SubTab(QWidget):
    def __init__(self, displayName, parent = None):
        super(SubTab, self).__init__(parent)
        self._displayName = displayName

    def canClose(self):
        # Redefine in child classes
        return True

    @property
    def isStatic(self):
        # Redefine in child classes
        return False

    @property
    def name(self):
        return self._displayName

    def updateTab(self):
        # Redefine in child classes
        pass

class FileList(SubTab):
    requestOpen = pyqtSignal(str, bool)
    requestRemove = pyqtSignal(str)
    selectionChanged = pyqtSignal()

    def __init__(self, name, subtitleData, parent = None):
        super(FileList, self).__init__(name, parent)
        self._subtitleData = subtitleData
        self._settings = SubSettings()

        self.__initGui()
        self.__connectSignals()

    def __initGui(self):
        self._contextMenu = None

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 3, 0, 0)
        mainLayout.setSpacing(0)

        self.__fileList = SubtitleList()
        fileListHeader = self.__fileList.header()
        self.__resizeHeader(fileListHeader)

        self.__fileList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__fileList.setColumnCount(4)
        self.__fileList.setHeaderLabels([
            _("File name"), _("Input encoding"), _("Output encoding"), _("Subtitle format"),
            _("FPS")])
        mainLayout.addWidget(self.__fileList)

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.setLayout(mainLayout)

    def __resizeHeader(self, header):
        # TODO: add an option (in subconvert settings) to set the following:
        # header.setResizeMode(0, QHeaderView.ResizeToContents);
        header.setStretchLastSection(False)
        header.setDefaultSectionSize(130)
        header.resizeSection(0, 500)

    def __initContextMenu(self):
        if self._contextMenu is not None:
            self._contextMenu.deleteLater()
            self._contextMenu = None

        self._contextMenu = QMenu()
        af = ActionFactory(self)

        selectedItems = self.__fileList.selectedItems()
        anyItemSelected = len(selectedItems) > 0

        # Open in tab

        actionOpenInTab = af.create(
            icon = "window-new", title = _("&Open in tab"), connection = self.requestOpeningSelectedFiles)
        actionOpenInTab.setEnabled(anyItemSelected)
        self._contextMenu.addAction(actionOpenInTab)

        self._contextMenu.addSeparator()

        # Property Files

        pfileMenu = self._contextMenu.addMenu(_("Use Subtitle &Properties"))
        pfileMenu.setEnabled(anyItemSelected)
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

        self._contextMenu.addSeparator()

        # Single properties

        fpsMenu = self._contextMenu.addMenu(_("&Frames per second"))
        fpsMenu.setEnabled(anyItemSelected)
        for fps in FPS_VALUES:
            fpsStr = str(fps)
            action = af.create(
                title = fpsStr,
                connection = lambda _, fps=fps: self.changeSelectedFilesFps(fps))
            fpsMenu.addAction(action)

        formatsMenu = self._contextMenu.addMenu(_("Subtitles forma&t"))
        formatsMenu.setEnabled(anyItemSelected)
        for fmt in self._subtitleData.supportedFormats:
            action = af.create(
                title = fmt.NAME,
                connection = lambda _, fmt=fmt: self.changeSelectedFilesFormat(fmt)
            )
            formatsMenu.addAction(action)

        inputEncodingsMenu = self._contextMenu.addMenu(_("Input &encoding"))
        inputEncodingsMenu.setEnabled(anyItemSelected)
        outputEncodingsMenu = self._contextMenu.addMenu(_("&Output encoding"))
        outputEncodingsMenu.setEnabled(anyItemSelected)
        for encoding in ALL_ENCODINGS:
            outAction = af.create(
                title = encoding,
                connection = lambda _, enc=encoding: self.changeSelectedFilesOutputEncoding(enc)
            )
            outputEncodingsMenu.addAction(outAction)

            inAction = af.create(
                title = encoding,
                connection = lambda _, enc=encoding: self.changeSelectedFilesInputEncoding(enc)
            )
            inputEncodingsMenu.addAction(inAction)

        offset = af.create(None, _("&Offset"), None, None, self._offsetDialog)
        offset.setEnabled(anyItemSelected)
        self._contextMenu.addAction(offset)

        self._contextMenu.addSeparator()

        # Link/unlink video
        actionLink = af.create(None, _("&Link video"), None, None, self.linkVideo)
        actionLink.setEnabled(anyItemSelected)
        self._contextMenu.addAction(actionLink)

        actionLink = af.create(
            None, _("U&nlink video"), None, None, lambda: self.changeSelectedFilesVideoPath(None))
        actionLink.setEnabled(anyItemSelected)
        self._contextMenu.addAction(actionLink)

        actionLink = af.create(None, _("&Get FPS"), None, None, self.detectSelectedFilesFps)
        actionLink.setEnabled(anyItemSelected)
        self._contextMenu.addAction(actionLink)

        self._contextMenu.addSeparator()


        # Show/Remove files

        # Key shortcuts are actually only a hack to provide some kind of info to user that he can
        # use "enter/return" and "delete" to open/close subtitles. Keyboard is handled via
        # keyPressed -> _handleKeyPress. This is because __fileList has focus most of time anyway
        # (I think...)
        actionOpen = af.create(
            None, _("&Show subtitles"), None, "Enter", lambda: self._handleKeyPress(Qt.Key_Enter))
        actionOpen.setEnabled(anyItemSelected)
        self._contextMenu.addAction(actionOpen)

        actionClose = af.create(
            None, _("&Close subtitles"), None, "Delete", lambda: self._handleKeyPress(Qt.Key_Delete))
        actionClose.setEnabled(anyItemSelected)
        self._contextMenu.addAction(actionClose)

        self._contextMenu.addSeparator()

        # Undo/redo

        actionUndo = af.create("undo", _("&Undo"), None, None, self.undoSelectedFiles)
        actionUndo.setEnabled(anyItemSelected)
        self._contextMenu.addAction(actionUndo)

        actionRedo = af.create("redo", _("&Redo"), None, None, self.redoSelectedFiles)
        actionRedo.setEnabled(anyItemSelected)
        self._contextMenu.addAction(actionRedo)

    def __connectSignals(self):
        self.__fileList.mouseButtonDoubleClicked.connect(self._handleDoubleClick)
        self.__fileList.mouseButtonClicked.connect(self._handleClick)
        self.__fileList.keyPressed.connect(self._handleKeyPress)
        self.__fileList.selectionModel().selectionChanged.connect(self._selectionChangedHandle)
        self.customContextMenuRequested.connect(self._showContextMenu)

        self._subtitleData.fileAdded.connect(self._addFile)
        self._subtitleData.fileRemoved.connect(self._removeFile)
        self._subtitleData.fileChanged.connect(self._updateFile)

    def _addFile(self, filePath):
        data = self._subtitleData.data(filePath)

        item = QTreeWidgetItem(
            [filePath, data.inputEncoding, data.outputEncoding, data.outputFormat.NAME,
                str(data.fps)])
        item.setToolTip(0, filePath)

        subtitleIcon = QIcon(":/img/ok.png")
        item.setIcon(0, subtitleIcon)

        videoIcon = QIcon(":/img/film.png") if data.videoPath is not None else QIcon()
        item.setIcon(4, videoIcon)

        self.__fileList.addTopLevelItem(item)

        self._subtitleData.history(filePath).cleanChanged.connect(
            lambda clean: self._cleanStateChanged(filePath, clean))

    def _removeFile(self, filePath):
        items = self.__fileList.findItems(filePath, Qt.MatchExactly)
        for item in items:
            index = self.__fileList.indexOfTopLevelItem(item)
            toDelete = self.__fileList.takeTopLevelItem(index)
            toDelete = None

    def _updateFile(self, filePath):
        items = self.__fileList.findItems(filePath, Qt.MatchExactly)
        if len(items) > 0:
            data = self._subtitleData.data(filePath)
            for item in items:
                item.setText(1, data.inputEncoding)
                item.setText(2, data.outputEncoding)
                item.setText(3, data.outputFormat.NAME)
                item.setText(4, str(data.fps))

                videoIcon = QIcon(":/img/film.png") if data.videoPath is not None else QIcon()
                item.setIcon(4, videoIcon)

    def _cleanStateChanged(self, filePath, clean):
        items = self.__fileList.findItems(filePath, Qt.MatchExactly)
        for item in items:
            if clean:
                icon = QIcon(":/img/ok.png")
            else:
                icon = QIcon(":/img/not_clean.png")
            item.setIcon(0, icon)

    def _selectionChangedHandle(self, selected, deselected):
        self.selectionChanged.emit()

    @property
    def selectedItems(self):
        return self.__fileList.selectedItems()

    def canClose(self):
        return False

    @property
    def isStatic(self):
        return True

    def getCurrentFile(self):
        return self.__fileList.currentItem()

    def _handleClick(self, button):
        item = self.__fileList.currentItem()
        if item is not None and button == Qt.MiddleButton:
            self.requestOpen.emit(item.text(0), True)

    def _handleDoubleClick(self, button):
        item = self.__fileList.currentItem()
        if item is not None and button == Qt.LeftButton:
            self.requestOpen.emit(item.text(0), False)

    def _handleKeyPress(self, key):
        items = self.__fileList.selectedItems()
        if key in (Qt.Key_Enter, Qt.Key_Return):
            for item in items:
                self.requestOpen.emit(item.text(0), False)
        elif key == Qt.Key_Delete:
            for item in items:
                self.requestRemove.emit(item.text(0))

    def _showContextMenu(self):
        self.__initContextMenu() # redraw menu
        self._contextMenu.exec(QCursor.pos())

    def changeSelectedSubtitleProperties(self, subProperties):
        # TODO: indicate the change somehow
        items = self.__fileList.selectedItems()
        applier = PropertiesFileApplier(subProperties)
        for item in items:
            filePath = item.text(0)
            data = self._subtitleData.data(filePath)
            applier.applyFor(filePath, data)
            command = ChangeData(filePath, data, _("Property file: %s") % filePath)
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
                subProperties = SubtitleProperties(
                    self._subtitleData.supportedFormats, propertyPath)
            except:
                log.error(_("Cannot read %s as Subtitle Property file.") % propertyPath)
                self._settings.removePropertyFile(propertyPath)
                return

            # Don't change the call order. We don't want to change settings or redraw context menu
            # if something goes wrong.
            self.changeSelectedSubtitleProperties(subProperties)
            self._settings.addPropertyFile(propertyPath)

    @property
    def filePaths(self):
        fileList = self.__fileList # shorten notation
        return [fileList.topLevelItem(i).text(0) for i in range(fileList.topLevelItemCount())]

    def linkVideo(self):
        movieExtensions = "%s%s" % ("*.", ' *.'.join(File.MOVIE_EXTENSIONS))
        fileDialog = FileDialog(
            parent = self,
            caption = _("Select a video"),
            directory = self._settings.getLatestDirectory(),
            filter = _("Video files (%s);;All files (*)") % movieExtensions)
        fileDialog.setFileMode(QFileDialog.ExistingFile)
        if fileDialog.exec():
            movieFilePath = fileDialog.selectedFiles()[0]
            self.changeSelectedFilesVideoPath(movieFilePath)

    def requestOpeningSelectedFiles(self):
        # Open all files, but focus only the last one
        items = self.__fileList.selectedItems()
        for item in items:
            self.requestOpen.emit(item.text(0), True)
        self.requestOpen.emit(items[-1].text(0), False)

    def changeSelectedFilesFps(self, fps):
        items = self.__fileList.selectedItems()
        for item in items:
            filePath = item.text(0)
            data = self._subtitleData.data(filePath)
            if data.fps != fps:
                data.subtitles.changeFps(fps)
                data.fps = fps
                command = ChangeData(filePath, data, _("FPS: %s") % fps)
                self._subtitleData.execute(command)

    def changeSelectedFilesVideoPath(self, path):
        items = self.__fileList.selectedItems()
        for item in items:
            filePath = item.text(0)
            data = self._subtitleData.data(filePath)
            if data.videoPath != path:
                data.videoPath = path
                command = ChangeData(filePath, data, _("Video path: %s") % path)
                self._subtitleData.execute(command)

    def _offsetDialog(self):
        dialog = OffsetDialog(self, FrameTime(25, seconds=0))
        if dialog.exec():
            self.offsetSelectedFiles(dialog.frametime.fullSeconds)

    def offsetSelectedFiles(self, seconds):
        if seconds == 0:
            return

        items = self.__fileList.selectedItems()
        for item in items:
            filePath = item.text(0)
            data = self._subtitleData.data(filePath)
            fps = data.subtitles.fps
            if fps is None:
                log.error(_("No FPS for '%s' (empty subtitles)." % filePath))
                continue
            ft = FrameTime(fps, seconds=seconds)
            data.subtitles.offset(ft)
            command = ChangeData(filePath, data,
                                _("Offset by: %s") % ft.toStr())
            self._subtitleData.execute(command)

    def detectSelectedFilesFps(self):
        items = self.__fileList.selectedItems()
        for item in items:
            filePath = item.text(0)
            data = self._subtitleData.data(filePath)
            if data.videoPath is not None:
                fpsInfo = File.detectFpsFromMovie(data.videoPath)
                if data.videoPath != fpsInfo.videoPath or data.fps != fpsInfo.fps:
                    data.videoPath = fpsInfo.videoPath
                    data.subtitles.changeFps(fpsInfo.fps)
                    data.fps = fpsInfo.fps
                    command = ChangeData(filePath, data, _("Detected FPS: %s") % data.fps)
                    self._subtitleData.execute(command)

    def changeSelectedFilesFormat(self, fmt):
        items = self.__fileList.selectedItems()
        for item in items:
            filePath = item.text(0)
            data = self._subtitleData.data(filePath)
            if data.outputFormat != fmt:
                data.outputFormat = fmt
                command = ChangeData(filePath, data, _("Format: %s ") % fmt.NAME)
                self._subtitleData.execute(command)

    def changeSelectedFilesInputEncoding(self, inputEncoding):
        items = self.__fileList.selectedItems()
        for item in items:
            filePath = item.text(0)
            data = self._subtitleData.data(filePath)
            if data.inputEncoding != inputEncoding:
                try:
                    data.encode(inputEncoding)
                except UnicodeDecodeError:
                    # TODO: indicate with something more than log entry
                    log.error(_("Cannot decode subtitles to '%s' encoding.") % inputEncoding)
                else:
                    command = ChangeData(filePath, data, _("Input encoding: %s") % inputEncoding)
                    self._subtitleData.execute(command)

    def changeSelectedFilesOutputEncoding(self, outputEncoding):
        items = self.__fileList.selectedItems()
        for item in items:
            filePath = item.text(0)
            data = self._subtitleData.data(filePath)
            if data.outputEncoding != outputEncoding:
                data.outputEncoding = outputEncoding
                command = ChangeData(filePath, data, _("Output encoding: %s") % outputEncoding)
                self._subtitleData.execute(command)

    def undoSelectedFiles(self):
        items = self.__fileList.selectedItems()
        for item in items:
            filePath = item.text(0)
            history = self._subtitleData.history(filePath)
            if history.canUndo():
                history.undo()

    def redoSelectedFiles(self):
        items = self.__fileList.selectedItems()
        for item in items:
            filePath = item.text(0)
            history = self._subtitleData.history(filePath)
            if history.canRedo():
                history.redo()

class SubtitleEditor(SubTab):
    def __init__(self, filePath, subtitleData, parent = None):
        name = os.path.split(filePath)[1]
        super(SubtitleEditor, self).__init__(name, parent)
        self.__initWidgets()
        self.__initContextMenu()

        self._settings = SubSettings()

        self._filePath = filePath
        self._movieFilePath = None
        self._subtitleData = subtitleData

        self.refreshSubtitles()

        # Some signals
        self._subtitleData.fileChanged.connect(self.fileChanged)
        self._subtitleData.subtitlesAdded.connect(self._subtitlesAdded)
        self._subtitleData.subtitlesRemoved.connect(self._subtitlesRemoved)
        self._subtitleData.subtitlesChanged.connect(self._subtitlesChanged)
        self._model.itemChanged.connect(self._subtitleEdited)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def __initWidgets(self):
        minimalSizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # List of subtitles
        subListDelegate = SubListItemDelegate()
        self._model = QStandardItemModel(0, 3, self)
        self._model.setHorizontalHeaderLabels([_("Begin"), _("End"), _("Subtitle")])
        self._subList = QTableView(self)
        self._subList.setModel(self._model)
        self._subList.setItemDelegateForColumn(0, subListDelegate)
        self._subList.setItemDelegateForColumn(1, subListDelegate)
        self._subList.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        self._searchBar = SearchBar(self)
        self._searchBar.hide()

        # Top toolbar
        toolbar = QHBoxLayout()
        toolbar.setAlignment(Qt.AlignLeft)
        #toolbar.addWidget(someWidget....)
        toolbar.addStretch(1)

        # Main layout
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(0, 3, 0, 0)
        grid.addLayout(toolbar, 0, 0, 1, 1) # stretch to the right
        grid.addWidget(self._subList, 1, 0)
        grid.addWidget(self._searchBar, 2, 0)
        self.setLayout(grid)

    def __initContextMenu(self):
        self._contextMenu = QMenu(self)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        af = ActionFactory(self)

        insertSub = af.create(title = _("&Insert subtitle"), icon = "list-add",
            connection = self.insertNewSubtitle)
        self._contextMenu.addAction(insertSub)

        insertSub = af.create(title = _("&Add subtitle"), icon = "list-add",
            connection = self.addNewSubtitle)
        self._contextMenu.addAction(insertSub)

        removeSub = af.create(title = _("&Remove subtitles"), icon = "list-remove",
            connection = self.removeSelectedSubtitles)
        self._contextMenu.addAction(removeSub)

    def _changeRowBackground(self, rowNo, bg):
        with DisableSignalling(self._model.itemChanged, self._subtitleEdited):
            for columnNo in range(self._model.columnCount()):
                item = self._model.item(rowNo, columnNo)
                item.setBackground(bg)

    def _changeItemData(self, item, val, role):
        with DisableSignalling(self._model.itemChanged, self._subtitleEdited):
            item.setData(val, role)

    def _handleIncorrectItem(self, item):
        with DisableSignalling(self._model.itemChanged, self._subtitleEdited):
            item.setData(False, CustomDataRoles.ErrorFlagRole)

        bg = item.background()
        rowNo = item.row()
        self._changeRowBackground(rowNo, Qt.red)
        QTimer.singleShot(600, lambda rowNo=rowNo, bg=bg: self._changeRowBackground(rowNo, bg))

    def _subtitleEdited(self, item):
        modelIndex = item.index()
        column = modelIndex.column()
        subNo = modelIndex.row()

        errorFlag = item.data(CustomDataRoles.ErrorFlagRole)
        if errorFlag is True:
            self._handleIncorrectItem(item)
        else:
            # TODO: timeStart and timeEnd might be displayed in a frame format in a bright future.
            # Check it and create FrameTime properly in that case.
            # TODO: Maybe add column numbers to some kind of enum to avoid magic numbers?
            oldSubtitle = self.subtitles[subNo]
            newSubtitle = oldSubtitle.clone()
            if 0 == column:
                timeStart = item.data(CustomDataRoles.FrameTimeRole)
                newSubtitle.change(start = timeStart)
            elif 1 == column:
                timeEnd = item.data(CustomDataRoles.FrameTimeRole)
                newSubtitle.change(end = timeEnd)
            elif 2 == column:
                newSubtitle.change(text = item.text())
            command = ChangeSubtitle(self.filePath, oldSubtitle, newSubtitle, subNo)
            self._subtitleData.execute(command)

    def _subtitlesAdded(self, path, subNos):
        if path != self.filePath:
            return

        subtitles = self.subtitles
        for subNo in subNos:
            row = createRow(subtitles[subNo])
            self._model.insertRow(subNo, row)

    def _subtitlesRemoved(self, path, subNos):
        if path != self.filePath:
            return

        for subNo in subNos:
            self._model.removeRow(subNo)

    def _subtitlesChanged(self, path, subNos):
        if path != self.filePath:
            return

        for subNo in subNos:
            self.refreshSubtitle(subNo)

    def _createNewSubtitle(self, data, subNo):
        fps = data.fps # data is passed to avoid unnecessary copies
        minFrameTime = FrameTime(fps, frames = 1)

        # calculate correct minimum subtitle start time
        if subNo > 0:
            timeStart = data.subtitles[subNo - 1].end + minFrameTime
        else:
            timeStart = FrameTime(fps, frames = 0)

        # calculate correct maximum subtitle end time
        if subNo < data.subtitles.size():
            try:
                timeEnd = data.subtitles[subNo].start - minFrameTime
            except SubException:
                timeEnd = FrameTime(fps, frames = 0)
        else:
            timeEnd = timeStart + FrameTime(fps, frames = 50)

        # add subtitle to DataModel
        sub = Subtitle(timeStart, timeEnd, "")
        command = AddSubtitle(self.filePath, subNo, sub)
        with DisableSignalling(self._subtitleData.subtitlesAdded, self._subtitlesAdded):
            self._subtitleData.execute(command)

        # create subtitle graphical representation in editor sub list
        row = createRow(sub)
        self._model.insertRow(subNo, row)
        index = self._model.index(subNo, 2)
        self._subList.clearSelection()
        self._subList.setCurrentIndex(index)
        self._subList.edit(index)

    def addNewSubtitle(self):
        data = self.data
        subNo = data.subtitles.size()
        indices = self._subList.selectedIndexes()
        if len(indices) > 0:
            rows = [index.row() for index in indices]
            subNo = max(rows) + 1
        self._createNewSubtitle(data, subNo)

    def insertNewSubtitle(self):
        data = self.data
        subNo = 0
        indices = self._subList.selectedIndexes()
        if len(indices) > 0:
            rows = [index.row() for index in indices]
            subNo = max(rows)
        self._createNewSubtitle(data, subNo)

    def removeSelectedSubtitles(self):
        indices = self._subList.selectedIndexes()
        if len(indices) > 0:
            rows = list(set([index.row() for index in indices]))
            command = RemoveSubtitles(self.filePath, rows)
            self._subtitleData.execute(command)
            if self._model.rowCount() > rows[-1]:
                self._subList.selectRow(rows[-1])
            else:
                self._subList.selectRow(self._model.rowCount() - 1)

    def highlight(self):
        self._searchBar.show()
        self._searchBar.highlight()

    def showContextMenu(self):
        self._contextMenu.exec(QCursor.pos())

    def changeInputEncoding(self, encoding):
        data = self._subtitleData.data(self.filePath)
        if encoding != data.inputEncoding:
            try:
                data.encode(encoding)
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
                command = ChangeData(self.filePath, data, _("Input encoding: %s") % encoding)
                self._subtitleData.execute(command)

    def changeOutputEncoding(self, encoding):
        data = self._subtitleData.data(self.filePath)
        if encoding != data.outputEncoding:
            data.outputEncoding = encoding
            command = ChangeData(self.filePath, data, _("Output encoding: %s") % encoding)
            self._subtitleData.execute(command)

    def changeSubFormat(self, fmt):
        data = self._subtitleData.data(self.filePath)
        if data.outputFormat != fmt:
            data.outputFormat = fmt
            command = ChangeData(self.filePath, data)
            self._subtitleData.execute(command)

    def changeFps(self, fps):
        data = self.data
        if data.fps != fps:
            data.subtitles.changeFps(fps)
            data.fps = fps
            command = ChangeData(self.filePath, data, _("FPS: %s") % fps)
            self._subtitleData.execute(command)

    def changeVideoPath(self, path):
        data = self.data
        if data.videoPath != path:
            data.videoPath = path
            command = ChangeData(self.filePath, data, _("Video path: %s") % path)
            self._subtitleData.execute(command)

    def offset(self, seconds):
        data = self.data
        fps = data.subtitles.fps
        if fps is None:
            log.error(_("No FPS for '%s' (empty subtitles)." % self.filePath))
            return
        ft = FrameTime(data.subtitles.fps, seconds=seconds)
        data.subtitles.offset(ft)
        command = ChangeData(self.filePath, data,
                             _("Offset by: %s") % ft.toStr())
        self._subtitleData.execute(command)

    def detectFps(self):
        data = self.data
        if data.videoPath is not None:
            fpsInfo = File.detectFpsFromMovie(data.videoPath)
            if data.videoPath != fpsInfo.videoPath or data.fps != fpsInfo.fps:
                data.videoPath = fpsInfo.videoPath
                data.subtitles.changeFps(fpsInfo.fps)
                data.fps = fpsInfo.fps
                command = ChangeData(self.filePath, data, _("Detected FPS: %s") % data.fps)
                self._subtitleData.execute(command)

    def fileChanged(self, filePath):
        if filePath == self._filePath:
            self.refreshSubtitles()

    def refreshSubtitle(self, subNo):
        sub = self.subtitles[subNo]
        self._model.removeRow(subNo)
        self._model.insertRow(subNo, createRow(sub))

    def refreshSubtitles(self):
        self._model.removeRows(0, self._model.rowCount())
        for sub in self.subtitles:
            self._model.appendRow(createRow(sub))

    def updateTab(self):
        self.refreshSubtitles()

    def selectedSubtitles(self):
        rows = self.selectedRows()
        subtitleList = [self.subtitles[row] for row in rows]
        return subtitleList

    def selectedRows(self):
        indices = self._subList.selectedIndexes()
        # unique list
        rows = list(set([index.row() for index in indices]))
        rows.sort()
        return rows

    def selectRow(self, row):
        self._subList.selectRow(row)

    @property
    def filePath(self):
        return self._filePath

    @property
    def movieFilePath(self):
        return self._movieFilePath

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

    @property
    def outputFormat(self):
        return self.data.outputFormat

class SearchBar(QWidget):
    class SearchDirection:
        Forward = 1
        Backward = 2

    def __init__(self, parent):
        super(SearchBar, self).__init__(parent)

        self._sit = None

        self._editor = SearchEdit(self)
        self._prevButton = QPushButton("<", self)
        self._nextButton = QPushButton(">", self)
        self._closeButton = QPushButton(QIcon.fromTheme("window-close"), "", self)

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        layout.setSpacing(0)

        layout.addWidget(self._editor)
        layout.addWidget(self._prevButton)
        layout.addWidget(self._nextButton)
        layout.addWidget(self._closeButton)
        layout.setContentsMargins(1, 1, 1, 1)

        self.setLayout(layout)

        self._nextButton.clicked.connect(self.next)
        self._prevButton.clicked.connect(self.prev)
        self._closeButton.clicked.connect(self.hide)
        self._editor.textChanged.connect(self._reset)
        self._editor.returnPressed.connect(self.next)
        self._editor.escapePressed.connect(self.hide)

    def highlight(self):
        self._editor.setFocus()
        self._editor.selectAll()

    def next(self):
        self._search(self.SearchDirection.Forward)

    def prev(self):
        self._search(self.SearchDirection.Backward)

    def _search(self, direction):
        if self._editor.text() == "":
            self._reset()
            return

        if self._sit is None:
            data = self.parent().data
            case = any(map(str.isupper, self._editor.text()))
            self._sit = SearchIterator(data.subtitles,
                lambda sub, text = self._editor.text(), case = case: matchText(sub, text, case))

        self._updateIteratorPositionFromSelection(direction)

        fn = self._sit.next if direction == self.SearchDirection.Forward else self._sit.prev
        try:
            subNo = fn()
            self.parent().selectRow(subNo)
        except StopIteration:
            self._searchError()

    def _updateIteratorPositionFromSelection(self, direction):
        selections = self.parent().selectedRows()
        startRow = selections[-1] if len(selections) > 0 else -1

        if startRow == -1 or len(self._sit.range()) == 0:
            return

        # When iterator points at different row, it means that user changed it
        if startRow != self._sit.last():
            pos = None
            if direction == self.SearchDirection.Forward:
                pos = bisect.bisect_right(self._sit.range(), startRow) - 1
            else:
                pos = bisect.bisect_left(self._sit.range(), startRow)
            self._sit.setpos(pos)

    def _searchError(self):
        self._editor.setStyleSheet("background-color: #CD5555")

    def _reset(self):
        self._sit = None
        self._editor.setStyleSheet("")

