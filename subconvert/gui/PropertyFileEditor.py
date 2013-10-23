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

import os
import errno
import gettext
import pkgutil
import encodings

from PyQt4.QtGui import QDialog, QGridLayout, QWidget, QFileDialog, QComboBox, QTextEdit
from PyQt4.QtGui import QCheckBox, QLabel, QGroupBox, QHBoxLayout, QVBoxLayout, QWidget
from PyQt4.QtGui import QPushButton

from subconvert.gui.FileDialogs import FileDialog
from subconvert.gui.Detail import AUTO_ENCODING_STR
from subconvert.parsing.Formats import *
from subconvert.utils import SubPath
from subconvert.utils.Encodings import ALL_ENCODINGS
from subconvert.utils.PropertyFile import SubtitleProperties, savePropertyFile, loadPropertyFile
from subconvert.utils.SubSettings import SubSettings

t = gettext.translation(
    domain='subconvert',
    localedir=SubPath.getLocalePath(__file__),
    fallback=True)
gettext.install('subconvert')
_ = t.gettext

class PropertyFileEditor(QDialog):
    def __init__(self, parent=None):
        super(PropertyFileEditor, self).__init__(parent)
        self._settings = SubSettings()

        self.__createPropertyFilesDirectory()
        self.__initAllSubFormats()
        self.__initGui()

    def __createPropertyFilesDirectory(self):
        pfileDir = self._settings.getPropertyFilesPath()
        try:
            os.makedirs(pfileDir)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(pfileDir):
                pass
            else: raise

    def __initAllSubFormats(self):
        formats = SubFormat.__subclasses__()
        self._formats = {}
        for f in formats:
            self._formats[f.NAME] = f

    def __initGui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        layout.addWidget(self._createFpsBox())
        layout.addWidget(self._createEncodingBox())
        layout.addWidget(self._createFormatBox())
        layout.addWidget(self._createButtons())

        self.setLayout(layout)
        self.setWindowTitle(_("Subtitle Properties Editor"))
        self.setModal(True)

        # Some signals
        self._closeButton.clicked.connect(self.close)
        self._openButton.clicked.connect(self.openProperties)
        self._saveButton.clicked.connect(self.saveProperties)

    def _createFpsBox(self):
        groupbox = QGroupBox(_("FPS"))
        layout = QHBoxLayout()

        self._autoFps = QCheckBox(_("Auto FPS"), self)

        self._fps = QComboBox(self)
        self._fps.addItems(["23.976", "24", "25", "29.97", "30"])
        self._fps.setEditable(True)

        layout.addWidget(self._autoFps)
        layout.addWidget(self._fps)
        groupbox.setLayout(layout)
        return groupbox

    def _createEncodingBox(self):
        groupbox = QGroupBox(_("File Encoding"))
        layout = QGridLayout()

        self._changeEncoding = QCheckBox(_("Change encoding on save"), self)

        self._inputEncoding = QComboBox(self)
        self._inputEncoding.addItem(AUTO_ENCODING_STR)
        self._inputEncoding.addItems(ALL_ENCODINGS)
        inputLabel = QLabel(_("Input encoding"))

        self._outputEncoding = QComboBox(self)
        self._outputEncoding.addItem(AUTO_ENCODING_STR) # FIXME: bool flag instead
        self._outputEncoding.addItems(ALL_ENCODINGS)
        outputLabel = QLabel(_("Output encoding"))

        layout.addWidget(self._changeEncoding, 0, 0)
        layout.addWidget(self._inputEncoding, 1, 0)
        layout.addWidget(inputLabel, 1, 1)
        layout.addWidget(self._outputEncoding, 2, 0)
        layout.addWidget(outputLabel, 2, 1)
        groupbox.setLayout(layout)
        return groupbox

    def _createFormatBox(self):
        groupbox = QGroupBox(_("Subtitle Format"))
        layout = QGridLayout()

        displayedFormats = list(self._formats.keys())
        displayedFormats.sort()
        self._outputFormat = QComboBox(self)
        self._outputFormat.addItems(displayedFormats)
        formatLabel = QLabel(_("Output format"))

        layout.addWidget(self._outputFormat, 0, 0)
        layout.addWidget(formatLabel, 0, 1)
        groupbox.setLayout(layout)
        return groupbox

    def _createButtons(self):
        widget = QWidget(self)
        layout = QHBoxLayout()

        self._openButton = QPushButton(_("Open"))
        self._saveButton = QPushButton(_("Save"))
        self._closeButton = QPushButton(_("Close"))

        layout.addWidget(self._openButton)
        layout.addWidget(self._saveButton)
        layout.addWidget(self._closeButton)

        widget.setLayout(layout)
        return widget

    def _createSubtitleProperties(self):
        subProperties = SubtitleProperties()

        subProperties.autoFps = self._autoFps.isChecked()
        subProperties.fps = self._fps.currentText()

        subProperties.changeEncoding = self._changeEncoding.isChecked()
        subProperties.inputEncoding = self._inputEncoding.currentText()
        subProperties.outputEncoding = self._outputEncoding.currentText()

        subProperties.outputFormat = self._formats.get(self._outputFormat.currentText())
        return subProperties

    def changeProperties(self, subProperties):
        self._autoFps.setChecked(subProperties.autoFps)
        self._fps.setEditText(str(subProperties.fps))

        self._changeEncoding.setChecked(subProperties.changeEncoding)
        self._inputEncoding.setCurrentIndex(
            self._inputEncoding.findText(subProperties.inputEncoding))
        self._outputEncoding.setCurrentIndex(
            self._outputEncoding.findText(subProperties.outputEncoding))

        if self._formats.get(subProperties.outputFormat.NAME) is subProperties.outputFormat:
            self._outputFormat.setCurrentIndex(
                self._outputFormat.findText(subProperties.outputFormat.NAME))
        else:
            self.close()
            raise RuntimeError(_("Subtitle format doesn't match any of known formats!"))

    def saveProperties(self):
        fileDialog = FileDialog(
            parent = self,
            caption = _('Save Subtitle Properties'),
            directory = self._settings.getPropertyFilesPath()
        )
        fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        fileDialog.setFileMode(QFileDialog.AnyFile)

        if fileDialog.exec():
            filename = fileDialog.selectedFiles()[0]
            if not filename.endswith(".spf"):
                filename = "%s%s" % (filename, ".spf")
            self._settings.setPropertyFilesPath(os.path.dirname(filename))
            subProperties = self._createSubtitleProperties()
            savePropertyFile(filename, subProperties)

    def openProperties(self):
        fileDialog = FileDialog(
            parent = self,
            caption = _("Open Subtitle Properties"),
            directory = self._settings.getPropertyFilesPath(),
            filter = _("Subtitle Properties (*.spf);;All files (*)")
        )
        fileDialog.setFileMode(QFileDialog.ExistingFile)

        if fileDialog.exec():
            filename = fileDialog.selectedFiles()[0]
            self._settings.setPropertyFilesPath(os.path.dirname(filename))
            subProperties = loadPropertyFile(filename)
            self.changeProperties(subProperties)

