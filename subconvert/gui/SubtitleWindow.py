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

import subparser.Convert as Convert
import subutils.path as subpath
from subutils import FileUtils

log = logging.getLogger('subconvert.%s' % __name__)

class SubTabWidget(QtGui.QWidget):
    def __init__(self, parent = None):
        super(SubTabWidget, self).__init__(parent)
        self.__initTabWidget()

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
        self.sidePanel.requestOpen.connect(self.showConverter)

        self.setLayout(mainLayout)

    def __addTab(self, tab):
        """Returns existing tab index. Creates a new one if it isn't opened and returns its index
        otherwise."""
        for i in range(self.tabBar.count()):
            if tab == self.pages.widget(i):
                return i
        newIndex = self.tabBar.addTab(tab.name())
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

    @QtCore.pyqtSlot(Convert.SubConverter)
    def showConverter(self, converter):
        tab = SubtitleEditor(converter)
        self.showTab(self.__addTab(tab))

    def addFile(self, filePath, icon=None):
        self.sidePanel.addFile(filePath)
        #if icon is None:
        #    self.tabBar.addTab(filePath)
        #else:
        #    self.tabBar.addTab(icon, filePath)

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

    def renameTab(self, index, newName):
        self.tabBar.setTabText(index, newName)

    def showTab(self, index):
        showWidget = self.pages.widget(index)
        self.pages.setCurrentWidget(showWidget)
        self.tabBar.setCurrentIndex(index)

class SidePanel(QtGui.QWidget):
    requestOpen = QtCore.pyqtSignal(Convert.SubConverter)

    def __init__(self, parent = None):
        super(SidePanel, self).__init__(parent)
        self.converterManager = Convert.SubConverterManager()
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
        converter = self.converterManager.add(filePath)
        if not converter.isParsed():
            converter.parse(FileUtils.openFile(filePath))
            # FIXME: icon doesn't show up
            selfPath = subpath.get_dirname(__file__)
            icon = QtGui.QIcon(os.path.join(selfPath, "img/initial_list.png"))
            item = QtGui.QListWidgetItem(icon, filePath)
            item.setToolTip(converter.filePath())
            self.__fileList.addItem(item)
            return True
        return False

    def removeFile(self):
        item = self.__fileList.takeItem(self.__fileList.currentRow())
        self.converterManager.remove(item.text())
        item = None

    def getCurrentFile(self):
        return self.__fileList.currentItem()

    def informFileRequest(self):
        item = self.__fileList.currentItem()
        converter = self.converterManager.get(item.text())
        if converter is not None:
            self.requestOpen.emit(converter)
        else:
            log.error(_("No such converter created: %s") % item.text())

class SubtitleEditor(QtGui.QWidget):
    def __init__(self, converter, parent = None):
        super(SubtitleEditor, self).__init__(parent)

        self.__converter = converter

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

        for line in self.__converter.parsedLines:
            if line is not None:
                timeStart = QtGui.QStandardItem(line['sub']['time_from'].toStr())
                timeEnd = QtGui.QStandardItem(line['sub']['time_from'].toStr())
                text = QtGui.QStandardItem(line['sub']['text'])
                self.model.appendRow([timeStart, timeEnd, text])
                pass

        self.setLayout(grid)

    def insertSubtitle(self, filePath):
        pass

    def name(self):
        return self.__converter.originalFilePath

    def __eq__(self, other):
        return self.__converter == other.__converter
