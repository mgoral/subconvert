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

from subconvert.parsing.Core import SubConverter
from subconvert.parsing.Formats import *
from subconvert.gui import SubtitleWindow
from subconvert.gui.DataModel import DataController, SubtitleData
from subconvert.gui.PropertyFileEditor import PropertyFileEditor
from subconvert.gui.FileDialogs import FileDialog
from subconvert.utils.SubSettings import SubSettings
from subconvert.utils.SubFile import File

log = logging.getLogger('Subconvert.%s' % __name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.__initGui()
        self.__initActions()
        self.__initMenuBar()
        self.__updateMenuItemsState()
        self.__connectSignals()
        self.show()

    def __initGui(self):
        self._settings = SubSettings()
        self.mainWidget = QWidget(self)
        mainLayout = QGridLayout()
        mainLayout.setContentsMargins(3, 3, 3, 3)

        self.setCentralWidget(self.mainWidget)

        self._subtitleData = DataController(self)
        self._tabs = SubtitleWindow.SubTabWidget(self._subtitleData)

        mainLayout.addWidget(self._tabs)

        self.statusBar()

        self.mainWidget.setLayout(mainLayout)
        self.setWindowTitle('Subconvert') # TODO: current file path

    def __connectSignals(self):
        self._subtitleData.fileAdded.connect(self.__updateMenuItemsState)
        self._subtitleData.fileRemoved.connect(self.__updateMenuItemsState)
        self._tabs.tabChanged.connect(self.__updateMenuItemsState)
        self._tabs.tabChanged.connect(self.__connectUndoRedo)

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
            "document-save",_("S&ave as..."), _("Save current file as..."), "ctrl++shift+s",
            self.saveFileAs)
        self._createAction("saveAllFiles",
            "document-save", _("Sa&ve all"), _("Save all opened files."), None, self.saveAll)
        self._createAction("exit",
            "application-exit", _("&Exit"), _("Exit Subconvert."), None, qApp.quit)
        self._createAction("nextTab", None, None, None, "ctrl+tab", self.nextTab)
        self._createAction("previousTab", None, None, None, "ctrl+shift+tab", self.previousTab)
        self._createAction("closeTab", None, None, None, "ctrl+w", self.closeTab)

        self._createAction("undo", None, _("Undo"), None, "ctrl+z", self.undo)
        self._createAction("redo", None, _("Redo"), None, "ctrl+shift+z", self.redo)

        self._createAction("pfileEditor", None, _("Subtitle &Properties Editor"), None, None,
                self.openPropertyEditor)

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

        editMenu = menubar.addMenu(_("&Edit"))
        editMenu.addAction(self._actions["undo"])
        editMenu.addAction(self._actions["redo"])

        toolsMenu = menubar.addMenu(_("&Tools"))
        toolsMenu.addAction(self._actions["pfileEditor"])

    def __getAllSubExtensions(self):
        formats = SubFormat.__subclasses__()
        exts = [_('Default')]
        exts.extend(set([ f.EXTENSION for f in formats ]))
        exts.sort()
        return exts

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
    def __connectUndoRedo(self):
        tab = self._tabs.currentPage()
        anyTabOpen = tab is not None
        tabIsStatic = tab.isStatic if anyTabOpen else False

        if anyTabOpen and not tabIsStatic:
            # yeah, __updateMenuItemsState is called too frequently but that's a low price for
            # increased code readability
            tab.history.canRedoChanged.connect(self.__updateMenuItemsState)
            tab.history.canUndoChanged.connect(self.__updateMenuItemsState)

    @pyqtSlot(bool)
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

        self._actions["undo"].setEnabled(anyTabOpen and not tabIsStatic and tab.history.canUndo())
        self._actions["redo"].setEnabled(anyTabOpen and not tabIsStatic and tab.history.canRedo())

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

        fileDialog = FileDialog(
            parent = self,
            caption = _("Open file"),
            directory = self._settings.getLatestDirectory(),
            filter = _("Subtitles (%s);;All files (*)") % str_sub_exts
        )
        fileDialog.addEncodings(True)
        fileDialog.setFileMode(QFileDialog.ExistingFiles)

        if fileDialog.exec():
            filenames = fileDialog.selectedFiles()
            encoding = fileDialog.getEncoding()
            self._settings.setLatestDirectory(os.path.dirname(filenames[0]))
            for filePath in filenames:
                self._tabs.fileList.addFile(filePath, encoding)

    def saveFile(self):
        currentTab = self._tabs.currentPage()
        currentTab.saveContent()
        self._writeFile(currentTab.filePath)

    def saveFileAs(self):
        fileDialog = FileDialog(
            parent = self,
            caption = _('Save as...'),
            directory = self._settings.getLatestDirectory()
        )
        fileDialog.addFormats()
        fileDialog.addEncodings(True)
        fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        fileDialog.setFileMode(QFileDialog.AnyFile)

        if fileDialog.exec():
            newFileName = fileDialog.selectedFiles()[0]
            currentTab = self._tabs.currentPage()
            currentTab.saveContent()
            self._settings.setLatestDirectory(os.path.dirname(newFileName))
            self._writeFile(currentTab.filePath, newFileName)

    def saveAll(self):
        # BUG!!!!!!!!!!!!
        # FIXME: fetch self._tabs.fileList list of opened files instead of opened tabs. We want to
        # save all files, not only those shown in tabs.
        # When asked to save file, FileList should check whether it's parsed and parse it if it's
        # not (in future the parsing moment might be moved to invrease responsibility when opening
        # a lot of files - i.e. only a file list will be printed and files will be actually parsed
        # on their first use (e.g. on tab open, fps change etc.). I'll have to think about it).
        # END OF FIXME
        for i in range(self._tabs.count()):
            tab = self._tabs.tab(i)
            if tab is not None and not tab.isStatic:
                tab.saveContent()
                self._writeFile(tab.filePath)
        # END OF BUG!!!!!!!!!!!!!

    def undo(self):
        currentTab = self._tabs.currentPage()
        currentTab.history.undo()

    def redo(self):
        currentTab = self._tabs.currentPage()
        currentTab.history.redo()

    def openPropertyEditor(self):
        editor = PropertyFileEditor(self)
        editor.exec()

