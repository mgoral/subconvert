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

from PyQt4.QtGui import QMainWindow, QWidget, QFileDialog, QGridLayout, QAction, QIcon, qApp
from PyQt4.QtCore import pyqtSlot, QDir

from subconvert.parsing.Core import SubManager, SubParser, SubConverter
from subconvert.parsing.Formats import *
from subconvert.gui import SubtitleWindow
from subconvert.gui.DataModel import DataController, SubtitleData
from subconvert.utils.SubSettings import SubSettings
from subconvert.utils.SubFile import File

log = logging.getLogger('Subconvert.%s' % __name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.__createParser()
        self.__initGui()
        self.__initActions()
        self.__initMenuBar()
        self.__updateMenuItemsState()
        self.__connectSignals()
        self.show()

    def __createParser(self):
        self._parser = SubParser()
        for Format in SubFormat.__subclasses__():
            self._parser.registerFormat(Format)

    def __initGui(self):
        self._settings = SubSettings()
        self.mainWidget = QWidget(self)
        mainLayout = QGridLayout()
        mainLayout.setContentsMargins(3, 3, 3, 3)

        self.setCentralWidget(self.mainWidget)

        self._subtitleData = DataController(self)
        self._tabs = SubtitleWindow.SubTabWidget(self._subtitleData)
        self.fileDialog = QFileDialog

        mainLayout.addWidget(self._tabs)

        self.statusBar()

        self.mainWidget.setLayout(mainLayout)
        self.setWindowTitle('Subconvert') # TODO: current file path

    def __connectSignals(self):
        self._subtitleData.fileAdded.connect(self.__updateMenuItemsState)
        self._subtitleData.fileRemoved.connect(self.__updateMenuItemsState)
        self._tabs.tabChanged.connect(self.__updateMenuItemsState)

    def _createAction(self, name, icon=None, title=None, tip=None, shortcut=None, connection=None):
        action = QAction(self)

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

        self.addAction(action)
        self._actions[name] = action # This way all actions can be immediately used
        return self._actions[name]

    def __initActions(self):
        self._actions = {}
        self._createAction("openFile",
            "document-open", _("&Open"), _("Open subtitle file."), "ctrl+o", self.openFile)
        self._createAction("saveFile",
            "document-save", _("&Save"), _("Save current file."), "ctrl+s", self.saveFile)
        self._createAction("saveFileAs",
            "document-save",_("&S&ave as..."), _("Save current file as..."), "ctrl++shift+s",
            self.saveFileAs)
        self._createAction("saveAllFiles",
            "document-save", _("&Sa&ve all"), _("Save all opened files."), None, self.saveAll)
        self._createAction("exit",
            "application-exit", _("&Exit"), _("Exit Subconvert."), None, qApp.quit)
        self._createAction("nextTab", None, None, None, "ctrl+tab", self.nextTab)
        self._createAction("previousTab", None, None, None, "ctrl+shift+tab", self.previousTab)
        self._createAction("closeTab", None, None, None, "ctrl+w", self.closeTab)

    def __initMenuBar(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu(_('&File'))
        fileMenu.addAction(self._actions["openFile"])
        fileMenu.addSeparator()
        fileMenu.addAction(self._actions["saveFile"])
        fileMenu.addAction(self._actions["saveFileAs"])
        fileMenu.addAction(self._actions["saveAllFiles"])
        fileMenu.addSeparator()
        fileMenu.addAction(self._actions["exit"])

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

    @pyqtSlot(int)
    @pyqtSlot(str)
    def __updateMenuItemsState(self):
        tab = self._tabs.currentPage()
        dataAvailable = self._subtitleData.count() != 0
        anyTabOpen = tab is not None
        tabIsStatic = tab.isStatic if anyTabOpen else False

        self._actions["saveAllFiles"].setEnabled(dataAvailable)
        self._actions["saveFile"].setEnabled(anyTabOpen and not tabIsStatic)
        self._actions["saveFileAs"].setEnabled(anyTabOpen and not tabIsStatic)

    def nextTab(self):
        if self._tabs.count() > 0:
            index = self._tabs.currentIndex() + 1
            if index > self._tabs.count() - 1:
                index = 0
            self._tabs.showTab(index)

    def previousTab(self):
        if self._tabs.count() > 0:
            index = self._tabs.currentIndex() - 1
            if index < 0:
                index = self._tabs.count() - 1
            self._tabs.showTab(index)

    def closeTab(self):
        if self._tabs.count() > 0:
            index = self._tabs.currentIndex()
            self._tabs.closeTab(index)

    def openFile(self):
        sub_extensions = self.__getAllSubExtensions()
        str_sub_exts = ' '.join(['*.%s' % ext for ext in sub_extensions[1:]])
        filenames = self.fileDialog.getOpenFileNames(
            parent = self,
            caption = _('Open file'),
            directory = self._settings.getLatestDirectory(),
            filter = _("Subtitles (%s);;All files (*.*)") % str_sub_exts
        )
        try:
            self._settings.setLatestDirectory(os.path.dirname(filenames[0]))
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
            directory = self._settings.getLatestDirectory()
        )
        if newFileName:
            currentTab.saveContent()
            self._settings.setLatestDirectory(os.path.dirname(newFileName))
            self._writeFile(currentTab.filePath, newFileName)

    def saveAll(self):
        for i in range(self._tabs.count()):
            tab = self._tabs.tab(i)
            if tab is not None:
                tab.saveContent()
                self._writeFile(tab.filePath)


