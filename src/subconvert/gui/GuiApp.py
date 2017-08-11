#-*- coding: utf-8 -*-

"""
Copyright (C) 2015 Michal Goral.

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

import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from subconvert.gui.MainWindow import MainWindow

class SubApplication:
    def __init__(self, args, parser):
        self._args = args
        self._parser = parser

        self._app = QApplication(sys.argv)
        self._gui = MainWindow(self._args, self._parser)

    def cleanup(self):
        self._gui.cleanup()

    def run(self):
        # Let the interpreter run each 500 ms.
        timer = QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)

        self._gui.show()
        return self._app.exec_()

