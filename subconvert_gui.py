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
	"""Graphical User Interface for Subconvert"""

	def __init__(self):
		super(SubConvertGUI, self).__init__()
		self.init_gui()
	
	def init_gui(self):
		grid = QtGui.QGridLayout(self)
		add_file = QtGui.QPushButton(self)
		movie_file = QtGui.QPushButton(self)
		remove_file = QtGui.QPushButton(self)
		start = QtGui.QPushButton('Start', self)
		encodings = QtGui.QComboBox(self)
		output_formats = QtGui.QComboBox(self)
		output_extensions = QtGui.QComboBox(self)
		fps = QtGui.QComboBox(self)
		file_list = QtGui.QListView(self)
		movie_path = QtGui.QLineEdit(self)
		auto_fps = QtGui.QCheckBox('Get FPS from movie.', self)
		fps_label = QtGui.QLabel('Movie FPS:', self)
		encoding_label = QtGui.QLabel('File(s) encoding:', self)
		format_label = QtGui.QLabel('Output format:', self)
		extension_label = QtGui.QLabel('File extension:', self)

		grid.setSpacing(10)
		add_file.setText('+')
		remove_file.setText('-')
		movie_file.setText('...')
		encodings.addItems(self.get_encodings())
		output_formats.addItems(self.get_formats())
		output_extensions.addItems(self.get_extensions())
		fps.addItems(['23.976', '24', '25', '29.97', '30'])
		
		grid.addWidget(encoding_label, 0, 0)
		grid.addWidget(encodings, 0, 1)
		grid.addWidget(fps_label, 0, 2)
		grid.addWidget(fps, 0, 3)
		grid.addWidget(file_list, 1, 0, 4, 6)
		grid.addWidget(add_file, 1, 6 )
		grid.addWidget(remove_file, 2, 6)
		grid.addWidget(movie_path, 5, 0, 1, 6)
		grid.addWidget(movie_file, 5, 6)
		grid.addWidget(auto_fps, 6, 0, 1, 2)
		grid.addWidget(format_label, 7, 0)
		grid.addWidget(output_formats, 7, 1)
		grid.addWidget(extension_label, 8, 0)
		grid.addWidget(output_extensions, 8, 1)
		grid.addWidget(start, 8, 6)

		self.setLayout(grid)
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

def main():
	app = QtGui.QApplication(sys.argv)
	gui = SubConvertGUI()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
