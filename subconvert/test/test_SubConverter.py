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
from subconvert.subparser.Convert import SubConverter
from subconvert.subparser.FrameTime import FrameTime

# FIXME: SubConverter tests should not rely on actual subtitle parsers. A mocked parser should be
# used instead.
class TestSubConverter(unittest.TestCase):
    """SubConverter test suite."""

    subWithHeader = ["[INFORMATION]\n", "[TITLE]\n", "[AUTHOR]\n", "[SOURCE]\n",
        "[PRG]SubConvert\n", "[FILEPATH]\n", "[DELAY]0\n", "[CD TRACK]0\n",
        "[COMMENT]Converted to subviewer format with SubConvert\n", "[END INFORMATION]\n",
        "[SUBTITLE]\n", "[COLF]&HFFFFFF,[STYLE]no,[SIZE]24,[FONT]Tahoma\n",
        "00:00:01.00,00:00:02.50\n", "First subtitle\n", "\n",
        "00:00:03.00,00:00:04.00\n", "Second\n", "subtitle\n"]

    subWithoutHeader = ["0\n", "00:00:01,000 --> 00:00:02,500\n", "First subtitle\n",
        "\n", "1\n", "00:00:03,000 --> 00:00:04,000\n", "Second\n", "subtitle\n"]

    def setUp(self):
        self.converter = SubConverter()
        #self.subWithHeaderParsed = self.converter.parse(self.subWithHeader)
        #self.subWithoutHeaderParsed = self.converter.parse(self.subWithoutHeader)

    def test_raiseExceptionWhenFpsIs_0_(self):
        with self.assertRaises(AssertionError):
            self.converter.changeFps(0)

    def test_raiseExceptionWhenFpsBelow_0_(self):
        with self.assertRaises(AssertionError):
            self.converter.changeFps(-1)

    def test_changeFpsCorrectly(self):
        self.converter.changeFps(5)
        self.assertEqual(5, self.converter.fps())

    def test_parseSubWithHeaderGivesProperSub(self):
        result = self.converter.parse(self.subWithHeader)
        self.assertEqual("First subtitle", result[0]["sub"]["text"])

    def test_parseSubWithHeaderGivesProperTimes(self):
        result = self.converter.parse(self.subWithHeader)
        self.assertIsInstance(result[0]["sub"]["time_from"], FrameTime)
        self.assertIsInstance(result[0]["sub"]["time_to"], FrameTime)

    def test_parseSubWithHeaderFillsInHeader(self):
        result = self.converter.parse(self.subWithHeader)
        self.assertIsInstance(result[0]["sub"]["header"], dict)
        self.assertNotEqual(0, len(result[0]["sub"]["header"]))

if __name__ == "__main__":
    unittest.main()
