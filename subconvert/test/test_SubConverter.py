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
from subconvert.parsing.FrameTime import FrameTime
from subconvert.parsing.Core import SubConverter, SubManager, Subtitle
from subconvert.parsing.Formats import SubRip, SubViewer

# FIXME: SubConverter tests should not rely on actual subtitle parsers. A mocked parser should be
# used instead.
class TestSubConverter(unittest.TestCase):
    """SubConverter test suite."""

    subWithHeader = ["[INFORMATION]\n", "[TITLE]Subtitle\n", "[AUTHOR]Subtitle author\n",
        "[SOURCE]\n","[PRG]SubConvert\n", "[FILEPATH]\n", "[DELAY]0\n", "[CD TRACK]0\n",
        "[COMMENT]Converted to subviewer format with SubConvert\n", "[END INFORMATION]\n",
        "[SUBTITLE]\n", "[COLF]&HFFFFFF,[STYLE]no,[SIZE]24,[FONT]Tahoma\n",
        "00:00:00.00,00:00:01.00\n", "First subtitle\n", "\n",
        "00:00:02.00,00:00:03.00\n", "Second\n", "subtitle\n"]

    subWithoutHeader = ["0\n", "00:00:00,000 --> 00:00:01,000\n", "First subtitle\n",
        "\n", "1\n", "00:00:02,000 --> 00:00:03,000\n", "Second\n", "subtitle\n"]

    def setUp(self):
        self.subs = SubManager()
        self.subs.append(Subtitle(FrameTime(25.0, frames=0), FrameTime(25.0, frames=25), "First subtitle"))
        self.subs.append(Subtitle(FrameTime(25.0, frames=50), FrameTime(25.0, frames=75), "Second{gsp_nl}subtitle"))
        self.subs.header().add("title", "Subtitle")
        self.subs.header().add("author", "Subtitle author")

        self.c = SubConverter()

    def test_convertAssertsThatSubtitleIsParsed(self):
        self.subs.clear()
        with self.assertRaises(AssertionError):
            self.c.convert(SubRip, self.subs)

    def test_convertReturnsTheSameSubForSubtitleWithHeader(self):
        result = self.c.convert(SubViewer, self.subs)
        # Comparing bare strings has several benefits: it produces better visual output when
        # something goes wrong. Also, SubConvert produces lists that arelogically equal to the
        # input but differ somehow (e.g. newlines aren't stored in individual list elements but
        # together with subtitle)
        self.assertEqual(''.join(self.subWithHeader).strip(), ''.join(result).strip())

    def test_convertReturnsTheSameSubForSubtitleWithoutHeader(self):
        result = self.c.convert(SubRip, self.subs)
        self.assertEqual(''.join(self.subWithoutHeader).strip(), ''.join(result).strip())

    def test_convertFromHeaderlessToSubtitleWithHeader(self):
        self.subs.header().clear()
        result = self.c.convert(SubViewer, self.subs)
        # Note: this requires the knowledge of what SubViewer converter default header values are.
        # They may change at times...
        compSubWithHeader = ["[INFORMATION]\n", "[TITLE]\n", "[AUTHOR]\n",
            "[SOURCE]\n","[PRG]SubConvert\n", "[FILEPATH]\n", "[DELAY]0\n", "[CD TRACK]0\n",
            "[COMMENT]Converted to subviewer format with SubConvert\n", "[END INFORMATION]\n",
            "[SUBTITLE]\n", "[COLF]&HFFFFFF,[STYLE]no,[SIZE]24,[FONT]Tahoma\n",
            "00:00:00.00,00:00:01.00\n", "First subtitle\n", "\n",
            "00:00:02.00,00:00:03.00\n", "Second\n", "subtitle\n"]
        self.assertEqual(''.join(compSubWithHeader).strip(), ''.join(result).strip())

    def test_convertSubtitleWithHeaderToHeaderless(self):
        result = self.c.convert(SubRip, self.subs)
        self.assertEqual(''.join(self.subWithoutHeader).strip(), ''.join(result).strip())

if __name__ == "__main__":
    unittest.main()
