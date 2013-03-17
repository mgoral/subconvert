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

class FrameTime(object):
    """Class defining a FrameTime object which consists of frame and time
    metrics (and fps as well)."""

    def __init__(self, fps, value_type, **kwargs):
        """Construct and convert value(s) given in kwargs.
        Kwargs should describe either 'frame' or 'h', 'm',
        's' and 'ms'."""
        if fps > 0:
            self.fps = float(fps)
        else:
            raise ValueError(_("Incorrect FPS value: %s.") % fps)
        if value_type == 'frame':
            self.__set_time__( int(kwargs['frame']) / self.fps)
        elif value_type == 'time':
            if int(kwargs['h']) < 0 or int(kwargs['m']) > 59 or int(kwargs['m']) < 0 \
            or int(kwargs['s']) > 59 or int(kwargs['s']) < 0 or int(kwargs['ms']) > 999 \
            or int(kwargs['ms']) < 0:
                raise ValueError("Arguments not in allowed ranges.")
            self.miliseconds = int(kwargs['ms'])
            self.seconds = int(kwargs['s'])
            self.minutes = int(kwargs['m'])
            self.hours = int(kwargs['h'])
            self.full_seconds = (3600*self.hours + 60*self.minutes + self.seconds + float(self.miliseconds)/1000)
            self.frame = int(round(self.fps * self.full_seconds))
        elif value_type == 'full_seconds':
            self.__set_time__( kwargs['seconds'] )
        else:
            raise AttributeError(_("Not supported FrameTime type: '%s'") % value_type)

    def get_frame(self):
        """Get Frame (and FPS) value)"""
        return (self.fps, self.frame)

    def get_time(self):
        """Get Time (and FPS) value)"""
        return (self.fps, { \
            'hours': self.hours, \
            'minutes': self.minutes, \
            'seconds': self.seconds, \
            'miliseconds': self.miliseconds
        })

    def getTimeStr(self):
        return "%d:%02d:%02d.%03d" % (self.hours, self.minutes, self.seconds, self.miliseconds)

    def getFrameStr(self):
        return "%s" % (self.frame)

    def __set_time__(self, seconds):
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

    def __set_frame__(self, frame):
        """Set time from a given frame"""
        if frame >= 0:
            self.__set_time__(frame / self.fps)
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
        return FrameTime(fps = self.fps, value_type = 'full_seconds', seconds = result)

    def __sub__(self, other):
        """Define FrameTime - FrameTime"""
        assert(self.fps == other.fps)
        assert(self.full_seconds >= other.full_seconds)
        result = self.full_seconds - other.full_seconds
        return FrameTime(fps = self.fps, value_type = 'full_seconds', seconds = result)

    def __mul__(self, val):
        """Define FrameTime * number"""
        result = self.full_seconds * val
        return FrameTime(fps = self.fps, value_type = 'full_seconds', seconds = result)

    def __div__(self, val):
        """Define FrameTime / number"""
        result = self.full_seconds / val
        return FrameTime(fps = self.fps, value_type = 'full_seconds', seconds = result)

    def __str__(self):
        """Define str(FrameTime)"""
        return "t: %s:%s:%s.%s; f: %s" % \
            ( self.hours, self.minutes, self.seconds, self.miliseconds, self.frame )



