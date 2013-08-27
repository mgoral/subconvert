#-*- coding: utf-8 -*-

"""
This file is part of SubConvert.

SubConvert is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SubConvert is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SubConvert.  If not, see <http://www.gnu.org/licenses/>.
"""

import gettext
import re

# TODO: change asserts to exceptions!
class FrameTime(object):
    """Class defining a FrameTime object which consists of frame and time metrics (and fps as well)."""

    def __init__(self, fps, seconds=None, frames=None, time=None):
        """Constructs FrameTime object with a given FPS value. Constructor accepts only one value
        from the following ones: time (properly formatted string), number of frames (int) or number
        of total seconds (float, with miliseconds specified after decimal point).

        Examples:
        FrameTime(time="1:01:01.100", fps=25)
        FrameTime(frame=100, fps=25)
        FrameTime(full_seconds="3600.01", fps=25)
        """
        exclusiveArgs = [frames, time, seconds]
        if exclusiveArgs.count(None) != 2:
            raise AttributeError(_("FrameTime can obly be initialized by one type."))

        if fps <= 0:
            raise ValueError(_("Incorrect FPS value: %s.") % fps)

        self._fps = float(fps)

        if frames is not None:
            self.__setFrame__(int(frames))
        elif time is not None:
            self.__setTime__(str(time))
        else:
            self.__setSeconds__(float(seconds))

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, newFps):
        if newFps > 0:
            self._fps = float(newFps)
        else:
            raise ValueError(_("Incorrect FPS value: %s.") % newFps)
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
            raise AttributeError(_("Incorrect string type: '%s'") % strType)

    def __setTime__(self, value):
        time = re.match(r"(?P<h>\d+):(?P<m>[0-5][0-9]):(?P<s>[0-5][0-9])(?:.(?P<ms>\d{3}))?", value)
        if time is None:
            raise ValueError(_("Incorrect time format."))

        if time.group('ms') is not None:
            self._miliseconds = int(time.group('ms'))
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
            raise ValueError(_("Incorrect seconds value."))

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
            raise ValueError(_("Incorrect frame value."))

    def __eq__(self, other):
        assert(self._fps == other._fps)
        return self._full_seconds == other._full_seconds

    def __ne__(self, other):
        assert(self._fps == other._fps)
        return self._full_seconds != other._full_seconds

    def __lt__(self, other):
        assert(self._fps == other._fps)
        return self._full_seconds < other._full_seconds

    def __gt__(self, other):
        assert(self._fps == other._fps)
        return self._full_seconds > other._full_seconds

    def __add__(self, other):
        """Defines FrameTime + FrameTime"""
        assert(self._fps == other._fps)
        result = self._full_seconds + other._full_seconds
        return FrameTime(fps = self._fps, seconds = result)

    def __sub__(self, other):
        """Defines FrameTime - FrameTime"""
        assert(self._fps == other._fps)
        assert(self._full_seconds >= other._full_seconds)
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



