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
from subconvert.parsing.FrameTime import FrameTime
from subconvert.parsing.Core import SubManager, Subtitle

class TestSubManager(unittest.TestCase):
    """SubManager test suite."""

    def setUp(self):
        self.m = SubManager()
        self.m.append(Subtitle(FrameTime(25.0, frames=0), FrameTime(25.0, frames=25), "First subtitle"))
        self.m.append(Subtitle(FrameTime(25.0, frames=26), FrameTime(25.0, frames=50), "Second{gsp_nl}subtitle"))

    def test_raiseExceptionWhenFpsIs_0_(self):
        with self.assertRaises(ValueError):
            self.m.changeFps(0)

    def test_raiseExceptionWhenFpsBelow_0_(self):
        with self.assertRaises(ValueError):
            self.m.changeFps(-1)

    def test_changeFpsCorrectly(self):
        self.m.changeFps(5)
        for sub in self.m:
            self.assertEqual(5, sub.fps)

    def test_subAssertsThatSomethingHasBeenParsed(self):
        self.m[0]

    def test_subCorrectlyUsesNegativeSubNumbers(self):
        self.assertEqual("Second{gsp_nl}subtitle", self.m[-1].text)
        self.assertEqual("Second{gsp_nl}subtitle", self.m[1].text)

    # TODO: Make also tests that check returned subtitle times.
    def test_subtitleManagerReturnsCorrectLines(self):
        self.assertEqual("First subtitle", self.m[0].text)
        self.assertEqual("Second{gsp_nl}subtitle", self.m[1].text)
