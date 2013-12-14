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
from string import Template

from PyQt4.QtGui import QMainWindow, QWidget, QFileDialog, QGridLayout, QAction, QIcon, qApp
from PyQt4.QtGui import QMessageBox, QPixmap, QSpacerItem, QDesktopServices
from PyQt4.QtCore import pyqtSlot, QDir, Qt, QUrl

from subconvert.parsing.Core import SubConverter
from subconvert.parsing.Formats import *
from subconvert.gui import SubtitleWindow
from subconvert.gui.DataModel import DataController
from subconvert.gui.PropertyFileEditor import PropertyFileEditor
from subconvert.gui.FileDialogs import FileDialog
from subconvert.gui.Detail import ActionFactory, CannotOpenFilesMsg, MessageBoxWithList, FPS_VALUES
from subconvert.gui.SubtitleCommands import *
from subconvert.utils.Locale import _, P_
from subconvert.utils.Encodings import ALL_ENCODINGS
from subconvert.utils.SubSettings import SubSettings
from subconvert.utils.SubFile import File, SubFileError
from subconvert.utils.version import __version__, __author__, __license__, __website__, __transs__

log = logging.getLogger('Subconvert.%s' % __name__)

substituteDict = {
    "author": __author__,
    "license": __license__,
    "version": __version__,
    "website": __website__,
    "icon_author": "gasyoun",
    "icon_website": "http://led24.de/iconset/",
    "translators": ", ".join(__transs__)
}

aboutText = Template(_("""
<h2>Subconvert</h2>
<p>
Version: $version<br/>
Website: <a href="$website">$website</a><br/>
License: $license
</p>

<h3>Authors</h3>
<p>
Development: $author<br/>
Logo: $author<br/>
Icons: <a href="$icon_website">$icon_author</a><br/>
Translations: $translators
</p>

<h3>About</h3>
<p>This is Subconvert - movie subtitles editor and converter.</p>
<p>If you'd like to help at developing Subconvert, see program <a href="$website">website</a> or contact author.</p>
""")).substitute(substituteDict)

class MainWindow(QMainWindow):
    def __init__(self, args):
        super(MainWindow, self).__init__()

        self.__initGui()
        self.__initActions()
        self.__initMenuBar()
        self.__initShortcuts()
        self.__updateMenuItemsState()
        self.__connectSignals()

        self.handleArgs(args)

    def __initGui(self):
        self._settings = SubSettings()
        self.mainWidget = QWidget(self)
        mainLayout = QGridLayout()
        mainLayout.setContentsMargins(3, 3, 3, 3)

        self.setCentralWidget(self.mainWidget)

        self._subtitleData = DataController(self)
        self._tabs = SubtitleWindow.SubTabWidget(self._subtitleData)

        mainLayout.addWidget(self._tabs, 0, 0)

        self.statusBar()

        self.mainWidget.setLayout(mainLayout)
        self.setWindowTitle('Subconvert')

    def __connectSignals(self):
        self._subtitleData.fileAdded.connect(self.__updateMenuItemsState, Qt.QueuedConnection)
        self._subtitleData.fileChanged.connect(self.__updateMenuItemsState, Qt.QueuedConnection)
        self._subtitleData.fileRemoved.connect(self.__updateMenuItemsState, Qt.QueuedConnection)
        self._tabs.tabChanged.connect(self.__updateMenuItemsState)
        self._tabs.tabChanged.connect(self.__updateWindowTitle)

    def __initActions(self):
        self._actions = {}
        af = ActionFactory(self)

        # open / save
        self._actions["openFile"] = af.create(
            "document-open", _("&Open"), _("Open subtitle file."), "ctrl+o", self.openFile)
        self._actions["saveFile"] = af.create(
            "document-save", _("&Save"), _("Save current file."), "ctrl+s", self.saveFile)
        self._actions["saveFileAs"] = af.create(
            "document-save",_("S&ave as..."), _("Save current file as..."), "ctrl++shift+s",
            self.saveFileAs)
        self._actions["saveAllFiles"] = af.create(
            "document-save", _("Sa&ve all"), _("Save all opened files."), None, self.saveAll)

        # app exit
        self._actions["exit"] = af.create(
            "application-exit", _("&Exit"), _("Exit Subconvert."), None, qApp.quit)

        # tab management
        self._actions["nextTab"] = af.create(
            None, None, None, "ctrl+tab", self.nextTab)
        self._actions["previousTab"] = af.create(
            None, None, None, "ctrl+shift+tab", self.previousTab)
        self._actions["closeTab"] = af.create(
            None, None, None, "ctrl+w", self.closeTab)

        # Subtitles
        self._actions["undo"] = af.create(
            None, _("&Undo"), None, "ctrl+z", self.undo)
        self._actions["redo"] = af.create(
            None, _("&Redo"), None, "ctrl+shift+z", self.redo)

        for fps in FPS_VALUES:
            fpsStr = str(fps)
            self._actions[fpsStr] = af.create(
                None, fpsStr, None, None,
                lambda _, fps=fps: self._tabs.currentPage().changeFps(fps))

        for encoding in ALL_ENCODINGS:
            self._actions["in_%s" % encoding] = af.create(
                None, encoding, None, None,
                lambda _, enc = encoding: self._tabs.currentPage().changeInputEncoding(enc))

            self._actions["out_%s" % encoding] = af.create(
                None, encoding, None, None,
                lambda _, enc = encoding: self._tabs.currentPage().changeOutputEncoding(enc))

        for fmt in self._subtitleData.supportedFormats:
            self._actions[fmt.NAME] = af.create(
                None, fmt.NAME, None, None,
                lambda _, fmt = fmt: self._tabs.currentPage().changeSubFormat(fmt))


        self._actions["selectMovie"] = af.create(
            None, _("Select &movie"), None, "ctrl+m",
                lambda: self._tabs.currentPage().selectMovieFile())

        # SPF editor
        self._actions["spfEditor"] = af.create(
            None, _("Subtitle &Properties Editor"), None, None, self.openPropertyEditor)

        # View
        self._actions["togglePanel"] = af.create(
            None, _("Side &panel"), _("Show or hide left panel"), "F4", self._tabs.togglePanel)

        # Help
        self._actions["helpPage"] = af.create(
            None, _("&Help"), _("Open &help page"), "F1", self.openHelp)
        self._actions["aboutSubconvert"] = af.create(
            None, _("&About Subconvert"), None, None, self.openAboutDialog)

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

        subtitlesMenu = menubar.addMenu(_("&Subtitles"))
        subtitlesMenu.addAction(self._actions["undo"])
        subtitlesMenu.addAction(self._actions["redo"])
        subtitlesMenu.addSeparator()
        self._fpsMenu = subtitlesMenu.addMenu(_("&Frames per second"))
        for fps in FPS_VALUES:
            self._fpsMenu.addAction(self._actions[str(fps)])
        self._subFormatMenu = subtitlesMenu.addMenu(_("Subtitles forma&t"))
        for fmt in self._subtitleData.supportedFormats:
            self._subFormatMenu.addAction(self._actions[fmt.NAME])
        self._inputEncodingMenu = subtitlesMenu.addMenu(_("Input &encoding"))
        self._outputEncodingMenu = subtitlesMenu.addMenu(_("&Output encoding"))
        for encoding in ALL_ENCODINGS:
            self._inputEncodingMenu.addAction(self._actions["in_%s" % encoding])
            self._outputEncodingMenu.addAction(self._actions["out_%s" % encoding])
        subtitlesMenu.addAction(self._actions["selectMovie"])

        viewMenu = menubar.addMenu(_("&View"))
        viewMenu.addAction(self._actions["togglePanel"])

        toolsMenu = menubar.addMenu(_("&Tools"))
        toolsMenu.addAction(self._actions["spfEditor"])

        helpMenu = menubar.addMenu(_("&Help"))
        helpMenu.addAction(self._actions["helpPage"])
        helpMenu.addAction(self._actions["aboutSubconvert"])

    def __initShortcuts(self):
        self.addAction(self._actions["nextTab"])
        self.addAction(self._actions["previousTab"])
        self.addAction(self._actions["closeTab"])

    def __getAllSubExtensions(self):
        formats = self._subtitleData.supportedFormats
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
        self._subtitleData.setCleanState(filePath)
        self.__updateMenuItemsState()

    def __updateWindowTitle(self):
        tab = self._tabs.currentPage()
        if tab.isStatic:
            self.setWindowTitle("Subconvert")
        else:
            self.setWindowTitle("%s - Subconvert" % tab.name)

    def _openFiles(self, paths, encoding):
        unsuccessfullFiles = []
        for filePath in paths:
            # TODO: separate reading file and adding to the list.
            # TODO: there should be readDataFromFile(filePath, properties=None),
            # TODO: which should set default properties from Subtitle Properties File
            command = NewSubtitles(filePath, encoding)
            try:
                self._subtitleData.execute(command)
            except DoubleFileEntry:
                pass # file already opened
            except Exception as e:
                log.error(str(e))
                unsuccessfullFiles.append("%s: %s" % (filePath, str(e)))
        if len(unsuccessfullFiles) > 0:
            dialog = CannotOpenFilesMsg(self)
            dialog.setFileList(unsuccessfullFiles)
            dialog.exec()

    @pyqtSlot(bool)
    @pyqtSlot(int)
    @pyqtSlot(str)
    def __updateMenuItemsState(self):
        tab = self._tabs.currentPage()
        dataAvailable = self._subtitleData.count() != 0
        anyTabOpen = tab is not None
        tabIsStatic = tab.isStatic if anyTabOpen else False
        if tabIsStatic:
            cleanState = False
        else:
            cleanState = tab.history.isClean()

        self._actions["saveAllFiles"].setEnabled(dataAvailable)
        self._actions["saveFile"].setEnabled(anyTabOpen and not tabIsStatic and not cleanState)
        self._actions["saveFileAs"].setEnabled(anyTabOpen and not tabIsStatic)

        self._actions["selectMovie"].setEnabled(anyTabOpen and not tabIsStatic)
        self._fpsMenu.setEnabled(anyTabOpen and not tabIsStatic)
        self._subFormatMenu.setEnabled(anyTabOpen and not tabIsStatic)
        self._inputEncodingMenu.setEnabled(anyTabOpen and not tabIsStatic)
        self._outputEncodingMenu.setEnabled(anyTabOpen and not tabIsStatic)

        self._actions["undo"].setEnabled(anyTabOpen and not tabIsStatic and tab.history.canUndo())
        self._actions["redo"].setEnabled(anyTabOpen and not tabIsStatic and tab.history.canRedo())

    def handleArgs(self, args):
        self._openFiles(args.files, args.inputEncoding)

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
            self._openFiles(filenames, encoding)


    @pyqtSlot()
    def saveFile(self, newFilePath = None):
        currentTab = self._tabs.currentPage()
        try:
            self._writeFile(currentTab.filePath, newFilePath)
        except SubFileError as msg:
            dialog = QMessageBox(self)
            dialog.setIcon(QMessageBox.Critical)
            dialog.setWindowTitle(_("Couldn't save file"))
            dialog.setText(str(msg))
            dialog.exec()

    @pyqtSlot()
    def saveFileAs(self):
        fileDialog = FileDialog(
            parent = self,
            caption = _('Save as...'),
            directory = self._settings.getLatestDirectory()
        )

        currentTab = self._tabs.currentPage()

        fileDialog.addFormats(self._subtitleData.supportedFormats)
        fileDialog.setSubFormat(currentTab.outputFormat)
        fileDialog.addEncodings(False)
        fileDialog.setEncoding(currentTab.outputEncoding)
        fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        fileDialog.setFileMode(QFileDialog.AnyFile)

        if fileDialog.exec():
            data = currentTab.data

            outputFormat = fileDialog.getSubFormat()
            outputEncoding = fileDialog.getEncoding() # user can overwrite previous output encoding

            if data.outputFormat != outputFormat or data.outputEncoding != outputEncoding:
                # save user changes
                data.outputFormat = outputFormat
                data.outputEncoding = outputEncoding
                command = ChangeData(currentTab.filePath, data, _("Output data change"))
                self._subtitleData.execute(command)

            newFileName = fileDialog.selectedFiles()[0]
            self.saveFile(newFileName)
            self._settings.setLatestDirectory(os.path.dirname(newFileName))

    def saveAll(self):
        dialog = MessageBoxWithList(self)
        dialog.setIcon(QMessageBox.Critical)


        # TODO
        # When asked to save file, it should be should checked if it's parsed and parse it if it's
        # not (in future the parsing moment might be moved to increase responsibility when opening
        # a lot of files - i.e. only a file list will be printed and files will be actually parsed
        # on their first use (e.g. on tab open, fps change etc.). I'll have to think about it).
        # END OF TODO
        for filePath in self._tabs.fileList.filePaths:
            try:
                if not self._subtitleData.isCleanState(filePath):
                    self._writeFile(filePath)
            except SubFileError as msg:
                dialog.addToList(str(msg))

        if dialog.listCount() > 0:
            dialog.setWindowTitle(P_(
                "Error on saving a file",
                "Error on saving files",
                len(self.listCount())
                ))
            dialog.setText(P_(
                "Following error occured when trying to save a file:",
                "Following errors occured when trying to save files:",
                len(self.listCount())
                ))
            dialog.exec()

    def undo(self):
        currentTab = self._tabs.currentPage()
        currentTab.history.undo()

    def redo(self):
        currentTab = self._tabs.currentPage()
        currentTab.history.redo()

    def openPropertyEditor(self):
        editor = PropertyFileEditor(self._subtitleData.supportedFormats, self)
        editor.exec()

    def openAboutDialog(self):
        spacer = QSpacerItem(650, 0)
        dialog = QMessageBox(self)
        dialog.setIconPixmap(QPixmap(":/img/icons/256x256/subconvert.png"))
        dialog.setWindowTitle(_("About Subconvert"))
        dialog.setText(aboutText)

        dialogLayout = dialog.layout()
        dialogLayout.addItem(spacer, dialogLayout.rowCount(), 0, 1, dialogLayout.columnCount())
        dialog.exec()

    def openHelp(self):
        url = "https://github.com/mgoral/subconvert/wiki"
        if QDesktopServices.openUrl(QUrl(url)) is False:
            dialog = QMessageBox(self)
            dialog.setIcon(QMessageBox.Critical)
            dialog.setWindowTitle(_("Couldn't open URL"))
            dialog.setText(_("""Failed to open URL: <a href="%(url)s">%(url)s</a>.""") % 
                {"url": url})
            dialog.exec()