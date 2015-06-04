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

import pkgutil
import encodings

from subconvert.utils.Encodings import ALL_ENCODINGS
from subconvert.parsing.Formats import *
from subconvert.gui.Detail import AUTO_ENCODING_STR
from subconvert.utils.Locale import _

from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QComboBox, QLabel

class SubFileDialog(QFileDialog):
    def __init__(self, parent = None, caption = "", directory = "", filter = ""):
        super().__init__(parent, caption, directory, filter)
        self.setOption(QFileDialog.DontUseNativeDialog)

    def _initAllSubFormats(self, formatList):
        self._formats = {}
        for f in formatList:
            self._formats[f.NAME] = f

    def _addEncodingsBox(self, row, addAuto):
        mainLayout = self.layout()

        encodingLabel = QLabel(_("File encoding:"), self)

        self._encodingBox = QComboBox(self)
        if addAuto is True:
            self._encodingBox.addItem(AUTO_ENCODING_STR)
        self._encodingBox.addItems(ALL_ENCODINGS)
        self._encodingBox.setToolTip(_("Change file encoding"))
        self._encodingBox.setEditable(True)

        mainLayout.addWidget(encodingLabel, row, 0)
        mainLayout.addWidget(self._encodingBox, row, 1)

    def _addFormatBox(self, row, formatList):
        self._initAllSubFormats(formatList)
        displayedFormats = list(self._formats.keys())
        displayedFormats.sort()

        mainLayout = self.layout()

        formatLabel = QLabel(_("Subtitle format:"), self)
        self._formatBox = QComboBox(self)
        self._formatBox.addItems(displayedFormats)

        mainLayout.addWidget(formatLabel, row, 0)
        mainLayout.addWidget(self._formatBox, row, 1)

    def getEncoding(self):
        encoding = self._encodingBox.currentText()
        if encoding == AUTO_ENCODING_STR:
            encoding = None
        return encoding

    def setEncoding(self, encoding):
        index = self._encodingBox.findText(encoding)
        self._encodingBox.setCurrentIndex(index)

    def getSubFormat(self):
        return self._formats.get(self._formatBox.currentText())

    def setSubFormat(self, subFormat):
        for key, val in self._formats.items():
            if val == subFormat:
                index = self._formatBox.findText(key)
                self._formatBox.setCurrentIndex(index)
                return

class FileDialog(SubFileDialog):
    def __init__(self, parent = None, caption = "", directory = "", filter = ""):
        super().__init__(parent, caption, directory, filter)

    def addEncodings(self, addAuto):
        self._addEncodingsBox(self.layout().rowCount(), addAuto)

    def addFormats(self, formatList):
        self._addFormatBox(self.layout().rowCount(), formatList)
