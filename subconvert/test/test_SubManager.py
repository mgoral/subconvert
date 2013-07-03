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

    def addSubtitles(self, no):
        for i in range(abs(no)):
            self.m.append(
                Subtitle(FrameTime(25.0, frames=i),
                FrameTime(25.0, frames=i),
                "Subtitle{gsp_nl}%s" % str(i + 1))
            )

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

    def test_subManagerCorrectlyUsesNegativeSubNumbers(self):
        self.addSubtitles(2)
        self.assertEqual("Subtitle{gsp_nl}2", self.m[-1].text)
        self.assertEqual("Subtitle{gsp_nl}2", self.m[1].text)

    # TODO: Make also tests that check returned subtitle times.
    def test_subManagerReturnsCorrectLines(self):
        self.addSubtitles(2)
        self.assertEqual("Subtitle{gsp_nl}1", self.m[0].text)
        self.assertEqual("Subtitle{gsp_nl}2", self.m[1].text)

