#-*- coding: utf-8 -*-

"""
Copyright (C) 2011, 2012, 2013 Michal Goral.

This file is part of Subconvert

Subconvert is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Subconvert is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Subconvert. If not, see <http://www.gnu.org/licenses/>.
"""

import unittest
from subconvert.parsing.Core import SubParser, SubParsingError
from subconvert.parsing.FrameTime import FrameTime
from subconvert.parsing.Formats import *

# FIXME: SubParser tests should not rely on actual subtitle parsers. A mocked parser should be
# used instead.

#TODO: test incorrect parsing
class TestSubParser(unittest.TestCase):
    """SubParser test suite."""

    subWithHeader = ["[INFORMATION]\n", "[TITLE]SubTitle\n", "[AUTHOR]Author\n",
        "[SOURCE]Source\n","[PRG]Prg\n", "[FILEPATH]Dummy/Path\n", "[DELAY]4\n", "[CD TRACK]1\n",
        "[COMMENT]No comment\n", "[END INFORMATION]\n",
        "[SUBTITLE]\n", "[COLF]&HFFFFFF,[STYLE]no,[SIZE]24,[FONT]Tahoma\n",
        "01:01:01.00,01:01:02.50\n", "First subtitle\n", "\n",
        "01:01:03.00,01:01:04.00\n", "Second\n", "subtitle\n"]

    subWithoutHeader = ["0\n", "01:01:01,000 --> 01:01:02,500\n", "First subtitle\n",
        "\n", "1\n", "01:01:03,000 --> 01:01:04,000\n", "Second\n", "subtitle\n"]

    def setUp(self):
        self.p = SubParser()
        self.p.registerFormat(SubRip)
        self.p.registerFormat(SubViewer)

    def test_ExceptionRisesWhenRepeatedParsingWasIncorrect(self):
        self.p.parse(self.subWithoutHeader)
        with self.assertRaises(SubParsingError):
            self.p.parse([""])

    def test_parseSubWithHeaderGivesProperSub(self):
        result = self.p.parse(self.subWithHeader)
        self.assertEqual("First subtitle", result[0].text)
        self.assertEqual("Second{gsp_nl}subtitle", result[1].text)

    def test_parseSubWithHeaderGivesProperTimes(self):
        result = self.p.parse(self.subWithHeader)
        self.assertIsInstance(result[0].start, FrameTime)
        self.assertIsInstance(result[0].start, FrameTime)

    def test_parseSubWithHeaderFillsInHeader(self):
        result = self.p.parse(self.subWithHeader)
        self.assertFalse(result.header().empty())

    def test_parseSubWithoutHeaderGivesProperSub(self):
        result = self.p.parse(self.subWithoutHeader)
        self.assertEqual("First subtitle", result[0].text)
        self.assertEqual("Second{gsp_nl}subtitle", result[1].text)

    # TODO: check actual times, not just types
    def test_parseSubWithoutHeaderGivesProperTimes(self):
        result = self.p.parse(self.subWithoutHeader)
        self.assertIsInstance(result[0].start, FrameTime)
        self.assertIsInstance(result[0].end, FrameTime)

    def test_parseSubWithoutHeaderDoesntFillInHeader(self):
        result = self.p.parse(self.subWithoutHeader)
        self.assertTrue(result.header().empty())
