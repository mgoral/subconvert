#!/usr/bin/env python3
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

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSlider, QPushButton, QSizePolicy
from PyQt5.QtWidgets import QAbstractSlider, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from subconvert.parsing.FrameTime import FrameTime
from subconvert.utils.VideoPlayer import VideoPlayer, VideoPlayerException
from subconvert.utils.SubSettings import SubSettings

from subconvert.utils.Locale import _

class VideoWidget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._initWidget()
        self.changePlayerAspectRatio(4, 3)
        self._movieFrame = 0
        self._modulo = 4 # CPU savior

        # Trivia: setting layout changes widgets winId, so MPlayer would be unusable if initialised
        # before.
        self._player = VideoPlayer(self._playerWidget)

        # connect some signals
        self._player.positionChanged.connect(self._moviePositionChanged)
        self._player.videoDataChanged.connect(self._dataAvailabilityChanged)
        self._player.playbackChanged.connect(self._playButton.setChecked)
        self._playButton.clicked.connect(self._playButtonToggled)
        self._slider.actionTriggered.connect(self._sliderActionHandle)

    def close(self):
        self._player = None # will be garbage collected
        super().close()

    def show(self):
        super().show()

    def hide(self):
        self._player.pause()
        super().hide()

    def play(self):
        self._modulo = 4
        self._player.play()

    def pause(self):
        self._modulo = 1
        self._player.pause()
        self._slider.setValue(self._movieFrame)

    def togglePlayback(self):
        if self._player.isPlaying:
            self.pause()
        else:
            self.play()

    def nextFrame(self):
        self.pause()
        self._player.frameStep()

    def forward(self):
        self._player.seek(5.0)

    def rewind(self):
        self._player.seek(-5.0)

    def fastForward(self):
        self._player.seek(30.0)

    def fastRewind(self):
        self._player.seek(-30.0)

    def jumpTo(self, frametime):
        position = frametime.fullSeconds
        self._changePosition(position)

    @property
    def position(self):
        if not self.movieProperties.isAllDataSet():
            return None
        return FrameTime(fps = self.movieProperties.fps, frames = self._movieFrame)

    def _changePosition(self, position):
        if not isinstance(position, float):
            if self._player.videoData.fps is not None:
                position = float(position) / self._player.videoData.fps
        self._player.jump(position)

    def openFile(self, filePath):
        self._player.loadFile(filePath)
        self._slider.setDisabled(False)

    def loadSubtitles(self, subtitles):
        pass

    @property
    def movieProperties(self):
        return self._player.videoData

    @property
    def videoPath(self):
        return self._player.path

    def changePlayerAspectRatio(self, width, height):
        ratio = float(width) / float(height)
        if ratio > 0:
            self._ratio = ratio
            self._repaintPlayer()

    def fillPlayer(self):
        self._ratio = 0
        self._repaintPlayer()

    def resizeEvent(self, event):
        self._repaintPlayer()
        super().resizeEvent(event)

    def _repaintPlayer(self):
        if self._ratio == 0:
            margin = 0
        else:
            newWidth = self._playerWidget.height() * self._ratio
            margin = int((self._background.width() - newWidth) / 2)
            if margin < 0:
                margin = 0
        self._background.layout().setContentsMargins(margin, 0, margin, 0)

    def _initWidget(self):
        self.setObjectName("video_player")

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # Separate background to keep black background when playerWidget resizes
        self._background = QWidget(self)
        self._background.setStyleSheet("background: black")
        mainLayout.addWidget(self._background, 1)

        self._playerWidget = QWidget(self)

        backgroundLayout = QHBoxLayout()
        self._background.setLayout(backgroundLayout)
        backgroundLayout.addWidget(self._playerWidget)

        controls = self._initControlPanel()
        mainLayout.addLayout(controls)

        self.setLayout(mainLayout)

    def _initControlPanel(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        self._playButton = QPushButton(QIcon.fromTheme("media-playback-start"), "", self)
        self._playButton.setCheckable(True)
        self._playButton.setFocusPolicy(Qt.NoFocus)
        self._playButton.setToolTip(_("Play/Pause"))
        self._slider = QSlider(Qt.Horizontal, self)
        self._slider.setDisabled(True)
        self._timeLabel = QLabel("0:00:00.000", self)
        layout.addWidget(self._playButton)
        layout.addWidget(self._slider)
        layout.addWidget(self._timeLabel)
        layout.addSpacing(5)
        return layout

    def saveWidgetState(self, settings):
        settings = SubSettings()
        settings.setHidden(self, self.isHidden())

    def restoreWidgetState(self, settings):
        if settings.getHidden(self) is True:
            self.hide()
        else:
            self.show()

    def _moviePositionChanged(self, frame):
        if not self._slider.isSliderDown():
            self._movieFrame = frame
            if frame % self._modulo == 0:
                self._slider.setValue(self._movieFrame)
                fps = self._player.videoData.fps
                ft = FrameTime(fps, frames=frame)
                self._timeLabel.setText(ft.toStr())

    def _sliderActionHandle(self, action):
        if action == QAbstractSlider.SliderPageStepAdd:
            self._player.seek(1.0)
        elif action == QAbstractSlider.SliderPageStepSub:
            self._player.seek(-1.0)
        elif action == QAbstractSlider.SliderSingleStepAdd:
            self.forward()
        elif action == QAbstractSlider.SliderSingleStepSub:
            self.rewind()
        elif action == QAbstractSlider.SliderMove:
            position = self._slider.sliderPosition()
            self._changePosition(position)
            if self._slider.isSliderDown() and self._player.videoData.fps is not None:
                fps = self._player.videoData.fps
                ft = FrameTime(fps, frames=position)
                self._timeLabel.setText(ft.toStr())

    def _dataAvailabilityChanged(self, val):
        if val is True:
            fps = self._player.videoData.fps
            length = self._player.videoData.length
            self._slider.setRange(0, int(fps * length))
        else:
            self._slider.setRange(0, 99)

    def _playButtonToggled(self, checked):
        if checked is True:
            self.play()
        else:
            self.pause()
