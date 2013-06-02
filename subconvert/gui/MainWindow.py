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

from subconvert.parsing.Core import SubParser
from subconvert.gui import SubtitleWindow
from subconvert.utils import SubPath

log = logging.getLogger('Subconvert.%s' % __name__)

class MainWindow(QtGui.QMainWindow):
    #subExtensions = "*.txt *.srt"

    def __init__(self):
        super(MainWindow, self).__init__()

        #self.userSettings = QtCore.QSettings(QtCore.QSettings.IniFormat,
        #    QtCore.QSettings.UserScope, "logmaster", "rc")
        #self.windowSettings = QtCore.QSettings(QtCore.QSettings.IniFormat,
        #    QtCore.QSettings.UserScope, "logmaster", "window")

        self.__initGui()
        self.show()

    def __initGui(self):
        self.mainWidget = QtGui.QWidget(self)
        mainLayout = QtGui.QGridLayout()
        mainLayout.setContentsMargins(3, 3, 3, 3)

        self.setCentralWidget(self.mainWidget)

        self.tabs = SubtitleWindow.SubTabWidget()
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
        openLogAction.triggered.connect(self.fileOpen)

        exitApp= QtGui.QAction(QtGui.QIcon.fromTheme('application-exit'),
            _('&Exit'), self)
        exitApp.setStatusTip(_("Exit Subconvert"))
        exitApp.triggered.connect(QtGui.qApp.quit)

        fileMenu = menubar.addMenu(_('&File'))
        fileMenu.addAction(openLogAction)
        fileMenu.addAction(exitApp)

    def __getAllSubExtensions(self):
        classes = SubParser.__subclasses__()
        exts = [_('Default')]
        exts.extend(set([ c.__EXT__ for c in classes ]))
        exts.sort()
        return exts

    def fileOpen(self):
        self.openFile()

    # TODO: mere this with openTab and check what action is required (new tab or
    # open tab)
    # like this :
    # button = self.sender()
    #   if button == self.add_file
    #     ...
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
        for filepath in filenames:
            self.tabs.addFile(filepath)


