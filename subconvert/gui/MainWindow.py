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
from subconvert.gui.DataModel import DataController
from subconvert.utils.SubFile import File

log = logging.getLogger('Subconvert.%s' % __name__)

class MainWindow(QtGui.QMainWindow):
    #subExtensions = "*.txt *.srt"

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
        self.tabs = SubtitleWindow.SubTabWidget(self._subtitleData)
        self.fileDialog = QtGui.QFileDialog
        self.directory = os.environ['HOME'] # TODO: read from config

        mainLayout.addWidget(self.tabs)

        self.__initMenuBar()

        self.statusBar()
        self.menuBar()

        self.mainWidget.setLayout(mainLayout)
        self.setWindowTitle('Subconvert') # TODO: current file path

    def __initMenuBar(self):
        menubar = self.menuBar()

        openLogAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-open'),
            _('&Open File'), self)
        openLogAction.setStatusTip(_("Open log file in current tab."))
        openLogAction.setShortcut('ctrl+o')    # TODO: read this from settings
        openLogAction.triggered.connect(self.openFile)

        exitApp= QtGui.QAction(QtGui.QIcon.fromTheme('application-exit'),
            _('&Exit'), self)
        exitApp.setStatusTip(_("Exit Subconvert"))
        exitApp.triggered.connect(QtGui.qApp.quit)

        fileMenu = menubar.addMenu(_('&File'))
        fileMenu.addAction(openLogAction)
        fileMenu.addAction(exitApp)

    def __getAllSubExtensions(self):
        formats = SubFormat.__subclasses__()
        exts = [_('Default')]
        exts.extend(set([ f.EXTENSION for f in formats ]))
        exts.sort()
        return exts

    def __createSubtitles(self, file_):
        # TODO: fetch fps and encoding from user input (e.g. commandline options, settings, etc)
        fps = 25
        encoding = None
        fileContent = file_.read(encoding)
        subtitles = self._parser.parse(fileContent)
        return subtitles

    def __addFile(self, filePath):
        if not self._subtitleData.fileExists(filePath):
            try:
                file_ = File(filePath)
            except IOError as msg:
                log.error(msg)
                return
            subtitles = self.__createSubtitles(file_)
            self._subtitleData.addFile(filePath, subtitles)

    def openFile(self):
        sub_extensions = self.__getAllSubExtensions()
        str_sub_exts = ' '.join(['*.%s' % ext for ext in sub_extensions[1:]])
        filenames = self.fileDialog.getOpenFileNames(
            parent = self,
            caption = _('Open file'),
            directory = self.directory,
            filter = _("Subtitles (%s);;All files (*.*)") % str_sub_exts)
        try:
            self.directory = os.path.split(filenames[0])[0]
        except IndexError:
            pass    # Normal error when hitting "Cancel"
        for filePath in filenames:
            self.__addFile(filePath)


