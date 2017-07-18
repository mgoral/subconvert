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

from PyQt5.QtWidgets import QWidget, QFormLayout, QGroupBox, QLabel, QScrollArea
from PyQt5.QtWidgets import QLayout

from subconvert.gui.ToolBox import Tool
from subconvert.utils.Locale import _

class Details(Tool):
    def __init__(self, subtitleData, parent = None):
        super().__init__(parent)
        self._filePath = None
        self._subtitleData = subtitleData
        self._connectSignals()

    def _connectSignals(self):
        self._subtitleData.fileChanged.connect(self._updateFileInfo)

    def _createFileInfo(self, filePath, data):
        self.clear()

        w = QWidget(self)
        w.setLayout(QFormLayout())
        w.layout().setContentsMargins(2, 2, 2, 2)
        w.layout().setSizeConstraint(QLayout.SetMinimumSize)

        sa = QScrollArea(self)
        sa.setWidget(w)
        sa.setBackgroundRole(w.backgroundRole())

        fileNameLabel = QLabel(os.path.split(filePath)[1], self)
        fileNameLabel.setToolTip(fileNameLabel.text())

        fpsLabel = QLabel(str(data.fps), self)
        fpsLabel.setToolTip(fpsLabel.text())

        formatLabel = QLabel(data.outputFormat.NAME, self)
        formatLabel.setToolTip(formatLabel.text())

        inEncodingLabel = QLabel(data.inputEncoding, self)
        inEncodingLabel.setToolTip(inEncodingLabel.text())

        outEncodingLabel = QLabel(data.outputEncoding, self)
        outEncodingLabel.setToolTip(outEncodingLabel.text())

        if data.videoPath is not None:
            videoLabel = QLabel(data.videoPath, self)
            videoLabel.setToolTip(videoLabel.text())
        else:
            videoLabel = QLabel("-", self)
            videoLabel.setToolTip(_("No video"))

        w.layout().addRow(_("File name:"), fileNameLabel)
        w.layout().addRow(_("Video:"), videoLabel)
        w.layout().addRow(_("FPS:"), fpsLabel)
        w.layout().addRow(_("Format:"), formatLabel)
        w.layout().addRow(_("Input encoding:"), inEncodingLabel)
        w.layout().addRow(_("Output encoding:"), outEncodingLabel)

        self.layout().addWidget(sa)

    def _updateFileInfo(self, filePath):
        if self._filePath == filePath:
            self.setContentForFile(filePath)

    @property
    def name(self):
        return _("Details")

    def setContent(self, widget):
        self._filePath = widget.filePath
        self.setContentForFile(self._filePath)

    def setContentForFile(self, filePath):
        data = self._subtitleData.data(filePath)
        self._createFileInfo(filePath, data)

