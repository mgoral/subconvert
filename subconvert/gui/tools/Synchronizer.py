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

from collections import namedtuple, defaultdict

from subconvert.parsing.Offset import SyncPoint, TimeSync
from subconvert.gui.ToolBox import Tool
from subconvert.gui.SubModel import createRow, SubListItemDelegate, CustomDataRoles
from subconvert.gui.SubtitleCommands import ChangeData
from subconvert.utils.Locale import _

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QErrorMessage
from PyQt5.QtWidgets import QTableView, QHeaderView, QLayout
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtCore import Qt, pyqtSlot

# Having data is redundant, but it avoids unnecessary copies
_CurrentData = namedtuple("CurrentData", ["data", "model", "editor"])


class Synchronizer(Tool):
    def __init__(self, videoWidget, subtitleData,  parent=None):
        super().__init__(parent)

        self._models = defaultdict(self._modelFactory) # path : QStandardItemModel
        self._current = None

        self._videoWidget = videoWidget
        self._subtitleData = subtitleData
        # avoid unnecessary copies in each addPoint() call
        self._err = QErrorMessage()

        self._table = None

        self._subtitleData.fileChanged.connect(self._fileChanged)
        self._subtitleData.subtitlesChanged.connect(self._subtitlesChanged)
        self._subtitleData.subtitlesAdded.connect(self._subtitlesAdded)
        self._subtitleData.subtitlesRemoved.connect(self._subtitlesRemoved)

    @property
    def name(self):
        return _("Synchronize")

    def setContent(self, widget):
        path = widget.filePath
        model = self._models[path]

        data = self._subtitleData.data(widget.filePath)
        self._current = _CurrentData(data, model, widget)

        if self._table is None:  # e.g. when switched from file list
            self.clear()
            self._table = self._makeTable(model)
            self.layout().addWidget(self._table, stretch=1)
            self.layout().addWidget(_Controls(self), stretch=0)
        else:
            self._table.setModel(model)
        self._updateRmButtons()

    def clear(self):
        super().clear()
        self._table = None

    def remove(self, path):
        if path in self._models:
            del self._models[path]

    def setTopLevelWindow(self):
        self.raise_()
        self.activateWindow()

    def apply(self):
        syncpoints = _syncPoints(self._current.model)
        if len(syncpoints) == 0:
            return

        ts = TimeSync(self._current.data.subtitles)  # in-place sync
        ts.sync(syncpoints)
        command = ChangeData(self._current.editor.filePath, self._current.data,
                             _("Subtitles synchronization"))
        self._subtitleData.execute(command)

    @pyqtSlot()
    def addPoint(self):
        rows = self._current.editor.selectedRows()
        newStart = self._videoWidget.position

        if len(rows) == 0 or newStart is None:
            self._err.showMessage(_("Select a subtitle and position in current video first."))
            return

        # row and sub reflect the same subtitle, but we need both for different things
        row = rows[0]
        sub = self._current.data.subtitles[row]

        # Don't add the same subtitle or the same sync time twice
        if any(row == point.subNo or newStart == point.start
               for point in _syncPoints(self._current.model)):
            self._err.showMessage(_("Can't repeat synchronization points"))
            return

        if sub.fps != newStart.fps:
            self._err.showMessage(_("Subtitle and video have different framerates (%(sub)s vs"
                                    "%(vid)s") % dict(sub=sub.fps, vid=newStart.fps))
            return

        delta = sub.end - sub.start
        newEnd = newStart + delta

        startItem, endItem, textItem = createRow(sub, newStart, newEnd)
        subNoItem = QStandardItem(str(row))
        subNoItem.setEditable(False)
        textItem.setEditable(False)
        rmItem = QStandardItem("")
        self._current.model.appendRow([subNoItem, startItem, endItem, textItem, rmItem])

        self._rmButton(self._table, rmItem)

    def removeSelected(self):
        indices = self._table.selectedIndexes()
        if len(indices) > 0:
            rows = list(set([index.row() for index in indices]))
            rows.sort(reverse=True)
            for row in rows:
                self.removeRow(row)
            if self._current.model.rowCount() > rows[-1]:
                self._table.selectRow(rows[-1])
            else:
                self._table.selectRow(self._current.model.rowCount() - 1)

    @pyqtSlot(int)
    def removeRow(self, no):
        self._current.model.removeRow(no)

    def keyPressEvent(self, keyEvent):
        if keyEvent.key() == Qt.Key_Delete:
            self.removeSelected()
        else:
            super().keyPressEvent(keyEvent)

    def _makeTable(self, model):
        table = QTableView(self)
        table.setModel(model)
        table.hideColumn(0)
        table.setShowGrid(False)

        subListDelegate = SubListItemDelegate()
        table.setItemDelegateForColumn(1, subListDelegate)
        table.setItemDelegateForColumn(2, subListDelegate)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        return table

    def _modelFactory(self):
        model = QStandardItemModel(0, 5, self)
        model.setHorizontalHeaderLabels([_("No."), _("New begin"), _("New end"),
                                            _("Subtitle"), ""])
        return model

    def _rmButton(self, table, item):
        rmButton = QPushButton(QIcon.fromTheme("list-remove"), "")
        rmButton.setFlat(True)
        table.setIndexWidget(item.index(), rmButton)
        rmButton.clicked.connect(lambda _, i=item: self.removeRow(i.row()))

    def _updateRmButtons(self):
        if self._table is None:  # safety check
            return

        for row in range(self._current.model.rowCount()):
            item = self._current.model.item(row, 4)
            self._rmButton(self._table, item)

    def _fileChanged(self, path):
        model = self._models.get(path)
        if model is None:
            return

        subtitles = self._subtitleData.subtitles(path)

        for row in range(model.rowCount()):
            subNo = _subNo(model, row)
            sub = subtitles[subNo]

            # clear model when things don't match pretty badly
            if subNo >= len(subtitles):
                model.removeRows(0, model.rowCount())
                return

            _setText(sub.text, model, row)

    def _subtitlesChanged(self, path, subNos):
        model = self._models.get(path)
        if model is None:
            return

        subtitles = self._subtitleData.subtitles(path)
        for no in subNos:
            sub = subtitles[no]
            row = _findRow(no, model)
            if row is not None:
                _setText(sub.text, model, row)

    def _subtitlesAdded(self, path, subNos):
        """When subtitle is added, all syncPoints greater or equal than a new
        subtitle are incremented."""
        def action(current, count, model, row):
            _setSubNo(current + count, model, row)

        def count(current, nos):
            ret = 0
            for no in nos:
                if current >= no:
                    ret += 1
                    # consider: current = 0, nos = [0, 1, 2, 3]
                    # in that case, current should be prepended by all nos
                    current += 1
            return ret

        self._changeSubNos(path, subNos, count, action)

    def _subtitlesRemoved(self, path, subNos):
        """When subtitle is removed, all syncPoints greater than removed
        subtitle are decremented. SyncPoint equal to removed subtitle is also
        removed."""
        def action(current, count, model, row):
            if count.equal > 0:
                model.removeRow(row)
            else:
                _setSubNo(current - count.greater_equal, model, row)

        def count(current, nos):
            return _GtEqCount(current, nos)

        self._changeSubNos(path, subNos, count, action)

    def _changeSubNos(self, path, subNos, count, action, reverse=False):
        """Implementation of subs add/removal handling.

        Args:
            path: file path associated with model on which work is done
            subNos: list of added/removed subtitle numbers
            count: function which accepts current sync point's subtitle number
                   and subNos and returns anything based on these values
            action: action performed for each of sync point's subtitle number.
                    Accepts current SyncPoint.subNo, count result, model and
                    row:
                        def action(current, count, model, row)
        """
        model = self._models.get(path)
        if model is None:
            return

        syncPoints = _syncPoints(model)
        syncSubNos = [p.subNo for p in syncPoints]
        syncSubNos.sort()

        if len(syncSubNos) == 0:
            return

        for current in syncSubNos:
            row = _findRow(current, model)
            action(current, count(current, subNos), model, row)


class _Controls(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        layout = QHBoxLayout(self)

        layout.addStretch(1)

        addButton = QPushButton(QIcon.fromTheme("list-add"), "")
        addButton.setToolTip(_("Add new synchronization point"))
        layout.addWidget(addButton)

        # might not be the best icon, but whatever...
        applyButton = QPushButton(QIcon.fromTheme("go-jump"), "")
        applyButton.setToolTip(_("Apply"))
        layout.addWidget(applyButton)

        self.setLayout(layout)

        addButton.clicked.connect(parent.addPoint)
        applyButton.clicked.connect(parent.apply)


def _syncPoints(model):
    ret = []
    for row in range(model.rowCount()):
        subNo = _subNo(model, row)
        start = _start(model, row)
        end = _end(model, row)
        ret.append(SyncPoint(subNo, start, end))
    return ret


def _findRow(subNo, model):
    """Finds a row in a given model which has a column with a given
    number."""
    items = model.findItems(str(subNo))
    if len(items) == 0:
        return None
    if len(items) > 1:
        raise IndexError("Too many items with sub number %s" % subNo)
    return items[0].row()


# model accessors which give names to cryptic column numbers
def _subNo(model, row):
    return int(model.item(row, 0).data(Qt.DisplayRole))


def _setSubNo(subNo, model, row):
    model.item(row, 0).setData(subNo, Qt.DisplayRole)


def _start(model, row):
    return model.item(row, 1).data(CustomDataRoles.FrameTimeRole)


def _setStart(ft, model, row):
    model.item(row, 1).setData(ft, CustomDataRoles.FrameTimeRole)


def _end(model, row):
    return model.item(row, 2).data(CustomDataRoles.FrameTimeRole)


def _setEnd(ft, model, row):
    model.item(row, 2).setData(ft, CustomDataRoles.FrameTimeRole)


def _text(model, row):
    return model.item(row, 3).data(Qt.DisplayRole)


def _setText(text, model, row):
    model.item(row, 3).setData(text, Qt.DisplayRole)


class _GtEqCount:
    def __init__(self, val, list_):
        self.greater_equal = 0
        self.equal = 0

        for elem in list_:
            if val >= elem:
                self.greater_equal += 1
            if val == elem:
                self.equal += 1
