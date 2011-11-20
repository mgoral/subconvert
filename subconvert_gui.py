#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
    This file is part of Subconvert.

    Subconvert is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Subconvert is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Subconvert.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
from PyQt4 import QtGui
import pkgutil
import encodings
import gettext
import subconvert

__VERSION__ = '0.1'
__AUTHOR__ = u'Michał Góral'

gettext.bindtextdomain('subconvert', '/usr/lib/subconvert/locale')
gettext.textdomain('subconvert')
_ = gettext.gettext

class SubConvertGUI(QtGui.QWidget):
	"""Graphical User Interface for Subconvert."""

	def __init__(self):
		super(SubConvertGUI, self).__init__()
		self.init_gui()
	
	def init_gui(self):
		self.grid = QtGui.QGridLayout(self)
		self.add_file = QtGui.QPushButton('+', self)
		self.add_movie_file = QtGui.QPushButton('...', self)
		self.remove_file = QtGui.QPushButton('-', self)
		self.start = QtGui.QPushButton(_('Start'), self)
		self.encodings = QtGui.QComboBox(self)
		self.output_formats = QtGui.QComboBox(self)
		self.output_extensions = QtGui.QComboBox(self)
		self.fps = QtGui.QComboBox(self)
		self.file_list = QtGui.QListWidget(self)
		self.movie_path = QtGui.QLineEdit(self)
		self.auto_fps = QtGui.QCheckBox(_('Get FPS from movie.'), self)
		self.fps_label = QtGui.QLabel('Movie FPS:', self)
		self.encoding_label = QtGui.QLabel(_('File(s) encoding:'), self)
		self.format_label = QtGui.QLabel(_('Output format:'), self)
		self.extension_label = QtGui.QLabel(_('File extension:'), self)

		self.file_dialog = QtGui.QAction('Open', self)

		self.grid.setSpacing(10)
		self.encodings.addItems(self.get_encodings())
		self.output_formats.addItems(self.get_formats())
		self.output_extensions.addItems(self.get_extensions())
		self.fps.addItems(['23.976', '24', '25', '29.97', '30'])

		self.add_file.clicked.connect(self.open_dialog)
		self.add_movie_file.clicked.connect(self.open_dialog)
		self.remove_file.clicked.connect(self.remove_from_list)
		self.auto_fps.clicked.connect(self.change_auto_fps)
		
		self.grid.addWidget(self.encoding_label, 0, 0)
		self.grid.addWidget(self.encodings, 0, 1)
		self.grid.addWidget(self.fps_label, 0, 2)
		self.grid.addWidget(self.fps, 0, 3)
		self.grid.addWidget(self.file_list, 1, 0, 4, 6)
		self.grid.addWidget(self.add_file, 1, 6 )
		self.grid.addWidget(self.remove_file, 2, 6)
		self.grid.addWidget(self.movie_path, 5, 0, 1, 6)
		self.grid.addWidget(self.add_movie_file, 5, 6)
		self.grid.addWidget(self.auto_fps, 6, 0, 1, 2)
		self.grid.addWidget(self.format_label, 7, 0)
		self.grid.addWidget(self.output_formats, 7, 1)
		self.grid.addWidget(self.extension_label, 8, 0)
		self.grid.addWidget(self.output_extensions, 8, 1)
		self.grid.addWidget(self.start, 8, 6)

		self.setLayout(self.grid)
		self.setWindowTitle('SubConvert')
		self.show()

	def get_encodings(self):
		# http://stackoverflow.com/questions/1707709/list-all-the-modules-that-are-part-of-a-python-package/1707786#1707786
		false_positives = set(["aliases"])
		found = set(name for imp, name, ispkg in pkgutil.iter_modules(encodings.__path__) if not ispkg)
		found.difference_update(false_positives)
		found = list(found)
		found.sort()
		return found

	def get_formats(self):
		cls = subconvert.GenericSubParser.__subclasses__()
		formats = set([ "%s (%s)" % (c.__OPT__, c.__SUB_TYPE__) for c in cls ])
		formats = list(formats)
		formats.sort()
		return formats

	def get_extensions(self):
		cls = subconvert.GenericSubParser.__subclasses__()
		exts = ['Default']
		exts.extend(set([ c.__EXT__ for c in cls ]))
		exts.sort()
		return exts

	def open_dialog(self):
		button = self.sender()
		if button == self.add_file:
			filenames = QtGui.QFileDialog.getOpenFileNames(self, _('Open file'))
			for f in filenames:
				item = QtGui.QListWidgetItem(f)
				self.file_list.addItem(item)
		elif button == self.add_movie_file:
			filename = QtGui.QFileDialog.getOpenFileName(self, _('Open file'))
			if filename:
				self.movie_path.setText(filename)

	def remove_from_list(self):
		item = self.file_list.takeItem(self.file_list.currentRow())
		item = None

	def change_auto_fps(self):
		if self.auto_fps.isChecked():
			self.fps.setEnabled(False)
		else:
			self.fps.setEnabled(True)

def main():
	app = QtGui.QApplication(sys.argv)
	gui = SubConvertGUI()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
