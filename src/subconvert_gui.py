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

import os
import sys
from PyQt4 import QtGui, QtCore
import pkgutil
import encodings
import codecs
import logging
import gettext
import time

import subparser.SubParser as SubParser
import subparser.Convert as Convert
import subparser.version as version

from optparse import OptionParser, OptionGroup

log = logging.getLogger('SubConvert')

t = gettext.translation('subconvert', '/usr/share/locale')
gettext.install('subconvert')
_ = t.ugettext

MAX_MEGS = 5 * 1048576

class BackupMessage(QtGui.QMessageBox):
    def __init__(self, filename):
        QtGui.QMessageBox.__init__(self)
        self.setText(_("File %s exists.") % filename) 
        self.setInformativeText("Do you want to overwrite it?.")
        self.setIcon(self.Question)
        self.addButton(_("Backup file"), QtGui.QMessageBox.ActionRole)
        self.addButton(_("Yes"), QtGui.QMessageBox.YesRole)
        self.addButton(_("No"), QtGui.QMessageBox.NoRole)
        self.addButton(_("Cancel"), QtGui.QMessageBox.DestructiveRole)
        self.to_all = QtGui.QCheckBox(_('To all'), self)
        self.layout().addWidget(self.to_all, 3, 0, 1, 1)

    def get_to_all(self):
        return self.to_all.isChecked()

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
        self.output_encodings = QtGui.QComboBox(self)
        self.output_formats = QtGui.QComboBox(self)
        self.output_extensions = QtGui.QComboBox(self)
        self.fps = QtGui.QComboBox(self)
        self.file_list = QtGui.QListWidget(self)
        self.movie_path = QtGui.QLineEdit(self)
        self.auto_fps = QtGui.QCheckBox(_('Get FPS from movie.'), self)
        self.fps_label = QtGui.QLabel(_('Movie FPS:'), self)
        self.encoding_label = QtGui.QLabel(_('File(s) encoding:'), self)
        self.output_encoding_label = QtGui.QLabel(_('Output encoding:'), self)
        self.format_label = QtGui.QLabel(_('Output format:'), self)
        self.extension_label = QtGui.QLabel(_('File extension:'), self)

        self.file_dialog = QtGui.QFileDialog
        sub_extensions = self.get_extensions()

        self.formats = self.get_formats()
        self.movie_exts = ('.avi', '.mkv', '.mpg', '.mp4', '.wmv')
        self.str_sub_exts = ' '.join(['*.%s' % ext for ext in sub_extensions[1:]])
        self.str_movie_exts = ' '.join(['*%s' % fmt for fmt in self.movie_exts])
        self.directory = ''

        self.grid.setSpacing(10)
        self.encodings.addItem(_('[Detect]'))
        self.encodings.addItems(self.get_encodings())
        self.output_encodings.addItem(_("[Don't change]"))
        self.output_encodings.addItems(self.get_encodings())
        for fmt in self.formats:
            self.output_formats.addItem(fmt[0], fmt[1])
        self.output_extensions.addItems(sub_extensions)
        self.fps.addItems(['23.976', '24', '25', '29.97', '30'])


        self.add_file.clicked.connect(self.open_dialog)
        self.add_movie_file.clicked.connect(self.open_dialog)
        self.remove_file.clicked.connect(self.remove_from_list)
        self.auto_fps.clicked.connect(self.change_auto_fps)
        self.start.clicked.connect(self.convert_files)

        self.auto_fps.setCheckState(QtCore.Qt.Checked)
        self.change_auto_fps()
        
        self.grid.addWidget(self.encoding_label, 0, 0)
        self.grid.addWidget(self.encodings, 0, 1)
        self.grid.addWidget(self.fps_label, 0, 2)
        self.grid.addWidget(self.fps, 0, 3)
        self.grid.addWidget(self.output_encoding_label, 1, 0)
        self.grid.addWidget(self.output_encodings, 1, 1)
        self.grid.addWidget(self.file_list, 2, 0, 4, 6)
        self.grid.addWidget(self.add_file, 2, 6 )
        self.grid.addWidget(self.remove_file, 3, 6)
        self.grid.addWidget(self.movie_path, 6, 0, 1, 6)
        self.grid.addWidget(self.add_movie_file, 6, 6)
        self.grid.addWidget(self.auto_fps, 7, 0, 1, 2)
        self.grid.addWidget(self.format_label, 8, 0)
        self.grid.addWidget(self.output_formats, 8, 1)
        self.grid.addWidget(self.extension_label, 9, 0)
        self.grid.addWidget(self.output_extensions, 9, 1)
        self.grid.addWidget(self.start, 9, 6)

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
        cls = SubParser.GenericSubParser.__subclasses__()
        for c in cls:
            yield (c.__SUB_TYPE__, c.__OPT__)

    def get_extensions(self):
        cls = SubParser.GenericSubParser.__subclasses__()
        exts = [_('Default')]
        exts.extend(set([ c.__EXT__ for c in cls ]))
        exts.sort()
        return exts

    def open_dialog(self):
        button = self.sender()
        if button == self.add_file:
            filenames = self.file_dialog.getOpenFileNames(
                parent = self, 
                caption = _('Open file'),
                directory = self.directory,
                filter = _("Subtitle files (%s);;All files (*.*)") % self.str_sub_exts)
            try:
                self.directory = os.path.split(str(filenames[0]))[0]
            except IndexError:
                pass    # Normal error when hitting "Cancel"
            for f in filenames:
                item = QtGui.QListWidgetItem(f)
                self.file_list.addItem(item)
        elif button == self.add_movie_file:
            filename = QtGui.QFileDialog.getOpenFileName(
                parent = self,
                caption = _('Open file'),
                directory = self.directory,
                filter = _("Movie files (%s);;All files (*.*)") % self.str_movie_exts)
            if filename:
                self.movie_path.setText(filename)
                self.directory = os.path.split(str(filename))[0]

    def remove_from_list(self):
        item = self.file_list.takeItem(self.file_list.currentRow())
        item = None

    def change_auto_fps(self):
        if self.auto_fps.isChecked():
            self.fps.setEnabled(False)
        else:
            self.fps.setEnabled(True)

    def convert_files(self):
        time_start = time.time()
        fps = str(self.fps.currentText())
        movie_file = str(self.movie_path.text())
        files = [str(self.file_list.item(i).text()) for i in xrange(self.file_list.count())]
        sub_format = str(self.output_formats.itemData(self.output_formats.currentIndex()).toString())
        out_extension = str(self.output_extensions.itemText(self.output_extensions.currentIndex())) if self.output_extensions.currentIndex() > 0 else ''

        convert_info = []

        to_all = False

        for job, arg in enumerate(files): # Call it 'arg' to keep a consistency with cli version
            convert_info.append(_("----- [ %d. %s ] -----") % (job, os.path.split(arg)[1]))
            if os.path.getsize(arg) > MAX_MEGS:
                convert_info.append(_("File '%s' too large.") % arg)
                continue

            if self.auto_fps.isChecked():
                if not movie_file:
                    filename, extension = os.path.splitext(arg)
                    for ext in self.movie_exts:
                        f = ''.join((filename, ext))
                        if os.path.isfile(f):
                            fps = Convert.mplayer_check(f, fps)
                            break
                else:
                    fps = Convert.mplayer_check(movie_file, fps)

            if 1 > self.encodings.currentIndex():
                opt_encoding = None
            else:
                opt_encoding = str(self.encodings.currentText())
            encoding = Convert.detect_encoding(arg, opt_encoding)

            if 1 > self.output_encodings.currentIndex():
                output_encoding = encoding
            else:
                output_encoding = str(self.output_encodings.currentText())
            
            try:
                conv, lines = Convert.convert_file(arg, encoding, output_encoding, fps, sub_format, out_extension)
            except NameError:
                convert_info.append(_("'%s' format not supported (or mistyped).") % sub_format)
                return -1
            except UnicodeDecodeError:
                convert_info.append(_("Couldn't handle '%s' given '%s' encoding.") % (arg, encoding))
                continue
            except SubParser.SubParsingError, msg:
                convert_info.append(str(msg))
                continue
            if lines:
                log.debug(_("%s parsed.") % arg)
                convert_info.append(_("%s parsed.") % arg)
                if os.path.isfile(conv.filename):
                    if not to_all:
                        bbox = BackupMessage(conv.filename)
                        choice = bbox.exec_()
                        to_all = bbox.get_to_all()
                    if choice == 0: # backup
                        if conv.filename == arg:
                            arg, _mvd = Convert.backup(arg)  # We will read from backed up file
                            log.info(_("%s backed up as %s") % (_mvd, arg))
                            convert_info.append(_("%s backed up as %s") % (_mvd, arg))
                        else:
                            _bck = Convert.backup(conv.filename)[0]
                            convert_info.append(_("%s backed up as %s") % (conv.filename, _bck))
                    elif choice == 2: # No
                        convert_info.append(_("Skipping %s") % arg)
                        continue
                    elif choice == 1: # Yes
                        convert_info.append(_("Overwriting %s") % conv.filename)
                    elif choice == 3: # Cancel 
                        convert_info.append(_("Quitting converting work."))
                        return 1
                else:
                    convert_info.append("Writing to %s" % conv.filename)
            
                with codecs.open(conv.filename, 'w', encoding=conv.encoding) as cf:
                    cf.writelines(lines)
            else:
                log.debug(_("%s not parsed.") % arg)
                convert_info.append(_("%s not parsed.") % arg)

        elapsed_time = time.time() - time_start
        summary = QtGui.QMessageBox()
        spacer = QtGui.QSpacerItem(500, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        l = summary.layout()
        l.addItem(spacer, l.rowCount(), 0, 1, l.columnCount())
        summary.setWindowTitle(_("Subconvert - finished"))
        summary.setText(_("Work finished."))
        summary.setInformativeText(os.linesep.join([_("Sub FPS: %s") % fps, _("Input encoding: %s") % encoding.replace('_', '-').upper(), _("Output encoding: %s") % output_encoding.replace('_', '-').upper(), _("Converted in: %f") % elapsed_time]))
        summary.setDetailedText(os.linesep.join(convert_info))
        summary.exec_()

def prepare_options():
    """Define optparse options."""
    optp = OptionParser(usage = _('Usage: %prog [options]'), \
        version = '%s' % version.__version__ )
    optp.add_option('--debug',
        action='store_true', dest='debug_messages', default=False,
        help=_("Generate debug output"))

    return optp

def main():
    """Main SubConvert GUI function"""
    optp = prepare_options()
    (options, args) = optp.parse_args()

    if options.debug_messages:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.ERROR)
    log.addHandler(logging.StreamHandler())

    app = QtGui.QApplication(sys.argv)
    gui = SubConvertGUI()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
