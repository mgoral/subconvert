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
from subconvert.parsing.Core import Subtitle
from subconvert.test.Mocks import *

class TestSubtitle(unittest.TestCase):
    """Subtitle test suite."""

    def test_defaultConstructorInitsStartToNone(self):
        sub = Subtitle()
        self.assertIsNone(sub.start)

    def test_defaultConstructorInitsEndToNone(self):
        sub = Subtitle()
        self.assertIsNone(sub.end)

    def test_defaultConstructorInitsTextToNone(self):
        sub = Subtitle()
        self.assertIsNone(sub.text)

    def test_constructorInitializesStartProperly(self):
        ft = FrameTimeMock(25.0)
        sub = Subtitle(start = ft)
        self.assertEqual(ft, sub.start)

    def test_constructorInitializesEndProperly(self):
        ft = FrameTimeMock(24.0)
        sub = Subtitle(end = ft)
        self.assertEqual(ft, sub.end)

    def test_constructorInitializesTextProperly(self):
        sub = Subtitle(text = "text")
        self.assertEqual("text", sub.text)

    def test_emptyReturnsTrueWhenSubIsEmpty(self):
        sub = Subtitle()
        self.assertTrue(sub.empty)

    def test_emptyReturnsFalseWhenStartIsSet(self):
        ft = FrameTimeMock(22.0)
        sub = Subtitle(start = ft)
        self.assertFalse(sub.empty())

    def test_emptyReturnsFalseWhenEndIsSet(self):
        ft = FrameTimeMock(21.0)
        sub = Subtitle(end = ft)
        self.assertFalse(sub.empty())

    def test_emptyReturnsFalseWhenTextIsSet(self):
        sub = Subtitle(text = "text")
        self.assertFalse(sub.empty())

    def test_changeStartCorrectly(self):
        sub = Subtitle(start = FrameTimeMock(10))
        ft = FrameTimeMock(15)
        sub.change(start = ft)
        self.assertEqual(ft, sub.start)

    def test_changeEndCorrectly(self):
        sub = Subtitle(end = FrameTimeMock(11))
        ft = FrameTimeMock(14)
        sub.change(end = ft)
        self.assertEqual(ft, sub.end)

    def test_changeTextCorrectly(self):
        sub = Subtitle(text = "string")
        sub.change(text = "Subtitle")
        self.assertEqual("Subtitle", sub.text)

    def test_changeDisallowsChangingStartToNone(self):
        ft = FrameTimeMock(17)
        sub = Subtitle(start = ft)
        sub.change(start = None)
        self.assertEqual(ft, sub.start)

    def test_changeDisallowsChangingEndToNone(self):
        ft = FrameTimeMock(19)
        sub = Subtitle(end = ft)
        sub.change(end = None)
        self.assertEqual(ft, sub.end)

    def test_changeDisallowsChangingTextToNone(self):
        sub = Subtitle(text = "My Subtitle")
        sub.change(text = None)
        self.assertEqual("My Subtitle", sub.text)

    def test_fpsIsReturnedForCorrectlyInitializedSubtitle(self):
        sub = Subtitle(start = FrameTimeMock(11))
        self.assertEqual(11, sub.fps)

    def test_fpsReturnsNoneWhenSubtitleIsNotIntializedCorrectly(self):
        sub = Subtitle()
        self.assertIsNone(sub.fps)

    def test_fpsCorrectlyChangesFpsForStart(self):
        ftStart = FrameTimeMock(10)
        ftEnd = FrameTimeMock(10)
        sub = Subtitle(start = ftStart, end = ftEnd)
        sub.fps = 25
        self.assertEqual(25, sub.start.fps)

    def test_fpsCorrectlyChangesFpsForEnd(self):
        ftStart = FrameTimeMock(12)
        ftEnd = FrameTimeMock(12)
        sub = Subtitle(start = ftStart, end = ftEnd)
        sub.fps = 23
        self.assertEqual(23, sub.end.fps)

    def test_fpsDoesntChangeStartWhenItIsNone(self):
        sub = Subtitle(end = FrameTimeMock(13))
        sub.fps = 10
        self.assertIsNone(sub.start)

    def test_fpsDoesntChangeEndWhenItIsNone(self):
        sub = Subtitle(start = FrameTimeMock(14))
        sub.fps = 9
        self.assertIsNone(sub.end)

    def test_SubtitleDisallowsCreatingSubtitleWithDifferentFpsValues(self):
        with self.assertRaises(ValueError):
            sub = Subtitle(start = FrameTimeMock(10), end = FrameTimeMock(20))

    def test_SubtitleDisallowChangingStartToADifferentFpsThanEnd(self):
        sub = Subtitle(start = FrameTimeMock(25), end = FrameTimeMock(25))
        with self.assertRaises(ValueError):
            sub.change(start = FrameTimeMock(34))

    def test_SubtitleDisallowChangingEndToADifferentFpsThanStart(self):
        sub = Subtitle(start = FrameTimeMock(15), end = FrameTimeMock(15))
        with self.assertRaises(ValueError):
            sub.change(end = FrameTimeMock(29))

    def test_SubtitleDisallowSettingStartAndEndWithDifferentFpsValues(self):
        sub = Subtitle(start = FrameTimeMock(17), end = FrameTimeMock(17))
        with self.assertRaises(ValueError):
            sub.change(start = FrameTimeMock(37), end = FrameTimeMock(26))
