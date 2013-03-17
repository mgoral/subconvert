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

class FrameTime(object):
    """Class defining a FrameTime object which consists of frame and time
    metrics (and fps as well)."""

    def __init__(self, fps, value_type, value):
        """Construct and convert value(s) given in kwargs.
        Kwargs should describe either 'frame' or 'h', 'm',
        's' and 'ms'."""
        if fps > 0:
            self.fps = float(fps)
        else:
            raise ValueError(_("Incorrect FPS value: %s.") % fps)


        if value_type == 'frame':
            self.__setTime__( int(value) / self.fps)
        elif value_type == 'time':
            time = re.match(r"(?P<h>\d+):(?P<m>[0-5][0-9]):(?P<s>[0-5][0-9])(?:.(?P<ms>\d{3}))?", value)
            if time is None:
                raise ValueError(_("Incorrect time format."))

            if time.group('ms') is not None:
                self.miliseconds = int(time.group('ms'))
            else:
                self.miliseconds = 0
            self.seconds = int(time.group('s'))
            self.minutes = int(time.group('m'))
            self.hours = int(time.group('h'))
            self.full_seconds = (3600*self.hours + 60*self.minutes + self.seconds + float(self.miliseconds)/1000)
            self.frame = int(round(self.fps * self.full_seconds))
        elif value_type == 'full_seconds':
            self.__setTime__( value )
        else:
            raise AttributeError(_("Not supported FrameTime type: '%s'") % value_type)

    def getFrame(self):
        """Get Frame (and FPS) value)"""
        return self.frame

    def getTime(self):
        """Get Time (and FPS) value)"""
        return { \
            'hours': self.hours, \
            'minutes': self.minutes, \
            'seconds': self.seconds, \
            'miliseconds': self.miliseconds
        }

    def toStr(self, strType="time"):
        """Convert FrameTime to string representation"""
        if strType == "time":
            return "%d:%02d:%02d.%03d" % (self.hours, self.minutes, self.seconds, self.miliseconds)
        elif strType == "frame":
            return "%s" % (self.frame)
        else:
            raise AttributeError(_("Incorrect string type: '%s'") % strType)

    def changeFps(self, newFps):
        if newFps > 0:
            self.fps = float(newFps)
        else:
            raise ValueError(_("Incorrect FPS value: %s.") % newFps)
        self.frame = int(round(self.full_seconds * self.fps))

    def __setTime__(self, seconds):
        """Set frame from a given time"""
        if seconds >= 0:
            self.full_seconds = float(seconds)
            self.frame = int(round(self.full_seconds * self.fps))
        else:
            raise ValueError(_("Incorrect seconds value."))
        seconds = int(seconds)
        str_full_seconds = "%.3f" % self.full_seconds   # hack for inaccurate float arithmetics
        dot_place = str_full_seconds.find(".") + 1
        self.miliseconds = int(str_full_seconds[dot_place:])
        self.hours = int(seconds / 3600)
        seconds -= 3600 * self.hours
        self.minutes = int(seconds / 60)
        self.seconds = seconds - 60 * self.minutes

    def __setFrame__(self, frame):
        """Set time from a given frame"""
        if frame >= 0:
            self.__setTime__(frame / self.fps)
        else:
            raise ValueError(_("Incorrect frame value."))

    def __eq__(self, other):
        assert(self.fps == other.fps)
        return self.full_seconds == other.full_seconds

    def __ne__(self, other):
        assert(self.fps == other.fps)
        return self.full_seconds != other.full_seconds

    def __lt__(self, other):
        assert(self.fps == other.fps)
        return self.full_seconds < other.full_seconds

    def __gt__(self, other):
        assert(self.fps == other.fps)
        return self.full_seconds > other.full_seconds

    def __add__(self, other):
        """Define FrameTime + FrameTime"""
        assert(self.fps == other.fps)
        result = self.full_seconds + other.full_seconds
        return FrameTime(fps = self.fps, value_type = 'full_seconds', value = result)

    def __sub__(self, other):
        """Define FrameTime - FrameTime"""
        assert(self.fps == other.fps)
        assert(self.full_seconds >= other.full_seconds)
        result = self.full_seconds - other.full_seconds
        return FrameTime(fps = self.fps, value_type = 'full_seconds', value = result)

    def __mul__(self, val):
        """Define FrameTime * number"""
        result = self.full_seconds * val
        return FrameTime(fps = self.fps, value_type = 'full_seconds', value = result)

    def __div__(self, val):
        """Define FrameTime / number"""
        result = self.full_seconds / val
        return FrameTime(fps = self.fps, value_type = 'full_seconds', value = result)

    def __str__(self):
        """Define str(FrameTime)"""
        return "t: %s:%s:%s.%s; f: %s" % \
            ( self.hours, self.minutes, self.seconds, self.miliseconds, self.frame )



