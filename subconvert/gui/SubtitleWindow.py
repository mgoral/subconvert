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

from PyQt4.QtGui import QWidget, QFrame, QVBoxLayout, QGridLayout, QTabBar, QStackedWidget
from PyQt4.QtGui import QIcon, QListWidgetItem, QTableView, QHeaderView, QSplitter
from PyQt4.QtGui import QStandardItemModel, QStandardItem
from PyQt4.QtCore import pyqtSignal, pyqtSlot, Qt

from subconvert.gui.Detail import ClickableListWidget

import subconvert.resources

log = logging.getLogger('subconvert.%s' % __name__)

class SubTabWidget(QWidget):
    _tabChanged = pyqtSignal(int, name = "tabChanged")

    def __init__(self, subtitleData, parent = None):
        super(SubTabWidget, self).__init__(parent)
        self._subtitleData = subtitleData
        self.__initTabWidget()

    def __initTabWidget(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        #TabBar
        self.tabBar = QTabBar(self)

        # Splitter (bookmarks + pages)
        self.splitter = QSplitter(self)

        # TODO: leftPanel is left so there might be displayed e.g. some information about currently
        # focused file
        self.leftPanel = QWidget()
        leftLayout = QVBoxLayout()
        leftLayout.setMargin(0)
        self.leftPanel.setLayout(leftLayout)

        self.rightPanel = QWidget()
        rightLayout = QGridLayout()
        rightLayout.setMargin(0)
        self.rightPanel.setLayout(rightLayout)

        self._mainTab = SubtitleTab(_("Subtitles"), self._subtitleData, self)

        self.pages = QStackedWidget(self)
        rightLayout.addWidget(self.pages, 0, 0)

        self.tabBar.addTab(self._mainTab.name)
        self.pages.addWidget(self._mainTab)

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
        self._mainTab.requestOpen.connect(self.openTab)

        self.setLayout(mainLayout)


    def __addTab(self, filePath):
        """Returns existing tab index. Creates a new one if it isn't opened and returns its index
        otherwise."""
        for i in range(self.tabBar.count()):
            widget = self.pages.widget(i)
            if not widget.isStatic and filePath == widget.filePath:
                return i
        tab = SubtitleEditor(filePath, self._subtitleData, self.pages)
        # FIXME: too many tab-change signals
        newIndex = self.tabBar.addTab(tab.name)
        self.pages.addWidget(tab)
        return newIndex

    def __drawSplitterHandle(self, index):
        splitterHandle = self.splitter.handle(index)

        splitterLayout = QVBoxLayout(splitterHandle)
        splitterLayout.setSpacing(0)
        splitterLayout.setMargin(0)

        line = QFrame(splitterHandle)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        splitterLayout.addWidget(line)
        splitterHandle.setLayout(splitterLayout)

    @pyqtSlot(str, bool)
    def openTab(self, filePath, background=False):
        if self._subtitleData.fileExists(filePath):
            tabIndex = self.__addTab(filePath)
            if background is False:
                self.showTab(tabIndex)
        else:
            log.error(_("SubtitleEditor not created for %s!" % filePath))

    @pyqtSlot(int)
    def closeTab(self, index):
        if not self.tab(index).isStatic:
            widgetToRemove = self.pages.widget(index)
            self.tabBar.removeTab(index)
            self.pages.removeWidget(widgetToRemove)
            widgetToRemove.close()
            # FIXME: too many tab-change signals
            # Hack
            # when last tab is closed, tabBar should emit tabCloseRequested and then currentChanged.
            # Unfortunately it emits these signals the other way round and when clients receive
            # self.tabChanged, they have no possibility to know if there's no tab opened. This hack
            # will inform them additionaly when last tab is closed.
            if self.currentIndex() == -1:
                self._tabChanged.emit(self.currentIndex())

    def count(self):
        return self.tabBar.count()

    def currentIndex(self):
        return self.tabBar.currentIndex()

    def currentPage(self):
        return self.pages.currentWidget()

    @pyqtSlot(int, int)
    def moveTab(self, fromIndex, toIndex):
        fromWidget = self.pages.widget(fromIndex)
        toWidget = self.pages.widget(toIndex)
        if fromWidget.isStatic or toWidget.isStatic:
            self.tabBar.blockSignals(True) # signals would cause infinite recursion
            self.tabBar.moveTab(toIndex, fromIndex)
            self.tabBar.blockSignals(False)
            return
        else:
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

    @pyqtSlot(int)
    def showTab(self, index):
        # FIXME: too many tab-change signals
        showWidget = self.pages.widget(index)
        if showWidget:
            self.pages.setCurrentWidget(showWidget)
            self.tabBar.setCurrentIndex(index)
            self._tabChanged.emit(index)

    def tab(self, index):
        return self.pages.widget(index)

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

class SubtitleTab(SubTab):
    requestOpen = pyqtSignal(str, bool)

    def __init__(self, name, subtitleData, parent = None):
        super(SubtitleTab, self).__init__(name, True, parent)
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        self.__fileList = ClickableListWidget()
        mainLayout.addWidget(self.__fileList)

        self.__fileList.mouseButtonDoubleClicked.connect(self.handleDoubleClick)
        self.__fileList.mouseButtonClicked.connect(self.handleClick)
        subtitleData.fileAdded.connect(self.addFile)

        self.setLayout(mainLayout)

    @pyqtSlot(str)
    def addFile(self, filePath):
        icon = QIcon(":/img/initial_list.png")
        item = QListWidgetItem(icon, filePath)
        item.setToolTip(filePath)
        self.__fileList.addItem(item)

    def removeFile(self):
        item = self.__fileList.takeItem(self.__fileList.currentRow())
        item = None

    def getCurrentFile(self):
        return self.__fileList.currentItem()

    def handleClick(self, button):
        item = self.__fileList.currentItem()
        if button == Qt.MiddleButton:
            self.requestOpen.emit(item.text(), True)

    def handleDoubleClick(self, button):
        item = self.__fileList.currentItem()
        if button == Qt.LeftButton:
            self.requestOpen.emit(item.text(), False)

class SubtitleEditor(SubTab):
    def __init__(self, filePath, subtitleData, parent = None):
        name = os.path.split(filePath)[1]
        super(SubtitleEditor, self).__init__(name, False, parent)

        self._filePath = filePath # for __eq__
        self._subtitleData = subtitleData

        grid = QGridLayout(self)

        self._model = QStandardItemModel(0, 3, self)
        self._model.setHorizontalHeaderLabels([_("Begin"), _("End"), _("Subtitle")])
        self.subList = QTableView(self)
        self.subList.setModel(self._model)

        self.subList.horizontalHeader().setResizeMode(2, QHeaderView.Stretch)

        grid.setSpacing(10)
        grid.addWidget(self.subList, 0, 0)

        self.updateSubtitles()

        self.setLayout(grid)

        # Some signals
        self._subtitleData.fileChanged.connect(self.fileChanged)

    @pyqtSlot(str)
    def fileChanged(self, filePath):
        if filePath == self._filePath:
            self.updateSubtitles()

    def updateSubtitles(self):
        data = self._subtitleData.data(self._filePath)
        self._subtitles = data.subtitles
        self._model.removeRows(0, self._model.rowCount())
        for sub in self._subtitles:
            timeStart = QStandardItem(sub.start.toStr())
            timeEnd = QStandardItem(sub.end.toStr())
            text = QStandardItem(sub.text)
            self._model.appendRow([timeStart, timeEnd, text])

    def saveContent(self):
        # TODO: check if subtitleData.fileExists(filePath) ???
        self._subtitleData.fileChanged.disconnect(self.fileChanged)
        data = self._subtitleData.data(self._filePath)
        data.subtitles = self._subtitles
        self._subtitleData.update(self._filePath, data)
        self._subtitleData.fileChanged.connect(self.fileChanged)

    @property
    def filePath(self):
        return self._filePath

    @property
    def subtitles(self):
        return self._subtitles
