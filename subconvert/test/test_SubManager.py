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
from subconvert.parsing.Core import SubManager, Subtitle
from subconvert.test.Mocks import *
from subconvert.parsing.FrameTime import FrameTime

class TestSubManager(unittest.TestCase):
    """SubManager test suite."""

    def setUp(self):
        self.m = SubManager()
        self.correctSub = SubtitleMock(FrameTime(10, 0), FrameTime(10, 0), "Default Subtitle")
        self.subWithNoEnd = SubtitleMock(FrameTime(10, 0), None, "NoEnd Subtitle")

    def addSubtitles(self, no):
        for i in range(abs(no)):
            self.m.append(
                SubtitleMock(
                    FrameTime(10, seconds=i),
                    FrameTime(10, seconds=i),
                    "Subtitle{gsp_nl}%s" % str(i + 1)
                )
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

    def test_raiseExceptionWhenTryingToInsertSubToNegativeIndex(self):
        with self.assertRaises(ValueError):
            self.m.insert(-1, self.correctSub)

    def test_insertProperlyAddsToEmptyList(self):
        self.m.insert(0, self.correctSub)
        self.assertEqual(self.correctSub, self.m[0])

    def test_insertProperlyAddsToTheBeginning(self):
        self.addSubtitles(2)
        self.m.insert(0, self.correctSub)
        self.assertEqual(self.correctSub, self.m[0])

    def test_insertProperlyAddsToTheEnd(self):
        self.addSubtitles(2)
        self.m.insert(2, self.correctSub)
        self.assertEqual(self.correctSub, self.m[2])

    def test_insertProperlyAddsToTheEndWhenIndexIsTooHigh(self):
        self.addSubtitles(5)
        self.m.insert(9, self.correctSub)
        self.assertEqual(self.correctSub, self.m[5])

    def test_insertProperlyAddsInTheMiddle(self):
        self.addSubtitles(4)
        self.m.insert(2, self.correctSub)
        self.assertEqual(self.correctSub, self.m[2])

    def test_insertHandlesChangingSubtitleEndWhenItIsNotSet(self):
        self.addSubtitles(3)
        self.assertIsNone(self.subWithNoEnd.end)
        self.m.insert(1, self.subWithNoEnd)
        self.assertIsNotNone(self.m[1].end)

    def test_appendCorrectlyAddsTheFirstSub(self):
        self.m.append(self.correctSub)
        self.assertEqual(self.correctSub, self.m[0])

    def test_appendCorrectlyAddsTheSecondSub(self):
        self.m.append(self.correctSub)
        self.m.append(self.subWithNoEnd)
        self.assertEqual(self.subWithNoEnd, self.m[1])

    def test_appendCorrectlyChangesEmptyEndTimeOfTheLastSubtitle(self):
        self.m.append(self.correctSub)
        self.m.append(self.subWithNoEnd)
        self.assertIsNotNone(self.subWithNoEnd.end)

    def test_appendCorrectlyChangesEndTimeOfPreviousSubtitleWhenANewSubtitlehasBeenAdded(self):
        self.m.append(self.correctSub)
        self.m.append(self.subWithNoEnd)
        self.assertEqual(2.5, self.subWithNoEnd.end.fullSeconds)

        nextSub = SubtitleMock(FrameTime(10, seconds=1), FrameTime(10, seconds=1), "")
        self.m.append(nextSub)
        self.assertEqual(0.85, self.subWithNoEnd.end.fullSeconds)

    # TODO: this should check number of mock calls
    def test_appendChangesEndTimeMaximumTwoTimes(self):
        nextSub = SubtitleMock(FrameTime(10, seconds=1), FrameTime(10, seconds=1), "")
        secondNextSub = SubtitleMock(FrameTime(10, seconds=2), FrameTime(10, seconds=2), "")

        self.m.append(self.correctSub)
        self.m.append(self.subWithNoEnd)
        self.m.append(nextSub)
        self.m.append(secondNextSub)

        self.assertEqual(0.85, self.subWithNoEnd.end.fullSeconds)

    def test_appendIsAbleToChangeEndTimeOfTwoSubsAtOnce(self):
        self.m.append(self.correctSub)
        self.m.append(self.subWithNoEnd)

        nextSub = SubtitleMock(FrameTime(10, seconds=1), None, "")
        self.m.append(nextSub)

        self.assertIsNotNone(self.subWithNoEnd.end)
        self.assertIsNotNone(nextSub.end)
