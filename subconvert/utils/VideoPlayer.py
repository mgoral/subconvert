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

import re
import logging

from PyQt5.QtCore import pyqtSignal, QObject, QProcess

from subconvert.utils.Locale import _

log = logging.getLogger('Subconvert.%s' % __name__)

class VideoPlayerException(Exception):
    pass

class VideoData:
    def __init__(self):
        self.reset()

    def reset(self):
        self.bitrate = None
        self.length = None
        self.fps = None
        self.width = None
        self.height = None

    def isAllDataSet(self):
        return None not in (self.bitrate, self.length, self.fps, self.width, self.height)

    def _fetchData(self, input_):
        pass

class VideoParameters:
    def __init__(self):
        self.position = 0.0

# For a reference about MPlayer Slave Mode Protocol, see:
# http://www.mplayerhq.hu/DOCS/tech/slave.txt
class VideoPlayer(QObject):
    positionChanged = pyqtSignal(int)
    playbackChanged = pyqtSignal(bool)
    playerStopped = pyqtSignal()
    videoDataChanged = pyqtSignal(bool) # True if all data is available

    def __init__(self, window, parent = None):
        super().__init__(parent)
        self._executable = "mplayer"
        self._window = window
        self._filePath = None
        self._proc = QProcess(self)
        self._isPlaying = False

        self._data = VideoData()
        self._params = VideoParameters()

        # connect some signals
        self._proc.readyReadStandardOutput.connect(self._readStdout)
        self._proc.readyReadStandardError.connect(self._readStdErr)
        self._compileRegex()

    def _compileRegex(self):
        # bunch of used regex patterns. Note that sometimes it's not necessary to use regex to
        # parse MPlayer output
        self._commandLinePattern = re.compile(r"""
            V:\ *?(?P<time>\d+\.\d)     # fallback time (always available). Note spaces after V:
            .*                          # anything between time and frame number
            \d+/\s*?(?P<frame>\d+)\     # frame number (not always available). Note that space is
                                        # the last character
            """, re.X)
        self._idVideoBitratePattern = re.compile(r"^ID_VIDEO_BITRATE=(?P<bitrate>\d+)")
        self._idWidthPattern = re.compile(r"^ID_VIDEO_WIDTH=(?P<width>\d+)")
        self._idHeightPattern= re.compile(r"^ID_VIDEO_HEIGHT=(?P<height>\d+)")
        self._idFpsPattern= re.compile(r"^ID_VIDEO_FPS=(?P<fps>[0-9.]+)")
        self._idLengthPattern= re.compile(r"ID_LENGTH=(?P<length>[0-9.]+)")

    def __del__(self):
        log.debug(_("Closing VideoPlayer"))
        self._kill()

    @property
    def isPlaying(self):
        return self._isPlaying

    @property
    def videoData(self):
        """Fetches meta data for loaded file"""
        return self._data

    def loadFile(self, filePath):
        """Loads a file"""
        self._filePath = filePath

        if self._proc.state() != QProcess.Running:
            self._kill()
            self._run(self._filePath)
        else:
            self._execute("pausing_keep_force pt_step 1")
            self._execute("get_property pause")
            self._execute("loadfile \"%s\"" % self._filePath)

        self._data.reset()
        self.videoDataChanged.emit(False)
        self._changePlayingState(True)

    def play(self):
        """Starts a playback"""
        if self._proc.state() == QProcess.Running:
            if self.isPlaying is False:
                self._execute("pause")
                self._changePlayingState(True)
        elif self._filePath is not None:
            self._kill()
            self._run(self._filePath)
            self._changePlayingState(True)

    def jump(self, timestamp):
        """Jumps to a given position in a movie"""
        self._execute("pausing_keep seek %.1f 2" % timestamp)

    def pause(self):
        """Pauses playback"""
        if self.isPlaying is True:
            self._execute("pause")
            self._changePlayingState(False)

    def stop(self):
        """Stops playback"""
        if self.isPlaying is True:
            self._execute("stop")
            self._changePlayingState(False)

    def seek(self, val):
        """Seeks +/- given seconds.miliseconds"""
        self._execute("pausing_keep seek %.1f 0" % val)

    def frameStep(self):
        self._execute("frame_step")

    def mute(self):
        """Mutes autio"""
        self._execute("mute")

    def setVolume(self, volume):
        """Changes volume"""
        val = float(val)
        cmd = "volume %s" % val
        self._execute(cmd)

    @property
    def path(self):
        return self._filePath

    def _run(self, filepath):
        arguments = [
            "-slave",
            "-noautosub",
            "-identify",
            "-nomouseinput",
            "-osdlevel", "0",
            "-input", "nodefault-bindings",
            "-noconfig", "all",
            "-wid", str(int(self._window.winId())),
            filepath
        ]

        self._proc.start(self._executable, arguments)
        if self._proc.waitForStarted() is False:
            raise VideoPlayerException("Cannot start MPlayer!")

    def _kill(self):
        log.debug(_("Killing MPlayer process"))
        self._proc.kill()
        if self._proc.waitForFinished() is False:
            log.debug(_("Cannot kill MPlayer process (if you killed Subconvert this is not "
                "necessary an error)!"))

    def _execute(self, cmd):
        if self._proc.state() == QProcess.Running:
            if cmd is not None and cmd != "":
                procCmd = "%s%s" % (str(cmd), "\n")
                self._proc.write(procCmd.encode('utf-8'))

    def _changePlayingState(self, state):
        if state != self._isPlaying:
            self._isPlaying = state
            self.playbackChanged.emit(state)

    def _readStdout(self):
        message = bytes(self._proc.readAllStandardOutput()).decode()
        log.debug("stderr: %s", message)
        self._parseMessage(message)

    def _readStdErr(self):
        message = bytes(self._proc.readAllStandardError()).decode()
        log.debug("stdout: %s", message)
        self._parseMessage(message)

    def _parseMessage(self, message):
        lines = message.splitlines()
        for line in lines:
            if line.startswith("A:") or line.startswith("V:"):
                self._parsePositionChange(line)
            elif line.startswith("ID_"):
                self._parseMovieInfo(line)

    def _parsePositionChange(self, message):
        if self.videoData.isAllDataSet():
            pos = self._commandLinePattern.search(message)
            if pos is not None:
                frame = int(pos.group("frame"))
                time = float(pos.group("time"))
                if frame == 0:
                    frame = int(time * self.videoData.fps)
                self.positionChanged.emit(frame)

    def _parseMovieInfo(self, message):
        if message.startswith("ID_VIDEO_BITRATE"):
            bitrate = self._idVideoBitratePattern.search(message).group("bitrate")
            self._data.bitrate = int(bitrate)
            self._dataChanged()
        elif message.startswith("ID_VIDEO_WIDTH"):
            width = self._idWidthPattern.search(message).group("width")
            self._data.width = int(width)
            self._dataChanged()
        elif message.startswith("ID_VIDEO_HEIGHT"):
            height = self._idHeightPattern.search(message).group("height")
            self._data.height = int(height)
            self._dataChanged()
        elif message.startswith("ID_VIDEO_FPS"):
            fps = self._idFpsPattern.search(message).group("fps")
            self._data.fps = float(fps)
            self._dataChanged()
        elif message.startswith("ID_LENGTH"):
            length = self._idLengthPattern.search(message).group("length")
            self._data.length = float(length)
            self._dataChanged()
        elif message.startswith("ID_PAUSED"):
            self._changePlayingState(False)
        elif message.startswith("ID_EXIT"):
            self._changePlayingState(False)
            self.playerStopped.emit()

    def _dataChanged(self):
        if self._data.isAllDataSet():
            self.videoDataChanged.emit(True)

