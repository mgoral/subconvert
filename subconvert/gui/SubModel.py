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

import re

from subconvert.gui.FrameTimeSpinBox import FrameTimeSpinBox
from subconvert.utils.Locale import _

from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import Qt


def createRow(sub, start=None, end=None):
    if start is None: start = sub.start
    if end is None: end = sub.end

    timeStart = QStandardItem(start.toStr())
    timeEnd = QStandardItem(end.toStr())
    text = QStandardItem(sub.text)

    timeStart.setData(start, CustomDataRoles.FrameTimeRole)
    timeEnd.setData(end, CustomDataRoles.FrameTimeRole)

    timeStart.setData(False, CustomDataRoles.ErrorFlagRole)
    timeEnd.setData(False, CustomDataRoles.ErrorFlagRole)

    return [timeStart, timeEnd, text]


class save_painter:
    def __init__(self, painter):
        self._painter = painter

    def __enter__(self, *args, **kwargs):
        self._painter.save()

    def __exit__(self, *args, **kwargs):
        self._painter.restore()


class CustomDataRoles:
    FrameTimeRole = Qt.UserRole + 1
    ErrorFlagRole = Qt.UserRole + 2
    WidgetRole    = Qt.UserRole + 3


class SubListItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return FrameTimeSpinBox(parent)

    def setEditorData(self, editor, index):
        frameTime = index.model().data(index, CustomDataRoles.FrameTimeRole)
        editor.setFrameTime(frameTime)

    def setModelData(self, editor, model, index):
        frameTime = editor.frameTime()
        modelFrameTime = index.model().data(index, CustomDataRoles.FrameTimeRole)

        if editor.incorrectInput() is True:
            model.setData(index, True, CustomDataRoles.ErrorFlagRole)
        elif frameTime is not None and frameTime != modelFrameTime:
            data = {
                Qt.EditRole: editor.text(),
                CustomDataRoles.FrameTimeRole: frameTime,
                CustomDataRoles.ErrorFlagRole: False,
            }
            model.setItemData(index, data)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
