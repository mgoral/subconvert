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

import re
import functools

from subconvert.utils.SubException import SubAssert
from subconvert.utils.Locale import _

class FrameTimeType:
    """Used to determine if frame or time should be changed on FPS change."""
    Undefined = 0
    Frame = 1
    Time = 2

@functools.total_ordering
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
            self._origin = FrameTimeType.Undefined
            self._frame = 0
            self._full_seconds = 0.0
        else:
            exclusiveArgs = [frames, time, seconds]
            if exclusiveArgs.count(None) != 2:
                raise AttributeError("FrameTime can obly be initialized by one type.")

            if frames is not None:
                self._origin = FrameTimeType.Frame
                self.__setFrame__(int(frames))
            elif time is not None:
                self._origin = FrameTimeType.Time
                self.__setTime__(str(time))
            elif seconds is not None:
                self._origin = FrameTimeType.Time
                self.__setSeconds__(float(seconds))

    def clone(self):
        other = FrameTime(fps = self.fps)
        other._origin = self._origin
        other._frame = self._frame
        other._full_seconds = self._full_seconds
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

        # TODO: test
        if self._origin == FrameTimeType.Time:
            self.__setFrame__(self._full_seconds * self._fps)
        else:
            self.__setSeconds__(self._frame / self._fps)


    @property
    def frame(self):
        """Get Frame (and FPS) value)"""
        return int(round(self._frame))

    @property
    def fullSeconds(self):
        return self._full_seconds

    @property
    def time(self):
        hours = int(self.fullSeconds / 3600)
        counted = hours * 3600
        minutes = int((self.fullSeconds - counted) / 60)
        counted += minutes * 60
        seconds = int((self.fullSeconds - counted))
        counted += seconds
        ms = int(round(1000 * (self.fullSeconds - counted)))

        return { \
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'miliseconds': ms
        }

    def toStr(self, strType="time"):
        """Convert FrameTime to string representation"""
        if strType == "time":
            t = self.time
            fmt = dict(sign='' if self._full_seconds >= 0 else '-',
                       h=abs(t['hours']),
                       m=abs(t['minutes']),
                       s=abs(t['seconds']),
                       ms=abs(t['miliseconds']))
            return "%(sign)s%(h)d:%(m)02d:%(s)02d.%(ms)03d" % fmt
        elif strType == "frame":
            return "%s" % int(round(self._frame))
        else:
            raise AttributeError("Incorrect string type: '%s'" % strType)

    def __setTime__(self, value):
        time = re.match(r"(?P<sign>[+-]?)(?P<h>\d+):(?P<m>[0-5][0-9]):(?P<s>[0-5][0-9])(?:$|\.(?P<ms>\d{1,3}))", value)
        if time is None:
            raise ValueError("Incorrect time format.")

        sign = 1
        if time.group('sign') is not None:
            sign = int('%s1' % time.group('sign'))

        if time.group('ms') is not None:
            # ljust explenation:
            # 10.1 != 10.001
            # 10.1 == 10.100
            ms = int(time.group('ms').ljust(3, '0'))
        else:
            ms = 0
        seconds = int(time.group('s'))
        minutes = int(time.group('m'))
        hours = int(time.group('h'))

        self._full_seconds = sign * (3600*hours + 60*minutes + seconds + float(ms)/1000)
        self._frame = self._fps * self._full_seconds

    def __setSeconds__(self, seconds):
        self._full_seconds = seconds
        self._frame = seconds * self._fps

    def __setFrame__(self, frame):
        self.__setSeconds__(frame / self._fps)

    def __eq__(self, other):
        SubAssert(self._fps == other._fps, _("FPS values are not equal"))
        return self._full_seconds == other._full_seconds

    def __lt__(self, other):
        SubAssert(self._fps == other._fps, _("FPS values are not equal"))
        return self._full_seconds < other._full_seconds

    def __add__(self, other):
        """Defines FrameTime + FrameTime"""
        SubAssert(self._fps == other._fps, _("FPS values are not equal"))
        result = self._full_seconds + other._full_seconds
        return FrameTime(fps = self._fps, seconds = result)

    def __sub__(self, other):
        """Defines FrameTime - FrameTime"""
        SubAssert(self._fps == other._fps, _("FPS values are not equal"))
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
        return "t: %s; f: %s" % (self.toStr(), self.toStr('frame'))

    def __repr__(self):
        return "FrameTime(id=%s, s=%s, f=%s, fps=%s)" % \
               (id(self), self.fullSeconds, self.frame, self.fps)



