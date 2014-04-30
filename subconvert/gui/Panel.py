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

from PyQt4.QtGui import QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel, QTextEdit
from PyQt4.QtCore import Qt

from subconvert.utils.Locale import _

class SidePanel(QWidget):
    def __init__(self, subtitleData, parent = None):
        super().__init__(parent)
        self._filePath = None
        self._subtitleData = subtitleData
        self._initGui()
        self._createEmptyPanel()
        self._connectSignals()

    def _initGui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

    def _connectSignals(self):
        self._subtitleData.fileChanged.connect(self._updateFileInfo)

    def _createEmptyPanel(self):
        self.clear()
        self.addTitle(_("No subtitle data"))
        self.addLabel(_("Open subtitles in a new tab to see their details."))
        self.addStretch()

    def _createFileInfo(self, filePath, data):
        self.clear()

        dataGroup = QGroupBox(_("Subtitle details"), self)
        dataGroupLayout = QFormLayout()
        dataGroup.setLayout(dataGroupLayout)

        fileNameLabel = QLabel(os.path.split(filePath)[1], dataGroup)
        fileNameLabel.setToolTip(fileNameLabel.text())

        fpsLabel = QLabel(str(data.fps), dataGroup)
        fpsLabel.setToolTip(fpsLabel.text())

        formatLabel = QLabel(data.outputFormat.NAME, dataGroup)
        formatLabel.setToolTip(formatLabel.text())

        inEncodingLabel = QLabel(data.inputEncoding, dataGroup)
        inEncodingLabel.setToolTip(inEncodingLabel.text())

        outEncodingLabel = QLabel(data.outputEncoding, dataGroup)
        outEncodingLabel.setToolTip(outEncodingLabel.text())

        if data.videoPath is not None:
            videoLabel = QLabel(data.videoPath, dataGroup)
            videoLabel.setToolTip(videoLabel.text())
        else:
            videoLabel = QLabel("-", dataGroup)
            videoLabel.setToolTip(_("No video"))

        dataGroupLayout.addRow(_("File name:"), fileNameLabel)
        dataGroupLayout.addRow(_("Video:"), videoLabel)
        dataGroupLayout.addRow(_("FPS:"), fpsLabel)
        dataGroupLayout.addRow(_("Format:"), formatLabel)
        dataGroupLayout.addRow(_("Input encoding:"), inEncodingLabel)
        dataGroupLayout.addRow(_("Output encoding:"), outEncodingLabel)

        mainLayout = self.layout()
        mainLayout.addWidget(dataGroup)

    def _updateFileInfo(self, filePath):
        if self._filePath == filePath:
            self.setInfoForFile(filePath)

    def clear(self):
        layout = self.layout()
        for index in reversed(range(layout.count())):
            item = layout.takeAt(index)
            try:
                item.widget().deleteLater()
            except AttributeError:
                item = None

    def setInfoForFile(self, filePath):
        self._filePath = filePath
        if self._filePath is not None:
            data = self._subtitleData.data(filePath)
            self._createFileInfo(filePath, data)
        else:
            self._createEmptyPanel()

    def addTitle(self, title):
        titleLabel = QLabel("<h3>%s</h3>" % title, self)
        titleLabel.setWordWrap(True)
        titleLabel.setTextFormat(Qt.RichText)
        self.layout().addWidget(titleLabel)

    def addLabel(self, text):
        label = QLabel(text, self)
        label.setWordWrap(True)
        self.layout().addWidget(label)

    def addText(self, text):
        textDisplay = QTextEdit(text)
        textDisplay.setAcceptRichText(True)
        textDisplay.setReadOnly(True)
        self.layout().addWidget(textDisplay)

    def addStretch(self):
        self.layout().addStretch()
