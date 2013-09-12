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
import pkgutil
import encodings
import copy

from PyQt4.QtGui import QWidget, QFrame, QHBoxLayout, QVBoxLayout, QGridLayout, QTabBar
from PyQt4.QtGui import QIcon, QListWidgetItem, QTableView, QHeaderView, QSplitter, QStackedWidget
from PyQt4.QtGui import QStandardItemModel, QStandardItem, QComboBox, QSizePolicy, QMessageBox
from PyQt4.QtCore import pyqtSignal, pyqtSlot, Qt

from subconvert.utils import SubPath
from subconvert.utils.SubFile import File
from subconvert.gui.Detail import ClickableListWidget
from subconvert.gui.DataModel import SubtitleData

import subconvert.resources

log = logging.getLogger('subconvert.%s' % __name__)

t = gettext.translation(
    domain='subconvert',
    localedir=SubPath.getLocalePath(__file__),
    fallback=True)
gettext.install('subconvert')
_ = t.gettext

# define globally to avoid mistakes
AUTO_ENCODING_STR = _("[Auto]")

def pythonEncodings():
    # http://stackoverflow.com/questions/1707709/list-all-the-modules-that-are-part-of-a-python-package/1707786#1707786
    false_positives = set(["aliases"])
    found = set(name for imp, name, ispkg in pkgutil.iter_modules(encodings.__path__) if not ispkg)
    found.difference_update(false_positives)
    found = list(found)
    found.sort()
    return found

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

    @property
    def fileList(self):
        return self._mainTab

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

class FileList(SubTab):
    requestOpen = pyqtSignal(str, bool)

    def __init__(self, name, subtitleData, parent = None):
        super(FileList, self).__init__(name, True, parent)
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        self.__fileList = ClickableListWidget()
        mainLayout.addWidget(self.__fileList)

        self.__fileList.mouseButtonDoubleClicked.connect(self.handleDoubleClick)
        self.__fileList.mouseButtonClicked.connect(self.handleClick)
        self._subtitleData = subtitleData

        self.setLayout(mainLayout)

    def addFile(self, filePath):
        if not self._subtitleData.fileExists(filePath):
            data = self._subtitleData.createDataFromFile(filePath)
            icon = QIcon(":/img/initial_list.png")
            item = QListWidgetItem(icon, filePath)
            item.setToolTip(filePath)

            self._subtitleData.add(filePath, data)
            self.__fileList.addItem(item)

    def removeFile(self):
        item = self.__fileList.takeItem(self.__fileList.currentRow())
        item = None

    def getCurrentFile(self):
        return self.__fileList.currentItem()

    def handleClick(self, button):
        item = self.__fileList.currentItem()
        if item is not None and button == Qt.MiddleButton:
            self.requestOpen.emit(item.text(), True)

    def handleDoubleClick(self, button):
        item = self.__fileList.currentItem()
        if item is not None and button == Qt.LeftButton:
            self.requestOpen.emit(item.text(), False)

class SubtitleEditor(SubTab):
    def __init__(self, filePath, subtitleData, parent = None):
        name = os.path.split(filePath)[1]
        super(SubtitleEditor, self).__init__(name, False, parent)
        self.__initWidgets()

        self._filePath = filePath
        self._subtitleData = subtitleData

        self.updateSubtitles()

        # Some signals
        self._subtitleData.fileChanged.connect(self.fileChanged)
        self._inputEncodings.currentIndexChanged.connect(self.changeEncoding)

    def __initWidgets(self):
        minimalSizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Encodings combo box
        # TODO: show only encodings selected by user in preferences
        self._inputEncodings = QComboBox(self)
        self._inputEncodings.addItem(AUTO_ENCODING_STR)
        self._inputEncodings.addItems(pythonEncodings())
        self._inputEncodings.setToolTip(_("Change input file encoding"))
        self._inputEncodings.setEditable(True)

        # List of subtitles
        self._model = QStandardItemModel(0, 3, self)
        self._model.setHorizontalHeaderLabels([_("Begin"), _("End"), _("Subtitle")])
        self._subList = QTableView(self)
        self._subList.setModel(self._model)
        self._subList.horizontalHeader().setResizeMode(2, QHeaderView.Stretch)

        # Top toolbar
        toolbar = QHBoxLayout()
        toolbar.setAlignment(Qt.AlignLeft)
        toolbar.addWidget(self._inputEncodings)
        toolbar.addStretch(1)

        # Main layout
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.addLayout(toolbar, 0, 0, 1, 1) # stretch to the right
        grid.addWidget(self._subList, 1, 0)
        self.setLayout(grid)

    @pyqtSlot(str)
    def changeEncoding(self, index):
        encoding = self._inputEncodings.itemText(index)
        if encoding == AUTO_ENCODING_STR:
            file_ = File(self._filePath)
            encoding = file_.detectEncoding()

        # Operate on a copy so we can fallback to the old subtitles in case wrong encoding has been
        # chosen
        subtitlesCopy = copy.deepcopy(self._data.subtitles)
        try:
            for i, subtitle in enumerate(subtitlesCopy):
                encodedBits = subtitle.text.encode(self._data.inputEncoding)
                subtitlesCopy.changeSubText(i, encodedBits.decode(encoding))
        except UnicodeDecodeError:
            message = QMessageBox(
                QMessageBox.Warning,
                _("Decoding error"),
                _("Cannot decode subtitles to '%s' encoding.\nPlease try different encoding.") % encoding,
                QMessageBox.Ok, self
            )
            message.exec()
        except LookupError:
            message = QMessageBox(
                QMessageBox.Warning, _("Unknown encoding"), _("Unknown encoding: '%s'") % encoding,
                QMessageBox.Ok, self
            )
            message.exec()
            # TODO: turn of signal handling for a sec. and set previous encoding
            addedIncorrectEncodingIndex = self._inputEncodings.findText(encoding)
            self._inputEncodings.removeItem(addedIncorrectEncodingIndex)
        else:
            self._data.inputEncoding = encoding
            self._data.subtitles = subtitlesCopy
            self.refreshSubtitles()

    def fileChanged(self, filePath):
        if filePath == self._filePath:
            self.updateSubtitles()

    def refreshSubtitles(self):
        self._model.removeRows(0, self._model.rowCount())
        for sub in self._data.subtitles:
            timeStart = QStandardItem(sub.start.toStr())
            timeEnd = QStandardItem(sub.end.toStr())
            text = QStandardItem(sub.text)
            self._model.appendRow([timeStart, timeEnd, text])

    def updateSubtitles(self):
        self._data = self._subtitleData.data(self._filePath)
        self.refreshSubtitles()

    def saveContent(self):
        # TODO: check if subtitleData.fileExists(filePath) ???
        self._subtitleData.fileChanged.disconnect(self.fileChanged)
        self._subtitleData.update(self._filePath, self._data)
        self._subtitleData.fileChanged.connect(self.fileChanged)

    @property
    def filePath(self):
        return self._filePath

    @property
    def subtitles(self):
        return self._data.subtitles
