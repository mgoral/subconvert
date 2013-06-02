#!/usr/bin/env python3
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
import locale

import logging
import gettext
import time

import parsing.SubParser as SubParser
import parsing.Convert as Convert
import utils.version as version
import utils.path as subpath
import utils.suboptparse as suboptparse

from optparse import OptionParser, OptionGroup

log = logging.getLogger('SubConvert')

t = gettext.translation(
    domain='subconvert',
    localedir=subpath.get_locale_path(__file__),
    fallback=True)
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

    def __init__(self, args = None, options = None):
        super(SubConvertGUI, self).__init__()
        self.init_gui(args, options)

    def init_gui(self, args = None, options = None):
        self.options = options
        self.grid = QtGui.QGridLayout(self)
        self.add_file = QtGui.QPushButton('+', self)
        self.add_movie_file = QtGui.QPushButton('...', self)
        self.remove_file = QtGui.QPushButton('-', self)
        self.start = QtGui.QPushButton(_('Start'), self)
        self.encodings = QtGui.QComboBox(self)
        self.output_encodings = QtGui.QComboBox(self)
        self.output_formats = QtGui.QComboBox(self)
        self.fps = QtGui.QComboBox(self)
        self.file_list = QtGui.QListWidget(self)
        self.movie_path = QtGui.QLineEdit(self)
        self.auto_fps = QtGui.QCheckBox(_('Get FPS from movie.'), self)
        self.fps_label = QtGui.QLabel(_('Movie FPS:'), self)
        self.encoding_label = QtGui.QLabel(_('File(s) encoding:'), self)
        self.output_encoding_label = QtGui.QLabel(_('Output encoding:'), self)
        self.format_label = QtGui.QLabel(_('Output format:'), self)

        self.file_dialog = QtGui.QFileDialog
        sub_extensions = self.get_extensions()

        self.formats = self.get_formats()
        self.movie_exts = ('.avi', '.mkv', '.mpg', '.mp4', '.wmv', '.rmvb', '.mov', '.mpeg')
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
        self.fps.addItems(['23.976', '24', '25', '29.97', '30'])


        self.add_file.clicked.connect(self.open_dialog)
        self.add_movie_file.clicked.connect(self.open_dialog)
        self.remove_file.clicked.connect(self.remove_from_list)
        self.auto_fps.clicked.connect(self.change_auto_fps)
        self.start.clicked.connect(self.convert_files)
        self.file_list.itemDoubleClicked.connect(self.show_item_log)

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
        self.grid.addWidget(self.start, 8, 6)

        self.setLayout(self.grid)
        self.setWindowTitle('SubConvert')

        # Handle args
        if args is not None:
            for arg in args:
                arg = arg.decode(locale.getpreferredencoding())
                filepath = os.path.realpath(arg)
                if os.path.isfile(filepath):
                    self.add_list_item(filepath)
                else:
                    log.error(_("No such file: %s") % arg)

        self_path = subpath.get_dirname(__file__)
        self.setWindowIcon(QtGui.QIcon(os.path.join(self_path, "img/icons/256x256/subconvert.png")))
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

    def add_list_item(self, filepath):
        """Create and set initial values for an item on the list"""
        self_path = subpath.get_dirname(__file__)
        icon = QtGui.QIcon(os.path.join(self_path, "img/initial_list.png"))
        item = QtGui.QListWidgetItem(icon, filepath)
        item.setToolTip("Double click for details.")
        # How not to love Python's polymorphism?
        item.log = list()
        item.job_counter = 0
        self.file_list.addItem(item)

    def change_item_icon(self, item, success):
        """Change file icon according to parsing success status:
        0: succeeded
        1: failed
        2: postponed (skipped)"""

        self_path = subpath.get_dirname(__file__)

        if 0 == success:
            icon = QtGui.QIcon(os.path.join(self_path, "img/ok.png"))
        elif 1 == success:
            icon = QtGui.QIcon(os.path.join(self_path, "img/nook.png"))
        elif 2 == success:
            icon = QtGui.QIcon(os.path.join(self_path, "img/skipped.png"))
        else:
            raise AttributeError
        item.setIcon(icon)

    def open_dialog(self):
        button = self.sender()
        if button == self.add_file:
            filenames = self.file_dialog.getOpenFileNames(
                parent = self,
                caption = _('Open file'),
                directory = self.directory,
                filter = _("Subtitle files (%s);;All files (*.*)") % self.str_sub_exts)
            try:
                self.directory = os.path.split(unicode(filenames[0]))[0]
            except IndexError:
                pass    # Normal error when hitting "Cancel"
            for f in filenames:
                self.add_list_item(f)
        elif button == self.add_movie_file:
            filename = QtGui.QFileDialog.getOpenFileName(
                parent = self,
                caption = _('Open file'),
                directory = self.directory,
                filter = _("Movie files (%s);;All files (*.*)") % self.str_movie_exts)
            if filename:
                self.movie_path.setText(filename)
                self.directory = os.path.split(unicode(filename))[0]

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
        movie_file = unicode(self.movie_path.text())
        sub_format = str(self.output_formats.itemData(self.output_formats.currentIndex()).toString())

        convert_info = []

        to_all = False

        for job in xrange(self.file_list.count()):
            item = self.file_list.item(job)
            filepath = unicode(item.text())
            item.job_counter = item.job_counter + 1
            if (self.options is None) or (self.options is not None and self.options.keep_logs is False):
                # Don't keep logs when started through "subconvert -g" or without --keep-logs option
                item.log = []
            item.log.append(_("----- [ %s: %s ] -----") % (os.path.basename(filepath), item.job_counter))
            if not os.path.isfile(filepath):
                item.log.append(_("No such file: %s") % filepath)
                self.change_item_icon(item, 1)
                continue

            if os.path.getsize(filepath) > MAX_MEGS:
                item.log.append(_("File '%s' too large.") % filepath)
                self.change_item_icon(item, 1)
                continue

            if self.auto_fps.isChecked():
                if not movie_file:
                    filename, extension = os.path.splitext(filepath)
                    for ext in self.movie_exts:
                        if os.path.isfile(''.join((filename, ext))):
                            fps = Convert.mplayer_check(''.join((filename, ext)), fps)
                            break
                        elif os.path.isfile(''.join((filename, ext.upper()))):
                            fps = Convert.mplayer_check(''.join((filename, ext.upper())), fps)
                            break
                else:
                    fps = Convert.mplayer_check(movie_file, fps)

            if 1 > self.encodings.currentIndex():
                opt_encoding = None
            else:
                opt_encoding = str(self.encodings.currentText())
            encoding = Convert.detect_encoding(filepath, opt_encoding)

            if 1 > self.output_encodings.currentIndex():
                output_encoding = encoding
            else:
                output_encoding = str(self.output_encodings.currentText())

            item.log.append(os.linesep.join((
                _("Input encoding: %s") % encoding.replace('_', '-').upper(),
                _("Output encoding: %s") % output_encoding.replace('_', '-').upper(),
                _("Sub FPS: %s") % fps
                )))

            try:
                conv, lines = Convert.convert_file(filepath, encoding, output_encoding, fps, sub_format)
            except NameError:
                item.log.append(_("'%s' format not supported (or mistyped).") % sub_format)
                self.change_item_icon(item, 1)
                return -1
            except UnicodeDecodeError:
                item.log.append(_("Couldn't handle '%s' given '%s' encoding.") % (filepath, encoding))
                self.change_item_icon(item, 1)
                continue
            except SubParser.SubParsingError, msg:
                item.log.append(str(msg).decode(locale.getpreferredencoding()))
                self.change_item_icon(item, 1)
                continue
            if lines:
                log.debug(_("%s parsed.") % filepath)
                convert_info.append(_("%s parsed.") % filepath)
                item.log.append(_("File parsed to %s.") % conv.__SUB_TYPE__)
                if os.path.isfile(conv.filename):
                    if not to_all:
                        bbox = BackupMessage(conv.filename)
                        choice = bbox.exec_()
                        to_all = bbox.get_to_all()
                    if choice == 0: # backup
                        if conv.filename == filepath:
                            filepath, _mvd = Convert.backup(filepath)  # We will read from backed up file
                            item.log.append(_("%s backed up as %s") % (_mvd, filepath))
                        else:
                            _bck = Convert.backup(conv.filename)[0]
                            item.log.append(_("%s backed up as %s") % (conv.filename, _bck))
                    elif choice == 2: # No
                        item.log.append(_("Skipping %s") % filepath)
                        self.change_item_icon(item, 2)
                        continue
                    elif choice == 1: # Yes
                        item.log.append(_("Overwriting %s") % conv.filename)
                    elif choice == 3: # Cancel
                        convert_info.append(_("Quitting converting work."))
                        break
                else:
                    item.log.append(_("Writing to %s") % conv.filename)

                with codecs.open(conv.filename, 'w', encoding=conv.encoding) as cf:
                    cf.writelines(lines)
                    self.change_item_icon(item, 0)
            else:
                log.debug(_("%s not parsed.") % filepath)
                convert_info.append(_("%s not parsed.") % filepath)
                item.log.append(_("File not parsed."))
                self.change_item_icon(item, 1)

        elapsed_time = time.time() - time_start
        summary = QtGui.QMessageBox()
        spacer = QtGui.QSpacerItem(500, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        l = summary.layout()
        l.addItem(spacer, l.rowCount(), 0, 1, l.columnCount())
        summary.setWindowTitle(_("Subconvert - finished"))
        summary.setText(_("Work finished."))
        summary.setInformativeText(os.linesep.join((
            _("Sub FPS: %s") % fps,
            _("Converted in: %f") % elapsed_time)))
        summary.setDetailedText(os.linesep.join(convert_info))
        summary.exec_()

    def show_item_log(self):
        item = self.file_list.currentItem()
        item_summary = QtGui.QMessageBox()
        spacer = QtGui.QSpacerItem(500, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        l = item_summary.layout()
        l.addItem(spacer, l.rowCount(), 0, 1, l.columnCount())
        item_summary.setWindowTitle(_("Subconvert - %s") % unicode(item.text()))
        item_summary.setText(_("Filepath: %s\nFinished jobs: %s") % (unicode(item.text()), item.job_counter))
        item_summary.setDetailedText(os.linesep.join(item.log))
        item_summary.exec_()

def prepare_options():
    """Define optparse options."""
    optp = suboptparse.SubOptionParser(
        usage = _('Usage: %prog [options]'), \
        version = '%s' % version.__version__,
        formatter = suboptparse.SubHelpFormatter()
    )
    optp.group_general.add_option('--debug',
        action='store_true', dest='debug_messages', default=False,
        help=_("Generate debug output"))
    optp.group_general.add_option('--keep-logs',
        action='store_true', dest='keep_logs', default=False,
        help=_("Keep log history for individual files"))

    optp.add_option_group(optp.group_general)

    return optp

def start_app(args, options):
    app = QtGui.QApplication(sys.argv)
    gui = SubConvertGUI(args, options)
    sys.exit(app.exec_())

def main():
    """Main SubConvert GUI function"""
    optp = prepare_options()
    (options, args) = optp.parse_args()

    if options.debug_messages:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.ERROR)
    log.addHandler(logging.StreamHandler())
    start_app(args, options)
