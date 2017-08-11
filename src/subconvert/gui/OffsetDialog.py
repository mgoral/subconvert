"""
Copyright (C) 2011-2017 Michal Goral.

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

from subconvert.gui.FrameTimeSpinBox import FrameTimeSpinBox
from subconvert.utils.Locale import _

from PyQt5.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox, QLabel

class OffsetDialog(QDialog):
    frametime = None

    def __init__(self, parent, init_frametime):
        super().__init__(parent)

        self.frametime = None

        layout = QVBoxLayout()
        layout.setSpacing(10)

        layout.addWidget(QLabel(_("Offset:")))

        self._spinbox = FrameTimeSpinBox()
        self._spinbox.setFrameTime(init_frametime)
        layout.addWidget(self._spinbox)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttonBox)

        self.setLayout(layout)
        self.setWindowTitle(_("Offset"))

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def accept(self):
        self.frametime = self._spinbox.frameTime()
        super().accept()

    def reject(self):
        self.frametime = None
        super().reject()
