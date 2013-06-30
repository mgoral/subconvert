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
from subconvert.parsing.FrameTime import FrameTime

# FIXME: SubParser tests should not rely on actual subtitle parsers. A mocked parser should be
# used instead.
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
        ft = FrameTime(25.0, seconds=0)
        sub = Subtitle(start = ft)
        self.assertEqual(ft, sub.start)

    def test_constructorInitializesEndProperly(self):
        ft = FrameTime(24.0, seconds=1)
        sub = Subtitle(end = ft)
        self.assertEqual(ft, sub.end)

    def test_constructorInitializesTextProperly(self):
        sub = Subtitle(text = "text")
        self.assertEqual("text", sub.text)

    def test_emptyReturnsTrueWhenSubIsEmpty(self):
        sub = Subtitle()
        self.assertTrue(sub.empty)

    def test_emptyReturnsFalseWhenStartIsSet(self):
        ft = FrameTime(22.0, seconds=5)
        sub = Subtitle(start = ft)
        self.assertFalse(sub.empty())

    def test_emptyReturnsFalseWhenEndIsSet(self):
        ft = FrameTime(21.0, seconds=2)
        sub = Subtitle(end = ft)
        self.assertFalse(sub.empty())

    def test_emptyReturnsFalseWhenTextIsSet(self):
        sub = Subtitle(text = "text")
        self.assertFalse(sub.empty())

    def test_changeStartCorrectly(self):
        sub = Subtitle(start = FrameTime(10, seconds=0))
        ft = FrameTime(15, seconds = 1)
        sub.change(start = ft)
        self.assertEqual(ft, sub.start)

    def test_changeEndCorrectly(self):
        sub = Subtitle(end = FrameTime(11, seconds=2))
        ft = FrameTime(14, seconds = 4)
        sub.change(end = ft)
        self.assertEqual(ft, sub.end)

    def test_changeTextCorrectly(self):
        sub = Subtitle(text = "string")
        sub.change(text = "Subtitle")
        self.assertEqual("Subtitle", sub.text)

    def test_changeDisallowsChangingStartToNone(self):
        ft = FrameTime(17, seconds = 6)
        sub = Subtitle(start = ft)
        sub.change(start = None)
        self.assertEqual(ft, sub.start)

    def test_changeDisallowsChangingEndToNone(self):
        ft = FrameTime(19, seconds = 64)
        sub = Subtitle(end = ft)
        sub.change(end = None)
        self.assertEqual(ft, sub.end)

    def test_changeDisallowsChangingTextToNone(self):
        sub = Subtitle(text = "My Subtitle")
        sub.change(text = None)
        self.assertEqual("My Subtitle", sub.text)

