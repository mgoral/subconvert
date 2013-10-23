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
import logging

from PyQt4.QtGui import QWidget, QFrame, QHBoxLayout, QVBoxLayout, QGridLayout, QTabBar
from PyQt4.QtGui import  QSplitter, QStackedWidget
from PyQt4.QtCore import pyqtSignal, pyqtSlot

from subconvert.utils.Locale import _
from subconvert.utils.SubFile import File
from subconvert.gui.DataModel import SubtitleData
from subconvert.gui.SubtitleTabs import FileList, SubtitleEditor

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

        self._mainTab = FileList(_("Subtitles"), self._subtitleData, self)

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
        tab = SubtitleEditor(filePath, self._subtitleData, self)
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

            # Try to update current tab.
            showWidget.updateTab()

            self._tabChanged.emit(index)

    def tab(self, index):
        return self.pages.widget(index)

    @property
    def fileList(self):
        return self._mainTab

