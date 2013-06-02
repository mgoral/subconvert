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
from subconvert.parsing.Convert import SubConverter
from subconvert.parsing.FrameTime import FrameTime

# FIXME: SubConverter tests should not rely on actual subtitle parsers. A mocked parser should be
# used instead.
class TestSubConverter(unittest.TestCase):
    """SubConverter test suite."""

    subWithHeader = ["[INFORMATION]\n", "[TITLE]SubTitle\n", "[AUTHOR]Author\n",
        "[SOURCE]Source\n","[PRG]Prg\n", "[FILEPATH]Dummy/Path\n", "[DELAY]4\n", "[CD TRACK]1\n",
        "[COMMENT]No comment\n", "[END INFORMATION]\n",
        "[SUBTITLE]\n", "[COLF]&HFFFFFF,[STYLE]no,[SIZE]24,[FONT]Tahoma\n",
        "01:01:01.00,01:01:02.50\n", "First subtitle\n", "\n",
        "01:01:03.00,01:01:04.00\n", "Second\n", "subtitle\n"]

    subWithoutHeader = ["0\n", "01:01:01,000 --> 01:01:02,500\n", "First subtitle\n",
        "\n", "1\n", "01:01:03,000 --> 01:01:04,000\n", "Second\n", "subtitle\n"]

    def setUp(self):
        self.c = SubConverter()

    def test_raiseExceptionWhenFpsIs_0_(self):
        with self.assertRaises(AssertionError):
            self.c.changeFps(0)

    def test_raiseExceptionWhenFpsBelow_0_(self):
        with self.assertRaises(AssertionError):
            self.c.changeFps(-1)

    def test_changeFpsCorrectly(self):
        self.c.changeFps(5)
        self.assertEqual(5, self.c.fps())

    def test_changeFpsChangesCorrectlySubtitleTimes(self):
        # Set FPS first so we don't rely on default value
        self.c.changeFps(25)

        result = self.c.parse(self.subWithHeader)
        subTime0 = (self.c.sub(0)["time_from"].getFrame(), self.c.sub(0)["time_to"].getFrame())
        subTime1 = (self.c.sub(1)["time_from"].getFrame(), self.c.sub(1)["time_to"].getFrame())

        self.c.changeFps(50)
        newTime0 = (self.c.sub(0)["time_from"].getFrame(), self.c.sub(0)["time_to"].getFrame())
        newTime1 = (self.c.sub(1)["time_from"].getFrame(), self.c.sub(1)["time_to"].getFrame())

        self.assertAlmostEqual(2 * subTime0[0], newTime0[0], delta=1)
        self.assertAlmostEqual(2 * subTime0[1], newTime0[1], delta=1)
        self.assertAlmostEqual(2 * subTime1[0], newTime1[0], delta=1)
        self.assertAlmostEqual(2 * subTime1[1], newTime1[1], delta=1)

    def test_parseSubWithHeaderGivesProperSub(self):
        result = self.c.parse(self.subWithHeader)
        self.assertEqual("First subtitle", result[0]["sub"]["text"])
        self.assertEqual("Second{gsp_nl}subtitle", result[1]["sub"]["text"])

    def test_parseSubWithHeaderGivesProperTimes(self):
        result = self.c.parse(self.subWithHeader)
        self.assertIsInstance(result[0]["sub"]["time_from"], FrameTime)
        self.assertIsInstance(result[0]["sub"]["time_to"], FrameTime)

    def test_parseSubWithHeaderFillsInHeader(self):
        result = self.c.parse(self.subWithHeader)
        self.assertIsInstance(result[0]["sub"]["header"], dict)
        self.assertNotEqual(0, len(result[0]["sub"]["header"]))

    def test_parseSubWithoutHeaderGivesProperSub(self):
        result = self.c.parse(self.subWithoutHeader)
        self.assertEqual("First subtitle", result[0]["sub"]["text"])
        self.assertEqual("Second{gsp_nl}subtitle", result[1]["sub"]["text"])

    def test_parseSubWithoutHeaderGivesProperTimes(self):
        result = self.c.parse(self.subWithoutHeader)
        self.assertIsInstance(result[0]["sub"]["time_from"], FrameTime)
        self.assertIsInstance(result[0]["sub"]["time_to"], FrameTime)

    def test_parseSubWithoutHeaderDoesntFillInHeader(self):
        result = self.c.parse(self.subWithoutHeader)
        self.assertIsNone(result[0]["sub"].get("header"))

    def test_parseReturnsEmptyListWhenUnsuccessfull(self):
        # We first make sure that there was something parsed earlier
        self.c.parse(self.subWithHeader)
        result = self.c.parse(["dummy text"])
        self.assertEqual([], result)

    def test_subAssertsThatSomethingHasBeenParsed(self):
        with self.assertRaises(AssertionError):
            self.c.sub(0)

    def test_subCorrectlyUsesNegativeSubNumbers(self):
        result = self.c.parse(self.subWithoutHeader)
        # Last sub is always None
        self.assertIsNone(self.c.sub(-1))
        self.assertEqual(result[1]["sub"], self.c.sub(-2))

    def test_subReturnsCorrectLines(self):
        result = self.c.parse(self.subWithoutHeader)
        self.assertEqual(result[0]["sub"], self.c.sub(0))
        self.assertEqual(result[1]["sub"], self.c.sub(1))

    def test_isParsedReturnsFalseWhenNothingIsParsed(self):
        self.assertFalse(self.c.isParsed())

    def test_isParsedReturnsFalseWhenSomethingIsParsed(self):
        self.c.parse(self.subWithoutHeader)
        self.assertTrue(self.c.isParsed())

    def test_isParsedReturnsFalseWhenRepeatedParsingWasIncorrect(self):
        self.c.parse(self.subWithoutHeader)
        self.c.parse([""])
        self.assertFalse(self.c.isParsed())

    def test_toFormatAssertsThatSubtitleIsParsed(self):
        with self.assertRaises(AssertionError):
            self.c.toFormat("subrip")

    def test_toFormatRaisesAnExceptionWhenIncorrectFormatIsGiven(self):
        self.c.parse(self.subWithoutHeader)
        self.c.toFormat("subrip")
        with self.assertRaises(AssertionError):
            self.c.toFormat("DummyFormatWhichDoesntExist")

    def test_toFormatReturnsTheSameSubForSubtitleWithHeader(self):
        self.c.parse(self.subWithHeader)
        result = self.c.toFormat("subviewer")
        # Comparing bare strings has several benefits: it produces better visual output when
        # something goes wrong. Also, SubConvert produces lists that arelogically equal to the
        # input but differ somehow (e.g. newlines aren't stored in individual list elements but
        # together with subtitle)
        self.assertEqual(''.join(self.subWithHeader).strip(), ''.join(result).strip())

    def test_toFormatReturnsTheSameSubForSubtitleWithoutHeader(self):
        self.c.parse(self.subWithoutHeader)
        result = self.c.toFormat("subrip")
        self.assertEqual(''.join(self.subWithoutHeader).strip(), ''.join(result).strip())

    def test_toFormatConvertsFromHeaderlessToSubtitleWithHeader(self):
        self.c.parse(self.subWithoutHeader)
        result = self.c.toFormat("subviewer")
        # Note: this requires the knowledge of what SubViewer converter default header values are.
        # They may change at times...
        compSubWithHeader = ["[INFORMATION]\n", "[TITLE]\n", "[AUTHOR]\n",
            "[SOURCE]\n","[PRG]SubConvert\n", "[FILEPATH]\n", "[DELAY]0\n", "[CD TRACK]0\n",
            "[COMMENT]Converted to subviewer format with SubConvert\n", "[END INFORMATION]\n",
            "[SUBTITLE]\n", "[COLF]&HFFFFFF,[STYLE]no,[SIZE]24,[FONT]Tahoma\n",
            "01:01:01.00,01:01:02.50\n", "First subtitle\n", "\n",
            "01:01:03.00,01:01:04.00\n", "Second\n", "subtitle\n"]
        self.assertEqual(''.join(compSubWithHeader).strip(), ''.join(result).strip())

    def test_toFormatConvertsSubtitleWithHeaderToHeaderless(self):
        self.c.parse(self.subWithHeader)
        result = self.c.toFormat("subrip")
        self.assertEqual(''.join(self.subWithoutHeader).strip(), ''.join(result).strip())

if __name__ == "__main__":
    unittest.main()
