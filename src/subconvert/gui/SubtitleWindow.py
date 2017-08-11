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

from PyQt5.QtWidgets import QWidget, QFrame, QHBoxLayout, QVBoxLayout, QGridLayout, QTabBar
from PyQt5.QtWidgets import  QSplitter, QStackedWidget
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QByteArray

from subconvert.utils.Locale import _
from subconvert.utils.SubFile import File
from subconvert.utils.SubSettings import SubSettings
from subconvert.gui.SubtitleTabs import FileList, SubtitleEditor
from subconvert.gui.SubtitleCommands import *
from subconvert.gui.ToolBox import ToolBox
from subconvert.gui.tools.Synchronizer import Synchronizer
from subconvert.gui.tools.Details import Details
from subconvert.gui.tools.History import History

import subconvert.resources

log = logging.getLogger('Subconvert.%s' % __name__)

class SubTabWidget(QWidget):
    _tabChanged = pyqtSignal(int, name = "tabChanged")

    def __init__(self, subtitleData, videoWidget, parent = None):
        super(SubTabWidget, self).__init__(parent)
        self._subtitleData = subtitleData
        self.__initTabWidget(videoWidget)

    def __initTabWidget(self, videoWidget):
        settings = SubSettings()

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        #TabBar
        self.tabBar = QTabBar(self)

        # Splitter (bookmarks + pages)
        self.splitter = QSplitter(self)
        self.splitter.setObjectName("sidebar_splitter")

        self._toolbox = ToolBox(self._subtitleData, self)
        self._toolbox.setObjectName("sidebar")
        self._toolbox.setMinimumWidth(100)

        self._toolbox.addTool(Details(self._subtitleData, self))
        self._toolbox.addTool(Synchronizer(videoWidget, self._subtitleData, self))
        self._toolbox.addTool(History(self))

        self.rightWidget = QWidget()
        rightLayout = QGridLayout()
        rightLayout.setContentsMargins(0, 0, 0, 0)
        self.rightWidget.setLayout(rightLayout)

        self._mainTab = FileList(_("Subtitles"), self._subtitleData, self)

        self.pages = QStackedWidget(self)
        rightLayout.addWidget(self.pages, 0, 0)

        self.tabBar.addTab(self._mainTab.name)
        self.pages.addWidget(self._mainTab)

        self.splitter.addWidget(self._toolbox)
        self.splitter.addWidget(self.rightWidget)
        self.__drawSplitterHandle(1)

        # Setting widgets
        mainLayout.addWidget(self.tabBar)
        mainLayout.addWidget(self.splitter)

        # Widgets settings
        self.tabBar.setMovable(True)
        self.tabBar.setTabsClosable(True)
        self.tabBar.setExpanding(False)

        # Don't resize left panel if it's not needed
        leftWidgetIndex = self.splitter.indexOf(self._toolbox)
        rightWidgetIndex = self.splitter.indexOf(self.rightWidget)

        self.splitter.setStretchFactor(leftWidgetIndex, 0)
        self.splitter.setStretchFactor(rightWidgetIndex, 1)
        self.splitter.setCollapsible(leftWidgetIndex, False)
        self.splitter.setSizes([250])

        # Some signals
        self.tabBar.currentChanged.connect(self.showTab)
        self.tabBar.tabCloseRequested.connect(self.closeTab)
        self.tabBar.tabMoved.connect(self.moveTab)
        self._mainTab.requestOpen.connect(self.openTab)
        self._mainTab.requestRemove.connect(self.removeFile)

        self.tabChanged.connect(lambda i: self._toolbox.setContentFor(self.tab(i)))

        self.setLayout(mainLayout)

    def __addTab(self, filePath):
        """Returns existing tab index. Creates a new one if it isn't opened and returns its index
        otherwise."""
        for i in range(self.tabBar.count()):
            widget = self.pages.widget(i)
            if not widget.isStatic and filePath == widget.filePath:
                return i
        tab = SubtitleEditor(filePath, self._subtitleData, self)
        newIndex = self.tabBar.addTab(self._createTabName(tab.name, tab.history.isClean()))
        tab.history.cleanChanged.connect(
            lambda clean: self._cleanStateForFileChanged(filePath, clean))
        self.pages.addWidget(tab)
        return newIndex

    def __drawSplitterHandle(self, index):
        splitterHandle = self.splitter.handle(index)

        splitterLayout = QVBoxLayout(splitterHandle)
        splitterLayout.setSpacing(0)
        splitterLayout.setContentsMargins(0, 0, 0, 0)

        line = QFrame(splitterHandle)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        splitterLayout.addWidget(line)
        splitterHandle.setLayout(splitterLayout)

    def _createTabName(self, name, cleanState):
        if cleanState is True:
            return name
        else:
            return "%s +" % name

    def _cleanStateForFileChanged(self, filePath, cleanState):
        page = self.tabByPath(filePath)
        if page is not None:
            for i in range(self.tabBar.count()):
                if self.tabBar.tabText(i)[:len(page.name)] == page.name:
                    self.tabBar.setTabText(i, self._createTabName(page.name, cleanState))
                    return

    def saveWidgetState(self, settings):
        settings.setState(self.splitter, self.splitter.saveState())
        settings.setHidden(self._toolbox, self._toolbox.isHidden())

    def restoreWidgetState(self, settings):
        self.showPanel(not settings.getHidden(self._toolbox))

        splitterState = settings.getState(self.splitter)
        if not splitterState.isEmpty():
            self.splitter.restoreState(settings.getState(self.splitter))

    @pyqtSlot(str, bool)
    def openTab(self, filePath, background=False):
        if self._subtitleData.fileExists(filePath):
            tabIndex = self.__addTab(filePath)
            if background is False:
                self.showTab(tabIndex)
        else:
            log.error(_("SubtitleEditor not created for %s!" % filePath))

    @pyqtSlot(str)
    def removeFile(self, filePath):
        tab = self.tabByPath(filePath)
        command = RemoveFile(filePath)
        if tab is not None:
            index = self.pages.indexOf(tab)
            if self.closeTab(index):
                self._subtitleData.execute(command)
        else:
            self._subtitleData.execute(command)


    @pyqtSlot(int)
    def closeTab(self, index):
        tab = self.tab(index)
        if tab.canClose():
            widgetToRemove = self.pages.widget(index)
            self.tabBar.removeTab(index)
            self.pages.removeWidget(widgetToRemove)
            widgetToRemove.deleteLater()
            return True
        return False


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
        showWidget = self.pages.widget(index)
        if showWidget:
            self.pages.setCurrentWidget(showWidget)
            self.tabBar.blockSignals(True)
            self.tabBar.setCurrentIndex(index)
            self.tabBar.blockSignals(False)

            # Try to update current tab.
            showWidget.updateTab()

            self._tabChanged.emit(index)

    def showPanel(self, val):
        if val is True:
            self._toolbox.show()
        else:
            self._toolbox.hide()

    def togglePanel(self):
        if self._toolbox.isHidden():
            self._toolbox.show()
        else:
            self._toolbox.hide()

    def tab(self, index):
        return self.pages.widget(index)

    def tabByPath(self, path):
        for i in range(self.pages.count()):
            page = self.tab(i)
            if not page.isStatic and page.filePath == path:
                return page
        return None

    @property
    def fileList(self):
        return self._mainTab

