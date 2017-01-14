#-*- coding: utf-8 -*-

"""
Copyright (C) 2016 Michal Goral.

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

from abc import abstractmethod

from PyQt5.QtWidgets import QWidget, QLabel, QTabWidget, QVBoxLayout
from PyQt5.QtCore import Qt

from subconvert.utils.Locale import _

class ToolBox(QTabWidget):
    def __init__(self, subtitleData, parent=None):
        super().__init__(parent)
        self._subtitleData = subtitleData
        self.setMovable(True)

        self._subtitleData.fileRemoved.connect(self.removeContent)

    def setContentFor(self, widget):
        """Updates toolbox contents with a data corresponding to a given tab."""
        for i in range(self.count()):
            item = self.widget(i)
            if widget.isStatic:
                item.setStaticContent(widget)
            else:
                item.setContent(widget)

    def removeContent(self, path):
        for i in range(self.count()):
            item = self.widget(i)
            item.remove(path)

    def addTool(self, tool):
        self.addTab(tool, tool.name)


class Tool(QWidget):
    """Abstract base class for widgets to be used in custom Toolbox.
    Remimplement anything you like."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.setStaticContent()

    @property
    @abstractmethod
    def name(self):
        """Name of the tool displayed in a toolbox."""
        return "Generic tool name"

    @abstractmethod
    def setContent(self, widget):
        """Set a content for dynamic widget (SubtitleEditor)."""
        pass

    def remove(self, path):
        """Cleanup action performed when widget (SubtitleEditor) with a given
        file path has been removed and is no longer accessible."""
        pass

    def clear(self):
        """Removes all child widgets."""
        layout = self.layout()
        for index in reversed(range(layout.count())):
            item = layout.takeAt(index)
            try:
                item.widget().deleteLater()
            except AttributeError:
                item = None

    def setStaticContent(self, widget=None):
        """Set content for static widget (FileList)."""
        self.clear()
        self.addTitle(_("No subtitle data"))
        self.addLabel(_("Open subtitles in a new tab to see their details."))
        self.addStretch()

    def addTitle(self, title):
        titleLabel = QLabel("<h3>%s</h3>" % title, self)
        titleLabel.setWordWrap(True)
        titleLabel.setTextFormat(Qt.RichText)
        self.layout().addWidget(titleLabel)

    def addLabel(self, text):
        label = QLabel(text, self)
        label.setWordWrap(True)
        self.layout().addWidget(label)

    def addStretch(self):
        self.layout().addStretch()
