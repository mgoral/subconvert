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

import unittest
import logging
import datetime
import random

from subparser.FrameTime import FrameTime
import subutils.version as version

from subconvert import _

class TestFrameTime(unittest.TestCase):
    """FrameTime Unit Tests
    Note: "fto" in some testcases means "FrameTime Object"
    Note2: In most cases full_seconds are pre-calculated."""

    fps = 25.0

    def compare(self, ft_object, fps, frame, full_seconds, hours, minutes, seconds, miliseconds):
        delta = 1
        self.assertEqual(ft_object.fps, fps)
        log.info("* Asserting frame is almost equal with delta=%s for %s =?= %s" % (delta, ft_object.frame, frame))
        self.assertAlmostEqual(ft_object.frame, frame, delta=1)
        self.assertEqual(ft_object.full_seconds, full_seconds)
        self.assertEqual(ft_object.hours, hours)
        self.assertEqual(ft_object.minutes, minutes)
        self.assertEqual(ft_object.seconds, seconds)
        self.assertEqual(ft_object.miliseconds, miliseconds)

    def test_init(self):
        log.info(" \n... running FrameTime constructing test")

        #1
        fto = FrameTime(self.fps, "time", h=1, m=1, s=1, ms=100)
        full_seconds = 3661.100
        frames = full_seconds * self.fps
        self.compare(fto, self.fps, frames, full_seconds, 1, 1, 1, 100)
        #2
        fto = FrameTime(self.fps, "full_seconds", seconds=3661.100)
        full_seconds = 3661.100
        frames = full_seconds * self.fps
        self.compare(fto, self.fps, frames, full_seconds, 1, 1, 1, 100)
        #3
        fto = FrameTime(self.fps, "frame", frame=100)
        full_seconds = 4
        frames = full_seconds * self.fps
        self.compare(fto, self.fps, frames, full_seconds, 0, 0, 4, 0)

    def test_set_time(self):
        log.info(" \n... running FrameTime __set_time__() test")
        fto = FrameTime(self.fps, "frame", frame=0)

        # 1
        full_seconds = 3661.001
        frames = full_seconds * self.fps
        fto.__set_time__(full_seconds)
        self.compare(fto, self.fps, frames, full_seconds, 1, 1, 1, 1)

        # 2
        full_seconds = 3661.010
        frames = full_seconds * self.fps
        fto.__set_time__(full_seconds)
        self.compare(fto, self.fps, frames, full_seconds, 1, 1, 1, 10)

        # 3
        full_seconds = 3661.1
        frames = full_seconds * self.fps
        fto.__set_time__(full_seconds)
        self.compare(fto, self.fps, frames, full_seconds, 1, 1, 1, 100)

        #4 - some random numbers
        full_seconds = random.uniform(1000, 10000)
        frames = full_seconds * self.fps
        fto.__set_time__(full_seconds)

        sseconds = int(full_seconds)
        str_full_seconds = "%.3f" % full_seconds
        dot_place = str_full_seconds.find(".") + 1
        miliseconds = int(str_full_seconds[dot_place:])
        hours = int(sseconds / 3600)
        sseconds -= 3600 * hours
        minutes = int(sseconds / 60)
        seconds = sseconds - 60 * minutes
        log.info("* Testing random full_seconds: %s" % full_seconds)
        log.info("  which is %s frames, %s hours, %s minutes, %s seconds and %s miliseconds" % \
            (frames, hours, minutes, seconds, miliseconds))
        self.compare(fto, self.fps, frames, full_seconds, hours, minutes, seconds, miliseconds)

    def test_set_frame(self):
        log.info(" \n... running FrameTime __set_frame__() test")
        fto = FrameTime(self.fps, "frame", frame=0)
        frames = 40120
        fto.__set_frame__(frames)
        full_seconds = frames / self.fps
        self.compare(fto, self.fps, frames, full_seconds, 0, 26, 44, 800)

    def test_get_frame(self):
        log.info(" \n... running FrameTime __get_frame__() test")
        fto = FrameTime(self.fps, "time", h=1, m=1, s=1, ms=100)
        full_seconds = 3661.100
        frames = round(full_seconds * self.fps)
        self.assertEqual(fto.get_frame(), frames)

    def test_get_time(self):
        log.info(" \n... running FrameTime __get_time__() test")
        fto = FrameTime(self.fps, "time", h=1, m=1, s=1, ms=100)
        full_seconds = 3661.100
        frames = round(full_seconds * self.fps)
        (fps, returned_dict) = fto.get_time()
        true_time_dict = {
            'hours': 1, \
            'minutes': 1, \
            'seconds': 1, \
            'miliseconds': 100
        }
        self.assertEqual(fps, self.fps)

        # First check if all test-defined fields are in returned dictionary
        for key in true_time_dict:
            if not key in returned_dict.keys():
                raise AssertionError("Key %s not in returned dictionary" % key)

        for key in returned_dict:
            if not key in true_time_dict.keys():
                raise AssertionError("Surplus key in returned dictionary")
            self.assertEqual(returned_dict[key], true_time_dict[key])

    def test_cmp(self):
        log.info(" \n... running FrameTime __cmp__() test")
        fto1 = FrameTime(self.fps, "frame", frame=50)
        fto2 = FrameTime(self.fps, "frame", frame=50)
        fto3 = FrameTime(self.fps, "frame", frame=49)
        fto4 = FrameTime(self.fps, "frame", frame=51)

        self.assertTrue(fto1 == fto2)
        self.assertTrue(fto1 > fto3)
        self.assertTrue(fto1 < fto4)

    def test_add(self):
        log.info(" \n... running FrameTime __add__() test")
        fto1 = FrameTime(self.fps, "time", h=1, m=1, s=1, ms=100)
        fto2 = FrameTime(self.fps, "time", h=2, m=2, s=2, ms=200)
        fto3 = fto1 + fto2
        full_seconds = 10983.3
        frames = full_seconds * self.fps
        self.compare(fto3, self.fps, frames, full_seconds, 3, 3, 3, 300)

    def test_str(self):
        log.info(" \n... running FrameTime __str__() test")
        fto = FrameTime(self.fps, "time", h=2, m=2, s=2, ms=200)
        full_seconds = 7322.2
        returned_str = str(fto)
        expected_str = "t: 2:2:2.200; f: %s" % int(round(full_seconds * self.fps))
        self.assertEqual(returned_str, expected_str)

    def test_changeFps(self):
        fto = FrameTime(self.fps, "time", h=0, m=0, s=1, ms=0)
        fto.changeFps(31)
        self.assertEqual(31, fto.get_frame())

if __name__ == "__main__":
    log = logging.getLogger('SubConvert')
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())
    log.info("Testing SubConvert, version %s." % version.__version__)
    log.info(datetime.datetime.now().isoformat())
    unittest.main()

