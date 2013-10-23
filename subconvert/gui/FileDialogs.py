"""
Copyright (C) 2013 Michal Goral.

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
from subconvert.gui.Detail import AUTO_ENCODING_STR, _
from subconvert.utils import SubPath

from PyQt4.QtGui import QFileDialog, QHBoxLayout, QComboBox, QLabel

class SubFileDialog(QFileDialog):
    def __init__(self, parent = None, caption = "", directory = "", filter = ""):
        super().__init__(parent, caption, directory, filter)

    def _initAllSubFormats(self):
        formats = SubFormat.__subclasses__()
        self._formats = {}
        for f in formats:
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

    def _addFormatBox(self, row):
        self._initAllSubFormats()
        displayedFormats = list(self._formats.keys())
        displayedFormats.sort()

        mainLayout = self.layout()

        formatLabel = QLabel(_("Subtitle format:"), self)
        self._formatBox = QComboBox(self)
        self._formatBox.addItems(displayedFormats)

        mainLayout.addWidget(formatLabel, row, 0)
        mainLayout.addWidget(self._formatBox, row, 1)

    def getEncoding(self):
        return self._encodingBox.currentText()

    def getSubFormat(self):
        return self._formats.get(self._formatBox.currentText())

class FileDialog(SubFileDialog):
    def __init__(self, parent = None, caption = "", directory = "", filter = ""):
        super().__init__(parent, caption, directory, filter)

    def addEncodings(self, addAuto):
        self._addEncodingsBox(self.layout().rowCount(), addAuto)

    def addFormats(self):
        self._addFormatBox(self.layout().rowCount())
