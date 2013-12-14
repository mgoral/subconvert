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

from subconvert.utils.SubException import SubAssert
from subconvert.utils.Locale import _

class FrameTime():
    """Class defining a FrameTime object which consists of frame and time metrics (and fps as well)."""

    def __init__(self, fps, seconds=None, frames=None, time=None):
        """Constructs FrameTime object with a given FPS value. Constructor accepts only one value
        from the following ones: time (properly formatted string), number of frames (int) or number
        of total seconds (float, with miliseconds specified after decimal point).

        Examples:
        FrameTime(time="1:01:01.100", fps=25)
        FrameTime(frames=100, fps=25)
        FrameTime(seconds="3600.01", fps=25)
        """

        if fps <= 0:
            raise ValueError("Incorrect FPS value: %s." % fps)

        self._fps = float(fps)
        if frames is None and time is None and seconds is None:
            self._frame = 0
            self._full_seconds = 0.0
            self._miliseconds = 0
            self._seconds = 0
            self._minutes = 0
            self._hours = 0
        else:
            exclusiveArgs = [frames, time, seconds]
            if exclusiveArgs.count(None) != 2:
                raise AttributeError("FrameTime can obly be initialized by one type.")

            if frames is not None:
                self.__setFrame__(int(frames))
            elif time is not None:
                self.__setTime__(str(time))
            if seconds is not None:
                self.__setSeconds__(float(seconds))

    def clone(self):
        other = FrameTime(fps = self.fps)
        other._frame = self._frame
        other._full_seconds = self._full_seconds
        other._miliseconds = self._miliseconds
        other._seconds = self._seconds
        other._minutes = self._minutes
        other._hours = self._hours
        return other

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, newFps):
        if newFps > 0:
            self._fps = float(newFps)
        else:
            raise ValueError("Incorrect FPS value: %s." % newFps)
        self.__setFrame__(self._full_seconds * self._fps)

    @property
    def frame(self):
        """Get Frame (and FPS) value)"""
        return int(round(self._frame))

    @property
    def fullSeconds(self):
        return self._full_seconds

    @property
    def time(self):
        return { \
            'hours': self._hours, \
            'minutes': self._minutes, \
            'seconds': self._seconds, \
            'miliseconds': self._miliseconds
        }

    def toStr(self, strType="time"):
        """Convert FrameTime to string representation"""
        if strType == "time":
            return "%d:%02d:%02d.%03d" % (self._hours, self._minutes, self._seconds, self._miliseconds)
        elif strType == "frame":
            return "%s" % int(round(self._frame))
        else:
            raise AttributeError("Incorrect string type: '%s'" % strType)

    def __setTime__(self, value):
        time = re.match(r"(?P<h>\d+):(?P<m>[0-5][0-9]):(?P<s>[0-5][0-9])(?:$|\.(?P<ms>\d{1,3}))", value)
        if time is None:
            raise ValueError("Incorrect time format.")

        if time.group('ms') is not None:
            # ljust explenation:
            # 10.1 != 10.001
            # 10.1 == 10.100
            self._miliseconds = int(time.group('ms').ljust(3, '0'))
        else:
            self._miliseconds = 0
        self._seconds = int(time.group('s'))
        self._minutes = int(time.group('m'))
        self._hours = int(time.group('h'))
        self._full_seconds = (3600*self._hours + 60*self._minutes + self._seconds + float(self._miliseconds)/1000)
        self._frame = self._fps * self._full_seconds

    def __setSeconds__(self, seconds):
        if seconds >= 0:
            self._full_seconds = seconds
            self._frame = seconds * self._fps
        else:
            raise ValueError("Incorrect seconds value.")

        self._hours = int(seconds / 3600)
        seconds = round(seconds - self._hours * 3600, 3)
        self._minutes = int(seconds / 60)
        seconds = round(seconds - self._minutes * 60, 3)
        self._seconds = int(seconds)
        self._miliseconds = int(round(1000 * (seconds - self._seconds)))

    def __setFrame__(self, frame):
        if frame >= 0:
            self.__setSeconds__(frame / self._fps)
        else:
            raise ValueError("Incorrect frame value.")

    def __eq__(self, other):
        SubAssert(self._fps == other._fps, _("FPS values are not equal"))
        return self._full_seconds == other._full_seconds

    def __ne__(self, other):
        SubAssert(self._fps == other._fps, _("FPS values are not equal"))
        return self._full_seconds != other._full_seconds

    def __lt__(self, other):
        SubAssert(self._fps == other._fps, _("FPS values are not equal"))
        return self._full_seconds < other._full_seconds

    def __gt__(self, other):
        SubAssert(self._fps == other._fps, _("FPS values are not equal"))
        return self._full_seconds > other._full_seconds

    def __add__(self, other):
        """Defines FrameTime + FrameTime"""
        SubAssert(self._fps == other._fps, _("FPS values are not equal"))
        result = self._full_seconds + other._full_seconds
        return FrameTime(fps = self._fps, seconds = result)

    def __sub__(self, other):
        """Defines FrameTime - FrameTime"""
        SubAssert(self._fps == other._fps, _("FPS values are not equal"))
        SubAssert(self._full_seconds >= other._full_seconds,
            _("Cannot substract higher time from lower"))
        result = self._full_seconds - other._full_seconds
        return FrameTime(fps = self._fps, seconds = result)

    def __mul__(self, val):
        """Defines FrameTime * number"""
        result = self._full_seconds * val
        return FrameTime(fps = self._fps, seconds = result)

    def __div__(self, val):
        """Defines FrameTime / number"""
        result = self._full_seconds / val
        return FrameTime(fps = self._fps, seconds = result)

    def __str__(self):
        """Defines str(FrameTime)"""
        return "t: %s:%s:%s.%s; f: %s" % \
            (self._hours, self._minutes, self._seconds, self._miliseconds, self.frame)


