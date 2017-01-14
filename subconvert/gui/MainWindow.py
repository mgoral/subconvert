#-*- coding: utf-8 -*-

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

import os
import logging
import bisect
from string import Template

from PyQt5.QtWidgets import QMainWindow, QWidget, QFileDialog, QVBoxLayout, QAction, qApp
from PyQt5.QtWidgets import QMessageBox, QSpacerItem
from PyQt5.QtGui import QPixmap, QDesktopServices, QIcon
from PyQt5.QtCore import pyqtSlot, QDir, Qt, QUrl

from subconvert.parsing.FrameTime import FrameTime
from subconvert.parsing.Core import SubConverter
from subconvert.parsing.Formats import *
from subconvert.gui import SubtitleWindow
from subconvert.gui.DataModel import DataController
from subconvert.gui.PropertyFileEditor import PropertyFileEditor
from subconvert.gui.FileDialogs import FileDialog
from subconvert.gui.OffsetDialog import OffsetDialog
from subconvert.gui.Detail import ActionFactory, CannotOpenFilesMsg, MessageBoxWithList, FPS_VALUES
from subconvert.gui.SubtitleCommands import *
from subconvert.gui.VideoWidget import VideoWidget
from subconvert.utils.Locale import _, P_
from subconvert.utils.Encodings import ALL_ENCODINGS
from subconvert.utils.SubSettings import SubSettings
from subconvert.utils.SubFile import File, SubFileError
from subconvert.utils.VideoPlayer import VideoPlayer, VideoPlayerException
from subconvert.utils.version import __version__, __author__, __license__, __website__, __transs__

log = logging.getLogger('Subconvert.%s' % __name__)

substituteDict = {
    "author": __author__,
    "license": __license__,
    "version": __version__,
    "website": __website__,
    "icon_author": "gasyoun",
    "icon_website": "http://led24.de/iconset/",
    "translators": ", ".join(__transs__)
}

aboutText = Template(_("""
<h2>Subconvert</h2>
<p>
Version: $version<br/>
Website: <a href="$website">$website</a><br/>
License: $license
</p>

<h3>Authors</h3>
<p>
Development: $author<br/>
Logo: $author<br/>
Icons: <a href="$icon_website">$icon_author</a><br/>
Translations: $translators
</p>

<h3>About</h3>
<p>This is Subconvert - movie subtitles editor and converter.</p>
<p>If you'd like to help at developing Subconvert, see program <a href="$website">website</a> or contact author.</p>
""")).substitute(substituteDict)

class MainWindow(QMainWindow):
    def __init__(self, args, parser):
        super(MainWindow, self).__init__()
        log.debug(_("Theme search paths: %s") % QIcon.themeSearchPaths())
        log.debug(_("Used theme name: '%s'") % QIcon.themeName())

        self.setObjectName("main_window")

        self._subtitleData = DataController(parser, self)

        self.__initGui()
        self.__initActions()
        self.__initMenuBar()
        self.__initShortcuts()
        self.__updateMenuItemsState()
        self.__connectSignals()
        self.restoreWidgetState()

        self.handleArgs(args)

    def __initGui(self):
        self._settings = SubSettings()
        self.mainWidget = QWidget(self)
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(3, 3, 3, 3)
        mainLayout.setSpacing(2)

        self.setCentralWidget(self.mainWidget)

        self._videoWidget = VideoWidget(self)
        self._tabs = SubtitleWindow.SubTabWidget(self._subtitleData,
                                                 self._videoWidget)

        mainLayout.addWidget(self._videoWidget, 1)
        mainLayout.addWidget(self._tabs, 3)

        self.statusBar()
        self.mainWidget.setLayout(mainLayout)

        self.setAcceptDrops(True)
        self.setWindowIcon(QIcon(":/img/logo.png"))
        self.setWindowTitle('Subconvert')

    def __connectSignals(self):
        self._tabs.tabChanged.connect(self.__updateMenuItemsState)
        self._tabs.tabChanged.connect(self.__updateWindowTitle)
        self._tabs.fileList.selectionChanged.connect(self.__updateMenuItemsState)
        self._subtitleData.fileAdded.connect(self.__updateMenuItemsState, Qt.QueuedConnection)
        self._subtitleData.fileChanged.connect(self.__updateMenuItemsState, Qt.QueuedConnection)
        self._subtitleData.fileRemoved.connect(self.__updateMenuItemsState, Qt.QueuedConnection)
        self._subtitleData.subtitlesAdded.connect(self.__updateMenuItemsState, Qt.QueuedConnection)
        self._subtitleData.subtitlesRemoved.connect(
            self.__updateMenuItemsState, Qt.QueuedConnection)
        self._subtitleData.subtitlesChanged.connect(
            self.__updateMenuItemsState, Qt.QueuedConnection)

    def __initActions(self):
        self._actions = {}
        af = ActionFactory(self)

        # open / save
        self._actions["openFile"] = af.create(
            "document-open", _("&Open"), _("Open subtitle file."), "ctrl+o", self.openFile)
        self._actions["saveFile"] = af.create(
            "document-save", _("&Save"), _("Save current file."), "ctrl+s", self.saveFile)
        self._actions["saveFileAs"] = af.create(
            "document-save-as",_("S&ave as..."), _("Save current file as..."), "ctrl++shift+s",
            self.saveFileAs)
        self._actions["saveAllFiles"] = af.create(
            "document-save", _("Sa&ve all"), _("Save all opened files."), None, self.saveAll)

        # app exit
        self._actions["exit"] = af.create(
            "application-exit", _("&Exit"), _("Exit Subconvert."), None, qApp.quit)

        # tab management
        self._actions["nextTab"] = af.create(
            None, None, None, "ctrl+tab", self.nextTab)
        self._actions["previousTab"] = af.create(
            None, None, None, "ctrl+shift+tab", self.previousTab)
        self._actions["closeTab"] = af.create(
            None, None, None, "ctrl+w", self.closeTab)

        # Subtitles
        self._actions["undo"] = af.create(
            "undo", _("&Undo"), None, "ctrl+z", self.undo)
        self._actions["redo"] = af.create(
            "redo", _("&Redo"), None, "ctrl+shift+z", self.redo)

        for fps in FPS_VALUES:
            fpsStr = str(fps)
            self._actions[fpsStr] = af.create(
                None, fpsStr, None, None, lambda _, fps=fps: self.changeFps(fps))

        for encoding in ALL_ENCODINGS:
            self._actions["in_%s" % encoding] = af.create(
                None, encoding, None, None,
                lambda _, enc = encoding: self.changeInputEncoding(enc))

            self._actions["out_%s" % encoding] = af.create(
                None, encoding, None, None,
                lambda _, enc = encoding: self.changeOutputEncoding(enc))

        for fmt in self._subtitleData.supportedFormats:
            self._actions[fmt.NAME] = af.create(
                None, fmt.NAME, None, None, lambda _, fmt = fmt: self.changeSubFormat(fmt))

        self._actions["linkVideo"] = af.create(
            None, _("&Link video"), None, "ctrl+l", self.linkVideo)

        self._actions["unlinkVideo"] = af.create(
            None, _("U&nlink video"), None, "ctrl+u", lambda: self._setVideoLink(None))

        self._actions["fpsFromMovie"] = af.create(
            None, _("&Get FPS"), None, "ctrl+g", self.getFpsFromMovie)

        self._actions["insertSub"] = af.create(
            "list-add", _("&Insert subtitle"), None, "insert",
            connection = lambda: self._tabs.currentPage().insertNewSubtitle())

        self._actions["addSub"] = af.create(
            "list-add", _("&Add subtitle"), None, "alt+insert",
            connection = lambda: self._tabs.currentPage().addNewSubtitle())

        self._actions["offset"] = af.create(
            None, _("&Offset"), None, None, self.offset)

        self._actions["removeSub"] = af.create(
            "list-remove", _("&Remove subtitles"), None, "delete",
            connection = lambda: self._tabs.currentPage().removeSelectedSubtitles())

        self._actions["findSub"] = af.create(
            "edit-find", _("&Find..."), None, "ctrl+f",
            connection = lambda: self._tabs.currentPage().highlight())

        # Video
        self._videoRatios = [(4, 3), (14, 9), (14, 10), (16, 9), (16, 10)]
        self._actions["openVideo"] = af.create(
            "document-open", _("&Open video"), None, "ctrl+m", self.openVideo)
        self._actions["togglePlayback"] = af.create(
            "media-playback-start", _("&Play/pause"), _("Toggle video playback"), "space",
            self._videoWidget.togglePlayback)
        self._actions["forward"] = af.create(
            "media-skip-forward", _("&Forward"), None, "ctrl+right", self._videoWidget.forward)
        self._actions["rewind"] = af.create(
            "media-skip-backward", _("&Rewind"), None, "ctrl+left", self._videoWidget.rewind)
        self._actions["frameStep"] = af.create(
            None, _("Next &frame"), _("Go to the next frame in a video"), ".",
            self._videoWidget.nextFrame)

        for ratio in self._videoRatios:
            self._actions["changeRatio_%d_%d" % ratio] = af.create(
                None, "%d:%d" % ratio, None, None,
                lambda _, r=ratio: self._videoWidget.changePlayerAspectRatio(r[0], r[1]))

        self._actions["changeRatio_fill"] = af.create(
            None, _("Fill"), None, None, self._videoWidget.fillPlayer)

        self._actions["videoJump"] = af.create(
            None, _("&Jump to subtitle"), None, "ctrl+j", self.jumpToSelectedSubtitle)

        # SPF editor
        self._actions["spfEditor"] = af.create(
            "accessories-text-editor", _("Subtitle &Properties Editor"), None, None, self.openPropertyEditor)

        # View
        self._actions["togglePlayer"] = af.create(
            None, _("&Video player"), _("Show or hide video player"), "F3", self.togglePlayer)
        self._actions["togglePanel"] = af.create(
            None, _("Side &panel"), _("Show or hide left panel"), "F4", self._tabs.togglePanel)

        # Help
        self._actions["helpPage"] = af.create(
            "help-contents", _("&Help"), _("Open &help page"), "F1", self.openHelp)
        self._actions["aboutSubconvert"] = af.create(
            "help-about", _("&About Subconvert"), None, None, self.openAboutDialog)

    def __initMenuBar(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu(_('&File'))
        fileMenu.addAction(self._actions["openFile"])
        fileMenu.addSeparator()
        fileMenu.addAction(self._actions["saveFile"])
        fileMenu.addAction(self._actions["saveFileAs"])
        fileMenu.addAction(self._actions["saveAllFiles"])
        fileMenu.addSeparator()
        fileMenu.addAction(self._actions["exit"])

        subtitlesMenu = menubar.addMenu(_("&Subtitles"))
        subtitlesMenu.addAction(self._actions["undo"])
        subtitlesMenu.addAction(self._actions["redo"])
        subtitlesMenu.addSeparator()
        subtitlesMenu.addAction(self._actions["insertSub"])
        subtitlesMenu.addAction(self._actions["addSub"])
        subtitlesMenu.addAction(self._actions["removeSub"])
        subtitlesMenu.addAction(self._actions["findSub"])
        subtitlesMenu.addSeparator()
        self._fpsMenu = subtitlesMenu.addMenu(_("&Frames per second"))
        self._fpsMenu.addSeparator()
        for fps in FPS_VALUES:
            self._fpsMenu.addAction(self._actions[str(fps)])
        self._subFormatMenu = subtitlesMenu.addMenu(_("Subtitles forma&t"))
        for fmt in self._subtitleData.supportedFormats:
            self._subFormatMenu.addAction(self._actions[fmt.NAME])
        self._inputEncodingMenu = subtitlesMenu.addMenu(_("Input &encoding"))
        self._outputEncodingMenu = subtitlesMenu.addMenu(_("&Output encoding"))
        for encoding in ALL_ENCODINGS:
            self._inputEncodingMenu.addAction(self._actions["in_%s" % encoding])
            self._outputEncodingMenu.addAction(self._actions["out_%s" % encoding])
        subtitlesMenu.addAction(self._actions["offset"])
        subtitlesMenu.addSeparator()
        subtitlesMenu.addAction(self._actions["linkVideo"])
        subtitlesMenu.addAction(self._actions["unlinkVideo"])
        subtitlesMenu.addAction(self._actions["fpsFromMovie"])
        subtitlesMenu.addSeparator()

        videoMenu = menubar.addMenu(_("&Video"))
        videoMenu.addAction(self._actions["openVideo"])
        videoMenu.addSeparator()

        playbackMenu = videoMenu.addMenu(_("&Playback"))
        playbackMenu.addAction(self._actions["togglePlayback"])
        playbackMenu.addSeparator()
        playbackMenu.addAction(self._actions["forward"])
        playbackMenu.addAction(self._actions["rewind"])
        playbackMenu.addAction(self._actions["frameStep"])

        self._ratioMenu = videoMenu.addMenu(_("&Aspect ratio"))
        for ratio in self._videoRatios:
            self._ratioMenu.addAction(self._actions["changeRatio_%d_%d" % ratio])
        self._ratioMenu.addSeparator()
        self._ratioMenu.addAction(self._actions["changeRatio_fill"])
        videoMenu.addSeparator()

        videoMenu.addAction(self._actions["videoJump"])

        viewMenu = menubar.addMenu(_("Vie&w"))
        viewMenu.addAction(self._actions["togglePlayer"])
        viewMenu.addAction(self._actions["togglePanel"])

        toolsMenu = menubar.addMenu(_("&Tools"))
        toolsMenu.addAction(self._actions["spfEditor"])

        helpMenu = menubar.addMenu(_("&Help"))
        helpMenu.addAction(self._actions["helpPage"])
        helpMenu.addAction(self._actions["aboutSubconvert"])

    def __initShortcuts(self):
        self.addAction(self._actions["nextTab"])
        self.addAction(self._actions["previousTab"])
        self.addAction(self._actions["closeTab"])

    def cleanup(self):
        self._videoWidget.close()

    def __getAllSubExtensions(self):
        formats = self._subtitleData.supportedFormats
        exts = [_('Default')]
        exts.extend(set([ f.EXTENSION for f in formats ]))
        exts.sort()
        return exts

    def _writeFile(self, filePath, newFilePath=None):
        if newFilePath is None:
            newFilePath = filePath

        data = self._subtitleData.data(filePath)
        converter = SubConverter()
        content = converter.convert(data.outputFormat, data.subtitles)

        if File.exists(newFilePath):
            file_ = File(newFilePath)
            file_.overwrite(content, data.outputEncoding)
        else:
            File.write(newFilePath, content, data.outputEncoding)
        self._subtitleData.setCleanState(filePath)
        self.__updateMenuItemsState()

    def __updateWindowTitle(self):
        tab = self._tabs.currentPage()
        if tab.isStatic:
            self.setWindowTitle("Subconvert")
        else:
            self.setWindowTitle("%s - Subconvert" % tab.name)

    def _openFiles(self, paths, encoding):
        unsuccessfullFiles = []
        for filePath in paths:
            # TODO: separate reading file and adding to the list.
            # TODO: there should be readDataFromFile(filePath, properties=None),
            # TODO: which should set default properties from Subtitle Properties File
            command = NewSubtitles(filePath, encoding)
            try:
                self._subtitleData.execute(command)
            except DoubleFileEntry:
                pass # file already opened
            except Exception as e:
                log.exception(e)
                unsuccessfullFiles.append("%s: %s" % (filePath, str(e)))
        if len(unsuccessfullFiles) > 0:
            dialog = CannotOpenFilesMsg(self)
            dialog.setFileList(unsuccessfullFiles)
            dialog.exec()

    def _setVideoLink(self, videoPath):
        currentTab = self._tabs.currentPage()
        if currentTab.isStatic:
            currentTab.changeSelectedFilesVideoPath(videoPath)
        else:
            currentTab.changeVideoPath(videoPath)

    @pyqtSlot()
    def __updateMenuItemsState(self):
        tab = self._tabs.currentPage()
        dataAvailable = self._subtitleData.count() != 0
        anyTabOpen = tab is not None
        tabIsStatic = tab.isStatic if anyTabOpen else False
        if tabIsStatic:
            cleanState = False
            anyItemSelected = len(tab.selectedItems) > 0
        else:
            cleanState = tab.history.isClean()
            anyItemSelected = False

        canUndo = (tabIsStatic and anyItemSelected) or (not tabIsStatic and tab.history.canUndo())
        canRedo = (tabIsStatic and anyItemSelected) or (not tabIsStatic and tab.history.canRedo())
        canEdit = (tabIsStatic and anyItemSelected) or (not tabIsStatic)

        self._actions["saveAllFiles"].setEnabled(dataAvailable)
        self._actions["saveFile"].setEnabled(not tabIsStatic and not cleanState)
        self._actions["saveFileAs"].setEnabled(not tabIsStatic)

        self._actions["undo"].setEnabled(canUndo)
        self._actions["redo"].setEnabled(canRedo)
        self._fpsMenu.setEnabled(canEdit)
        self._subFormatMenu.setEnabled(canEdit)
        self._inputEncodingMenu.setEnabled(canEdit)
        self._outputEncodingMenu.setEnabled(canEdit)
        self._actions["offset"].setEnabled(canEdit)

        self._actions["linkVideo"].setEnabled(canEdit)
        self._actions["unlinkVideo"].setEnabled(canEdit)
        self._actions["fpsFromMovie"].setEnabled(canEdit)

        self._actions["insertSub"].setEnabled(not tabIsStatic)
        self._actions["addSub"].setEnabled(not tabIsStatic)
        self._actions["removeSub"].setEnabled(not tabIsStatic)
        self._actions["findSub"].setEnabled(not tabIsStatic)

        self._actions["videoJump"].setEnabled(not tabIsStatic)

    def closeEvent(self, ev):
        self.saveWidgetState()

    def saveWidgetState(self):
        self._settings.setGeometry(self, self.saveGeometry())
        self._settings.setState(self, self.saveState())

        self._videoWidget.saveWidgetState(self._settings)
        self._tabs.saveWidgetState(self._settings)

    def restoreWidgetState(self):
        self.restoreGeometry(self._settings.getGeometry(self))
        self.restoreState(self._settings.getState(self))

        self._videoWidget.restoreWidgetState(self._settings)
        self._tabs.restoreWidgetState(self._settings)

    def handleArgs(self, args):
        self._openFiles(args.files, args.inputEncoding)

    def nextTab(self):
        if self._tabs.count() > 0:
            index = self._tabs.currentIndex() + 1
            if index > self._tabs.count() - 1:
                index = 0
            self._tabs.showTab(index)

    def previousTab(self):
        if self._tabs.count() > 0:
            index = self._tabs.currentIndex() - 1
            if index < 0:
                index = self._tabs.count() - 1
            self._tabs.showTab(index)

    def closeTab(self):
        if self._tabs.count() > 0:
            index = self._tabs.currentIndex()
            self._tabs.closeTab(index)

    def openFile(self):
        sub_extensions = self.__getAllSubExtensions()
        str_sub_exts = ' '.join(['*.%s' % ext for ext in sub_extensions[1:]])

        fileDialog = FileDialog(
            parent = self,
            caption = _("Open file"),
            directory = self._settings.getLatestDirectory(),
            filter = _("Subtitles (%s);;All files (*)") % str_sub_exts
        )
        fileDialog.addEncodings(True)
        fileDialog.setFileMode(QFileDialog.ExistingFiles)

        if fileDialog.exec():
            filenames = fileDialog.selectedFiles()
            encoding = fileDialog.getEncoding()
            self._settings.setLatestDirectory(os.path.dirname(filenames[0]))
            self._openFiles(filenames, encoding)


    @pyqtSlot()
    def saveFile(self, newFilePath = None):
        currentTab = self._tabs.currentPage()
        try:
            self._writeFile(currentTab.filePath, newFilePath)
        except SubException as msg:
            dialog = QMessageBox(self)
            dialog.setIcon(QMessageBox.Critical)
            dialog.setWindowTitle(_("Couldn't save file"))
            dialog.setText(str(msg))
            dialog.exec()

    @pyqtSlot()
    def saveFileAs(self):
        fileDialog = FileDialog(
            parent = self,
            caption = _('Save as...'),
            directory = self._settings.getLatestDirectory()
        )

        currentTab = self._tabs.currentPage()

        fileDialog.addFormats(self._subtitleData.supportedFormats)
        fileDialog.setSubFormat(currentTab.outputFormat)
        fileDialog.addEncodings(False)
        fileDialog.setEncoding(currentTab.outputEncoding)
        fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        fileDialog.setFileMode(QFileDialog.AnyFile)

        if fileDialog.exec():
            newFilePath = fileDialog.selectedFiles()[0]
            data = currentTab.data

            outputFormat = fileDialog.getSubFormat()
            outputEncoding = fileDialog.getEncoding() # user can overwrite previous output encoding

            if data.outputFormat != outputFormat or data.outputEncoding != outputEncoding:
                # save user changes
                data.outputFormat = outputFormat
                data.outputEncoding = outputEncoding

            if self._subtitleData.fileExists(newFilePath):
                command = ChangeData(newFilePath, data, _("Overwritten by %s") % currentTab.name)
            else:
                command = CreateSubtitlesFromData(newFilePath, data)
            self._subtitleData.execute(command)
            self._tabs.openTab(newFilePath)

            self.saveFile(newFilePath)
            self._settings.setLatestDirectory(os.path.dirname(newFilePath))

    def saveAll(self):
        dialog = MessageBoxWithList(self)
        dialog.setIcon(QMessageBox.Critical)


        # TODO
        # When asked to save file, it should be should checked if it's parsed and parse it if it's
        # not (in future the parsing moment might be moved to increase responsibility when opening
        # a lot of files - i.e. only a file list will be printed and files will be actually parsed
        # on their first use (e.g. on tab open, fps change etc.). I'll have to think about it).
        # END OF TODO
        for filePath in self._tabs.fileList.filePaths:
            try:
                if not self._subtitleData.isCleanState(filePath):
                    self._writeFile(filePath)
            except SubException as msg:
                dialog.addToList(str(msg))

        if dialog.listCount() > 0:
            dialog.setWindowTitle(P_(
                "Error on saving a file",
                "Error on saving files",
                dialog.listCount()
                ))
            dialog.setText(P_(
                "Following error occured when trying to save a file:",
                "Following errors occured when trying to save files:",
                dialog.listCount()
                ))
            dialog.exec()

    def undo(self):
        currentTab = self._tabs.currentPage()
        if currentTab.isStatic:
            currentTab.undoSelectedFiles()
        else:
            currentTab.history.undo()

    def redo(self):
        currentTab = self._tabs.currentPage()
        if currentTab.isStatic:
            currentTab.redoSelectedFiles()
        else:
            currentTab.history.redo()

    def changeInputEncoding(self, encoding):
        currentTab = self._tabs.currentPage()
        if currentTab.isStatic:
            currentTab.changeSelectedFilesInputEncoding(encoding)
        else:
            currentTab.changeInputEncoding(encoding)

    def changeOutputEncoding(self, encoding):
        currentTab = self._tabs.currentPage()
        if currentTab.isStatic:
            currentTab.changeSelectedFilesOutputEncoding(encoding)
        else:
            currentTab.changeOutputEncoding(encoding)

    def changeSubFormat(self, fmt):
        currentTab = self._tabs.currentPage()
        if currentTab.isStatic:
            currentTab.changeSelectedFilesFormat(fmt)
        else:
            currentTab.changeSubFormat(fmt)

    def offset(self):
        currentTab = self._tabs.currentPage()

        # fps isn't used, but we need one to init starting FrameTime
        dialog = OffsetDialog(self, FrameTime(25, seconds=0))
        if dialog.exec():
            if currentTab.isStatic:
                currentTab.offsetSelectedFiles(dialog.frametime.fullSeconds)
            else:
                currentTab.offset(dialog.frametime.fullSeconds)

    def changeFps(self, fps):
        currentTab = self._tabs.currentPage()
        if currentTab.isStatic:
            currentTab.changeSelectedFilesFps(fps)
        else:
            currentTab.changeFps(fps)

    def togglePlayer(self):
        if self._videoWidget.isHidden():
            self._videoWidget.show()
        else:
            self._videoWidget.hide()

    def getFpsFromMovie(self):
        currentTab = self._tabs.currentPage()
        if currentTab.isStatic:
            currentTab.detectSelectedFilesFps()
        else:
            currentTab.detectFps()

    def openVideo(self):
        movieExtensions = "%s%s" % ("*.", ' *.'.join(File.MOVIE_EXTENSIONS))
        fileDialog = FileDialog(
            parent = self,
            caption = _("Select a video"),
            directory = self._settings.getLatestDirectory(),
            filter = _("Video files (%s);;All files (*)") % movieExtensions)
        fileDialog.setFileMode(QFileDialog.ExistingFile)
        if fileDialog.exec():
            movieFilePath = fileDialog.selectedFiles()[0]
            self._videoWidget.openFile(movieFilePath)

    def jumpToSelectedSubtitle(self):
        currentTab = self._tabs.currentPage()
        subtitleList = currentTab.selectedSubtitles()
        if len(subtitleList) > 0:
            self._videoWidget.jumpTo(subtitleList[0].start)

    def openPropertyEditor(self):
        editor = PropertyFileEditor(self._subtitleData.supportedFormats, self)
        editor.exec()

    def openAboutDialog(self):
        spacer = QSpacerItem(650, 0)
        dialog = QMessageBox(self)
        dialog.setIconPixmap(QPixmap(":/img/logo.png"))
        dialog.setWindowTitle(_("About Subconvert"))
        dialog.setText(aboutText)

        dialogLayout = dialog.layout()
        dialogLayout.addItem(spacer, dialogLayout.rowCount(), 0, 1, dialogLayout.columnCount())
        dialog.exec()

    def openHelp(self):
        url = "https://github.com/mgoral/subconvert/wiki"
        if QDesktopServices.openUrl(QUrl(url)) is False:
            dialog = QMessageBox(self)
            dialog.setIcon(QMessageBox.Critical)
            dialog.setWindowTitle(_("Couldn't open URL"))
            dialog.setText(_("""Failed to open URL: <a href="%(url)s">%(url)s</a>.""") %
                {"url": url})
            dialog.exec()

    def dragEnterEvent(self, event):
        mime = event.mimeData()

        # search for at least local file in dragged urls (and accept drag event only in that case)
        if mime.hasUrls():
            urls = mime.urls()
            for url in urls:
                if url.isLocalFile() and os.path.isfile(url.toLocalFile()):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        mime = event.mimeData()
        urls = mime.urls()

        subPaths = []
        moviePaths = []
        for url in urls:
            if url.isLocalFile():
                filePath = url.toLocalFile()
                if not os.path.isdir(filePath):
                    fileName, fileExtension = os.path.splitext(filePath)

                    if fileExtension.strip('.').lower() in File.MOVIE_EXTENSIONS:
                        moviePaths.append(filePath)
                    else:
                        subPaths.append(filePath)

        # open all subtitles and only the first movie
        if len(moviePaths) > 0:
            self._videoWidget.openFile(moviePaths[0])
        if len(subPaths) > 0:
            self._openFiles(subPaths, None)

    def linkVideo(self):
        movieExtensions = "%s%s" % ("*.", ' *.'.join(File.MOVIE_EXTENSIONS))
        fileDialog = FileDialog(
            parent = self,
            caption = _("Select a video"),
            directory = self._settings.getLatestDirectory(),
            filter = _("Video files (%s);;All files (*)") % movieExtensions)
        fileDialog.setFileMode(QFileDialog.ExistingFile)
        if fileDialog.exec():
            movieFilePath = fileDialog.selectedFiles()[0]
            self._setVideoLink(movieFilePath)
