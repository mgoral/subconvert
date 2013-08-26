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

from PyQt4 import QtGui, QtCore, Qt

import subconvert.resources
from subconvert.parsing.Core import SubManager, SubParser, SubConverter
from subconvert.parsing.Formats import *
from subconvert.utils.SubFile import File

log = logging.getLogger('subconvert.%s' % __name__)

class SubTabWidget(QtGui.QWidget):
    def __init__(self, parent = None):
        super(SubTabWidget, self).__init__(parent)
        self.__createParser()
        self.__initTabWidget()
        self._fileStorage = {
            # File(filePath): SubManager
        }

    def __createParser(self):
        self._parser = SubParser()
        for Format in SubFormat.__subclasses__():
            self._parser.registerFormat(Format)

    def __initTabWidget(self):
        mainLayout = QtGui.QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        #TabBar
        self.tabBar = QtGui.QTabBar(self)

        # Splitter (bookmarks + pages)
        self.splitter = QtGui.QSplitter(self)

        self.leftPanel = QtGui.QWidget()
        leftLayout = QtGui.QVBoxLayout()
        leftLayout.setMargin(0)
        self.leftPanel.setLayout(leftLayout)

        self.rightPanel = QtGui.QWidget()
        rightLayout = QtGui.QGridLayout()
        rightLayout.setMargin(0)
        self.rightPanel.setLayout(rightLayout)

        self.sidePanel = SidePanel(self)
        leftLayout.addWidget(self.sidePanel)

        self.pages = QtGui.QStackedWidget()
        rightLayout.addWidget(self.pages, 0, 0)

        self.splitter.addWidget(self.leftPanel)
        self.splitter.addWidget(self.rightPanel)
        self.__drawSplitterHandle(1)

        # Setting widgets
        mainLayout.addWidget(self.tabBar)
        mainLayout.addWidget(self.splitter)

        # Widgets settings
        self.tabBar.setMovable(True)
        self.tabBar.setTabsClosable(True)
        self.tabBar.setExpanding(False)

        # Don't resize left panel if it's not needed
        leftPanelIndex = self.splitter.indexOf(self.leftPanel)
        rightPanelIndex = self.splitter.indexOf(self.rightPanel)
        self.splitter.setStretchFactor(leftPanelIndex, 0)
        self.splitter.setStretchFactor(rightPanelIndex, 1)

        # Some signals
        self.tabBar.currentChanged.connect(self.showTab)
        self.tabBar.tabCloseRequested.connect(self.closeTab)
        self.tabBar.tabMoved.connect(self.moveTab)
        self.sidePanel.requestOpen.connect(self.showEditor)

        self.setLayout(mainLayout)

    def __addTab(self, filePath, subtitles):
        """Returns existing tab index. Creates a new one if it isn't opened and returns its index
        otherwise."""
        for i in range(self.tabBar.count()):
            if filePath == self.pages.widget(i).filePath:
                return i
        tab = SubtitleEditor(filePath, subtitles)
        newIndex = self.tabBar.addTab(filePath)
        self.pages.addWidget(tab)
        return newIndex

    def __drawSplitterHandle(self, index):
        splitterHandle = self.splitter.handle(index)

        splitterLayout = QtGui.QVBoxLayout(splitterHandle)
        splitterLayout.setSpacing(0)
        splitterLayout.setMargin(0)

        line = QtGui.QFrame(splitterHandle)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        splitterLayout.addWidget(line)
        splitterHandle.setLayout(splitterLayout)

    def __createSubtitles(self, file_):
        # TODO: fetch fps and encoding from user input (e.g. commandline options, settings, etc)
        fps = 25
        encoding = None
        fileContent = file_.read(encoding)
        subtitles = self._parser.parse(fileContent)
        return subtitles

    @QtCore.pyqtSlot(str)
    def showEditor(self, filePath):
        subtitles = self._fileStorage.get(File(filePath))
        if subtitles is not None:
            self.showTab(self.__addTab(filePath, subtitles))
        else:
            log.error(_("Converter not created for %s!" % filePath))


    def addFile(self, filePath, icon=None):
        try:
            file_ = File(filePath)
        except IOError as msg:
            log.error(msg)
            return

        subtitles = self._fileStorage.get(file_)
        if subtitles is None:
            subtitles = self.__createSubtitles(file_)
            self._fileStorage[file_] = subtitles
            self.sidePanel.addFile(filePath)

    def count(self):
        return self.tabBar.count()

    def closeTab(self, index):
        widgetToRemove = self.pages.widget(index)
        self.tabBar.removeTab(index)
        self.pages.removeWidget(widgetToRemove)
        widgetToRemove.close()

    def currentIndex(self):
        return self.tabBar.currentIndex()

    def currentPage(self):
        return self.pages.currentWidget()

    def moveTab(self, fromIndex, toIndex):
        fromWidget = self.pages.widget(fromIndex)
        toWidget = self.pages.widget(toIndex)

        self.pages.removeWidget(fromWidget)
        self.pages.removeWidget(toWidget)

        if fromIndex < toIndex:
            self.pages.insertWidget(fromIndex, toWidget)
            self.pages.insertWidget(toIndex, fromWidget)
        else:
            self.pages.insertWidget(toIndex, fromWidget)
            self.pages.insertWidget(fromIndex, toWidget)

        # Hack
        # Qt changes tabs during mouse drag and dropping. The next line is added
        # to prevent it.
        self.showTab(self.tabBar.currentIndex())

    def showTab(self, index):
        showWidget = self.pages.widget(index)
        self.pages.setCurrentWidget(showWidget)
        self.tabBar.setCurrentIndex(index)

class SidePanel(QtGui.QWidget):
    requestOpen = QtCore.pyqtSignal(str)

    def __init__(self, parent = None):
        super(SidePanel, self).__init__(parent)
        self.__initSidePanel()


    def __initSidePanel(self):
        mainLayout = QtGui.QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        self.__fileList = QtGui.QListWidget()
        mainLayout.addWidget(self.__fileList)

        self.__fileList.itemDoubleClicked.connect(self.informFileRequest)

        self.setLayout(mainLayout)

    def addFile(self, filePath):
        icon = QtGui.QIcon(":/img/initial_list.png")
        item = QtGui.QListWidgetItem(icon, filePath)
        item.setToolTip(filePath)
        self.__fileList.addItem(item)

    def removeFile(self):
        item = self.__fileList.takeItem(self.__fileList.currentRow())
        item = None

    def getCurrentFile(self):
        return self.__fileList.currentItem()

    def informFileRequest(self):
        item = self.__fileList.currentItem()
        self.requestOpen.emit(item.text())

class SubtitleEditor(QtGui.QWidget):
    def __init__(self, filePath, subtitles, parent = None):
        super(SubtitleEditor, self).__init__(parent)

        self._filePath = filePath # for __eq__
        self._subtitles = subtitles

        grid = QtGui.QGridLayout(self)

        self.model = QtGui.QStandardItemModel(0, 3)
        self.model.setHorizontalHeaderLabels([_("Begin"), _("End"), _("Subtitle")])
        self.subList = QtGui.QTableView(self)
        self.subList.setModel(self.model)

        #self.subList.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        #self.subList.horizontalHeader().resizeSection(2,600)
        self.subList.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        #self.subList.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Interactive)

        grid.setSpacing(10)
        grid.addWidget(self.subList, 0, 0)

        for sub in self._subtitles:
            timeStart = QtGui.QStandardItem(sub.start.toStr())
            timeEnd = QtGui.QStandardItem(sub.end.toStr())
            text = QtGui.QStandardItem(sub.text)
            self.model.appendRow([timeStart, timeEnd, text])

        self.setLayout(grid)

    def insertSubtitle(self, filePath):
        pass

    @property
    def filePath(self):
        return self._filePath

    @property
    def subtitles(self):
        return self._subtitles
