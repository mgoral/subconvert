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

import json
from subconvert.parsing.Formats import *
from subconvert.utils.SubFile import File

class SubtitleProperties:
    __JSON_ENCODING = "UTF-8"

    def __init__(self, subFormats, filePath = None):
        self._availableFormats = subFormats

        self._autoInputEncoding = True
        self._autoFps = True
        self._fps = 23.976
        self._inputEncoding = None
        self._outputEncoding = None
        self._changeEncoding = False
        self._outputFormat = SubFormat

        if filePath is not None:
            self.load(filePath)

    def _setBoolean(self, val):
        if val not in (True, False):
            raise TypeError("Expected boolean!")
        return bool(val)

    @property
    def autoInputEncoding(self):
        return self._autoInputEncoding

    @autoInputEncoding.setter
    def autoInputEncoding(self, val):
        self._autoInputEncoding = self._setBoolean(val)

    @property
    def autoFps(self):
        return self._autoFps

    @autoFps.setter
    def autoFps(self, val):
        self._autoFps = self._setBoolean(val)

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, val):
        self._fps = float(val)

    @property
    def inputEncoding(self):
        return self._inputEncoding

    @inputEncoding.setter
    def inputEncoding(self, val):
        if val is None:
            self._inputEncoding = val
        else:
            self._inputEncoding = str(val)

    @property
    def outputEncoding(self):
        return self._outputEncoding

    @outputEncoding.setter
    def outputEncoding(self, val):
        if val is None:
            self._outputEncoding = val
        else:
            self._outputEncoding = str(val)

    @property
    def changeEncoding(self):
        return self._changeEncoding

    @changeEncoding.setter
    def changeEncoding(self, val):
        self._changeEncoding = self._setBoolean(val)

    @property
    def outputFormat(self):
        return self._outputFormat

    @outputFormat.setter
    def outputFormat(self, val):
        if not issubclass(val, SubFormat):
            raise TypeError("Incorrect outputFormat type!")
        self._outputFormat = val

    def load(self, filePath):
        with open(filePath, 'r') as f:
            obj = json.load(f)
            self._fromJson(obj)


    def save(self, filePath):
        with open(filePath, 'w') as f:
            json.dump(self._toJson(), f)

    def _toJson(self):
        serializable = {}
        serializable["autoFps"] = self._autoFps
        serializable["fps"] = self._fps
        serializable["autoInputEncoding"] = self._autoInputEncoding
        serializable["inputEncoding"] = self._inputEncoding
        serializable["outputEncoding"] = self._outputEncoding
        serializable["changeEncoding"] = self._changeEncoding
        serializable["outputFormat"] = self._outputFormat.NAME
        return serializable

    def _fromJson(self, data):
        self._autoFps = bool(data["autoFps"])
        self._fps = float(data["fps"])
        self._autoInputEncoding = bool(data["autoInputEncoding"])
        self._inputEncoding = str(data["inputEncoding"])
        self._outputEncoding = str(data["outputEncoding"])
        self._changeEncoding = bool(data["changeEncoding"])
        self._outputFormat = self._formatFromString(str(data["outputFormat"]))

    # Convert a given string to format type or raise an exception if it's not possible.
    def _formatFromString(self, fmt):
        for availableFormat in self._availableFormats:
            if fmt.lower() == availableFormat.NAME.lower():
                return availableFormat
        raise LookupError(_("Unknown format: %s") % fmt)


class PropertiesFileApplier:
    def __init__(self, subProperties):
        self._subProperties = subProperties

    def applyFor(self, filePath, data):
        subtitleFile = File(filePath)

        # fps
        if self._subProperties.autoFps:
            videoInfo = subtitleFile.detectFps(default=self._subProperties.fps)
            data.subtitles.changeFps(videoInfo.fps)
            data.fps = videoInfo.fps
            data.videoPath = videoInfo.videoPath
        else:
            data.subtitles.changeFps(self._subProperties.fps)
            data.fps = self._subProperties.fps
            data.videoPath = None

        # input encoding
        inputEncoding = self._subProperties.inputEncoding
        if self._subProperties.autoInputEncoding:
            inputEncoding = subtitleFile.detectEncoding().lower()
        if data.inputEncoding != inputEncoding:
            data.encode(inputEncoding)

        # output encoding
        if self._subProperties.changeEncoding:
            data.outputEncoding = self._subProperties.outputEncoding
        else:
            data.outputEncoding = self._subProperties.inputEncoding

        # subtitle format
        data.outputFormat = self._subProperties.outputFormat

        return data
