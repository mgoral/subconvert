#-*- coding: utf-8 -*-

"""
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


import os
import gettext
import logging

from PyQt4 import QtGui, QtCore

from subconvert.parsing.Core import SubManager, SubParser, SubConverter
from subconvert.parsing.Formats import *
from subconvert.gui import SubtitleWindow
from subconvert.gui.DataModel import DataController, SubtitleData
from subconvert.utils.SubFile import File

log = logging.getLogger('Subconvert.%s' % __name__)

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        #self.userSettings = QtCore.QSettings(QtCore.QSettings.IniFormat,
        #    QtCore.QSettings.UserScope, "logmaster", "rc")
        #self.windowSettings = QtCore.QSettings(QtCore.QSettings.IniFormat,
        #    QtCore.QSettings.UserScope, "logmaster", "window")

        self.__createParser()
        self.__initGui()
        self.show()

    def __createParser(self):
        self._parser = SubParser()
        for Format in SubFormat.__subclasses__():
            self._parser.registerFormat(Format)

    def __initGui(self):
        self.mainWidget = QtGui.QWidget(self)
        mainLayout = QtGui.QGridLayout()
        mainLayout.setContentsMargins(3, 3, 3, 3)

        self.setCentralWidget(self.mainWidget)

        self._subtitleData = DataController(self)
        self._tabs = SubtitleWindow.SubTabWidget(self._subtitleData)
        self.fileDialog = QtGui.QFileDialog
        self.directory = QtCore.QDir.homePath() # TODO: read from config

        mainLayout.addWidget(self._tabs)

        self.__initMenuBar()

        self.statusBar()
        self.menuBar()
        self._updateMenuItemsState()

        self.mainWidget.setLayout(mainLayout)
        self.setWindowTitle('Subconvert') # TODO: current file path

        # Some signals
        self._subtitleData.fileAdded.connect(self._updateMenuItemsState)
        self._subtitleData.fileRemoved.connect(self._updateMenuItemsState)
        self._tabs.tabChanged.connect(self._updateMenuItemsState)

    def __initMenuBar(self):
        menubar = self.menuBar()

        self.openAction = QtGui.QAction(
            QtGui.QIcon.fromTheme('document-open'), _('&Open'), self)
        self.openAction.setStatusTip(_("Open log file in current tab."))
        self.openAction.setShortcut('ctrl+o')    # TODO: read this from settings
        self.openAction.triggered.connect(self.openFile)

        self.saveAction = QtGui.QAction(
            QtGui.QIcon.fromTheme('document-save'), _('&Save'), self)
        self.saveAction.setStatusTip(_("Save currently opened file."))
        self.saveAction.setShortcut('ctrl+s')    # TODO: read this from settings
        self.saveAction.triggered.connect(self.saveFile)

        self.saveAsAction = QtGui.QAction(
            QtGui.QIcon.fromTheme('document-save'), _('S&ave as...'), self)
        self.saveAsAction.setShortcut('ctrl+shift+s')    # TODO: read this from settings
        self.saveAsAction.setStatusTip(_("Save currently opened file under different name"))
        self.saveAsAction.triggered.connect(self.saveFileAs)

        self.saveAllAction = QtGui.QAction(
            QtGui.QIcon.fromTheme('document-save'), _('Sa&ve all'), self)
        self.saveAllAction.setStatusTip(_("Save all opened files."))
        self.saveAllAction.triggered.connect(self.saveAll)

        self.exitApp= QtGui.QAction(QtGui.QIcon.fromTheme('application-exit'), _('&Exit'), self)
        self.exitApp.setStatusTip(_("Exit Subconvert"))
        self.exitApp.triggered.connect(QtGui.qApp.quit)

        fileMenu = menubar.addMenu(_('&File'))
        fileMenu.addAction(self.openAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)
        fileMenu.addAction(self.saveAllAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitApp)

    def __getAllSubExtensions(self):
        formats = SubFormat.__subclasses__()
        exts = [_('Default')]
        exts.extend(set([ f.EXTENSION for f in formats ]))
        exts.sort()
        return exts

    def __createSubtitles(self, file_):
        # TODO: fetch fps and encoding from user input (e.g. commandline options, settings, etc)
        fps = 25
        inputEncoding = None
        fileContent = file_.read(inputEncoding)
        subtitles = self._parser.parse(fileContent)
        return subtitles

    def __addFile(self, filePath):
        if not self._subtitleData.fileExists(filePath):
            try:
                file_ = File(filePath)
            except IOError as msg:
                log.error(msg)
                return
            data = SubtitleData()
            data.subtitles = self.__createSubtitles(file_)
            if self._parser.isParsed:
                # TODO: fetch those somehow
                data.outputFormat = self._parser.parsedFormat()
                data.outputEncoding = "utf8"
                self._subtitleData.add(filePath, data)
            else:
                log.error(_("Unable to parse file '%s'.") % filePath)

    def _writeFile(self, filePath, newFilePath=None):
        if newFilePath is None:
            newFilePath = filePath

        data = self._subtitleData.data(filePath)
        converter = SubConverter()
        content = converter.convert(data.outputFormat, data.subtitles)

        if File.exists(newFilePath):
            file_ = File(newFilePath)
            file_.overwrite(content, data.outputEncoding)
        else:
            File.write(newFilePath, content, data.outputEncoding)

    def _saveFileDirectory(self, filename):
            self.directory = os.path.split(filename)[0]

    @QtCore.pyqtSlot(int)
    @QtCore.pyqtSlot(str)
    def _updateMenuItemsState(self):
        dataAvailable = self._subtitleData.count() != 0
        anyTabOpen = self._tabs.currentPage() is not None

        self.saveAllAction.setEnabled(dataAvailable)
        self.saveAction.setEnabled(anyTabOpen)
        self.saveAsAction.setEnabled(anyTabOpen)

    def openFile(self):
        sub_extensions = self.__getAllSubExtensions()
        str_sub_exts = ' '.join(['*.%s' % ext for ext in sub_extensions[1:]])
        filenames = self.fileDialog.getOpenFileNames(
            parent = self,
            caption = _('Open file'),
            directory = self.directory,
            filter = _("Subtitles (%s);;All files (*.*)") % str_sub_exts
        )
        try:
            self._saveFileDirectory(filenames[0])
        except IndexError:
            pass    # Normal error when hitting "Cancel" - list of fileNames is empty
        for filePath in filenames:
            self.__addFile(filePath)

    def saveFile(self):
        currentTab = self._tabs.currentPage()
        currentTab.saveContent()
        self._writeFile(currentTab.filePath)

    def saveFileAs(self):
        currentTab = self._tabs.currentPage()
        newFileName = self.fileDialog.getSaveFileName(
            parent = self,
            caption = _('Save as...'),
            directory = self.directory
        )
        if newFileName:
            currentTab.saveContent()
            self._saveFileDirectory(newFileName)
            self._writeFile(currentTab.filePath, newFileName)

    def saveAll(self):
        for i in range(self._tabs.count()):
            tab = self._tabs.tab(i)
            if tab is not None:
                tab.saveContent()
                self._writeFile(tab.filePath)


