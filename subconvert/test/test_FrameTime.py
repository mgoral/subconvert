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
import datetime
import random

from subconvert.parsing.FrameTime import FrameTime
import subconvert.utils.version as version

from subconvert.apprunner import _

# TODO: tests for: sub, mul and div
class TestFrameTime(unittest.TestCase):
    """FrameTime Unit Tests
    Note: "fto" in some testcases means "FrameTime Object"
    Note2: In most cases full_seconds are pre-calculated."""

    def compare(self, ft_object, fps, frame, full_seconds, hours, minutes, seconds, miliseconds):
        self.assertEqual(ft_object._fps, fps)
        self.assertEqual(ft_object.getFrame(), round(frame))
        self.assertEqual(ft_object.getFullSeconds(), full_seconds)
        self.assertEqual(ft_object.getTime()['hours'], hours)
        self.assertEqual(ft_object.getTime()['minutes'], minutes)
        self.assertEqual(ft_object.getTime()['seconds'], seconds)
        self.assertEqual(ft_object.getTime()['miliseconds'], miliseconds)

    def test_initWith_0_Fps(self):
        with self.assertRaises(ValueError):
            FrameTime(0, frames=5)

    def test_initWithNegativeFps(self):
        with self.assertRaises(ValueError):
            FrameTime(-5, frames=5)

    def test_initWithoutFrameTimeOrSecondsSpecified(self):
        with self.assertRaises(AttributeError):
            FrameTime(5)

    def test_initWithOneSurplusParameter(self):
        with self.assertRaises(AttributeError):
            FrameTime(5, frames=5, seconds=10)

    def test_initWithTwoSurplusParameters(self):
        with self.assertRaises(AttributeError):
            FrameTime(5, frames=5, time="1:01:01.000", seconds=10)

    def test_initByTimeString(self):
        fto = FrameTime(25, time="1:01:01.101")
        full_seconds = 3661.101
        frames = full_seconds * 25
        self.compare(fto, 25, frames, full_seconds, 1, 1, 1, 101)

    def test_initFullSeconds(self):
        fto = FrameTime(25, seconds=3661.100)
        full_seconds = 3661.100
        frames = full_seconds * 25
        self.compare(fto, 25, frames, full_seconds, 1, 1, 1, 100)

    def test_initFrames(self):
        fto = FrameTime(25, frames=100)
        full_seconds = 4
        frames = full_seconds * 25
        self.compare(fto, 25, frames, full_seconds, 0, 0, 4, 0)

    def test_setSecondsWith1ms(self):
        fto = FrameTime(25, seconds=0)
        full_seconds = 3661.001
        fto.__setSeconds__(full_seconds)
        frames = full_seconds * 25
        self.compare(fto, 25, frames, full_seconds, 1, 1, 1, 1)

    def test_setSecondsWith10ms(self):
        fto = FrameTime(25, seconds=0)
        full_seconds = 3661.010
        fto.__setSeconds__(full_seconds)
        frames = full_seconds * 25
        self.compare(fto, 25, frames, full_seconds, 1, 1, 1, 10)

    def test_setSecondsWith100ms(self):
        fto = FrameTime(25, seconds=0)
        full_seconds = 3661.1
        fto.__setSeconds__(full_seconds)
        frames = full_seconds * 25
        self.compare(fto, 25, frames, full_seconds, 1, 1, 1, 100)

    def test_setSecondsWithNegativeSecondsRaisesAnError(self):
        fto = FrameTime(25, seconds=0)
        with self.assertRaises(ValueError):
            fto.__setSeconds__(-1)

    def test_setFrame(self):
        fto = FrameTime(25, frames=0)
        frames = 40120
        fto.__setFrame__(frames)
        full_seconds = frames / 25
        self.compare(fto, 25, frames, full_seconds, 0, 26, 44, 800)

    def test_setFrameWithNegativeSecondsRaisesAnError(self):
        fto = FrameTime(25, frames=0)
        with self.assertRaises(ValueError):
            fto.__setFrame__(-1)

    def test_setTime(self):
        fto = FrameTime(25, time="0:00:00.000")
        time = "1:01:01.234"
        fto.__setTime__(time)
        full_seconds = 3661.234
        frames = full_seconds * 25
        self.compare(fto, 25, frames, full_seconds, 1, 1, 1, 234)

    def test_setIncorrectlyFormattedTimeRaisesAnError(self):
        fto = FrameTime(25, time="0:00:00.000")
        with self.assertRaises(ValueError):
            fto.__setTime__("1:12;44-999")

    def test_getFrame(self):
        # full_seconds = 3661.100
        fto = FrameTime(25, time="1:01:01.100")
        self.assertEqual(91528, fto.getFrame())

    def test_getFullSeconds(self):
        fto = FrameTime(25, frames=50)
        self.assertEqual(2, fto.getFullSeconds())

    def test_getTime(self):
        full_seconds = 3661.100
        fto = FrameTime(25, seconds=full_seconds)
        frames = round(full_seconds * 25)
        returned_dict = fto.getTime()
        true_time_dict = {
            'hours': 1, \
            'minutes': 1, \
            'seconds': 1, \
            'miliseconds': 100
        }

        # First check if all test-defined fields are in returned dictionary
        for key in true_time_dict:
            if not key in returned_dict.keys():
                raise AssertionError("Key %s not in returned dictionary" % key)

        for key in returned_dict:
            if not key in true_time_dict.keys():
                raise AssertionError("Surplus key in returned dictionary")
            self.assertEqual(returned_dict[key], true_time_dict[key])

    def test_compareEqual(self):
        fto1 = FrameTime(25, frames=50)
        fto2 = FrameTime(25, frames=50)
        self.assertTrue(fto1 == fto2)

    def test_compareHigherThan(self):
        fto1 = FrameTime(25, frames=51)
        fto2 = FrameTime(25, frames=50)
        self.assertTrue(fto1 > fto2)
        self.assertFalse(fto2 > fto1)

    def test_compareLowerThan(self):
        fto1 = FrameTime(25, frames=49)
        fto2 = FrameTime(25, frames=50)
        self.assertTrue(fto1 < fto2)
        self.assertFalse(fto2 < fto1)

    def test_add(self):
        fto1 = FrameTime(25, time="1:01:01.100")
        fto2 = FrameTime(25, time="2:02:02.200")
        fto3 = fto1 + fto2
        full_seconds = 10983.3
        frames = full_seconds * 25
        self.compare(fto3, 25, frames, full_seconds, 3, 3, 3, 300)

    def test_str(self):
        fto = FrameTime(25, time="2:02:02.200")
        full_seconds = 7322.2
        returned_str = str(fto)
        expected_str = "t: 2:2:2.200; f: %s" % int(round(full_seconds * 25))
        self.assertEqual(returned_str, expected_str)

    def test_changeFpsOkCase(self):
        fto = FrameTime(25, time="0:00:01")
        self.assertEqual(25, fto.getFrame())
        fto.changeFps(31)
        self.assertEqual(31, fto.getFrame())

    def test_changeFpsToZeroIncorrectValue(self):
        fto = FrameTime(25, time="0:00:01")
        with self.assertRaises(ValueError):
            fto.changeFps(0)
        with self.assertRaises(ValueError):
            fto.changeFps(-1)

if __name__ == "__main__":
    unittest.main()

