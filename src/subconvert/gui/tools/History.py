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

from PyQt5.QtWidgets import QVBoxLayout, QUndoView

from subconvert.gui.ToolBox import Tool
from subconvert.utils.Locale import _

class History(Tool):
    def __init__(self, parent = None):
        super().__init__(parent)

    @property
    def name(self):
        return _("History of changes")

    def setContent(self, widget):
        self.clear()
        undoview = QUndoView(widget.history, self)
        undoview.setEmptyLabel(_("<Original file>"))
        self.layout().addWidget(undoview)
