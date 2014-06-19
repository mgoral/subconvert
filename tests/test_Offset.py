#-*- coding: utf-8 -*-

"""
Copyright (C) 2011-2014 Michal Goral.

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

from subconvert.parsing.Offset import SyncPoint, TimeSync
from subconvert.parsing.FrameTime import FrameTime
from subconvert.parsing.Core import Subtitle, SubManager

class TestOffset(unittest.TestCase):
    """Offset Unit Tests"""

    def setUp(self):
        self._subs = SubManager()
        self._subs.append(self.createSubtitle(1, 2))
        self._subs.append(self.createSubtitle(25, 26))
        self._subs.append(self.createSubtitle(21, 25))
        self._subs.append(self.createSubtitle(22, 23))
        self._subs.append(self.createSubtitle(25, 28))
        self._subs.append(self.createSubtitle(30, 30))

        self._testedTimeSync = TimeSync(self._subs)

    def createFrameTime(self, secs):
        return FrameTime(fps = 25, seconds = secs)

    def createSubtitle(self, secStart, secEnd):
        start = self.createFrameTime(secStart)
        end = self.createFrameTime(secEnd)
        text = "Test subtitle, %d - %d" % (secStart, secEnd)
        return Subtitle(start, end, text)

    def createSyncPoint(self, subNo, secStart, secEnd):
        start = self.createFrameTime(secStart)
        end = self.createFrameTime(secEnd)
        return SyncPoint(subNo, start, end)

    def test_syncWithoutSyncPointsChangesNothing(self):
        syncList = []
        self._testedTimeSync.sync(syncList)

        self.assertEqual(self._subs[0].start, self.createFrameTime(1))
        self.assertEqual(self._subs[0].end, self.createFrameTime(2))

        self.assertEqual(self._subs[3].start, self.createFrameTime(22))
        self.assertEqual(self._subs[3].end, self.createFrameTime(23))

    def test_syncWithAFirstSyncPoint(self):
        syncList = [self.createSyncPoint(0, 5, 7)]
        self._testedTimeSync.sync(syncList)

        self.assertEqual(self._subs[0].start, self.createFrameTime(5))
        self.assertEqual(self._subs[0].end, self.createFrameTime(7))

        self.assertNotEqual(self._subs[1].start, self.createFrameTime(25))
        self.assertNotEqual(self._subs[1].end,  self.createFrameTime(26))

        self.assertEqual(self._subs[-1].start, self.createFrameTime(30))
        self.assertEqual(self._subs[-1].end, self.createFrameTime(30))

    def test_syncWithALastPoint(self):
        syncList = [self.createSyncPoint(5, 5, 7)]
        self._testedTimeSync.sync(syncList)

        self.assertEqual(self._subs[0].start, self.createFrameTime(1))
        self.assertEqual(self._subs[0].end, self.createFrameTime(2))

        self.assertTrue(self._subs[1].start < self.createFrameTime(5))
        self.assertTrue(self._subs[1].end < self.createFrameTime(7))

        self.assertEqual(self._subs[-1].start, self.createFrameTime(5))
        self.assertEqual(self._subs[-1].end, self.createFrameTime(7))

    def test_syncWithASingleSyncPointNotAtStartOrEnd(self):
        syncList = [self.createSyncPoint(3, 5, 7)]
        self._testedTimeSync.sync(syncList)

        self.assertEqual(self._subs[0].start, self.createFrameTime(1))
        self.assertEqual(self._subs[0].end, self.createFrameTime(2))

        self.assertTrue(self._subs[1].start < self.createFrameTime(25))
        self.assertTrue(self._subs[1].end < self.createFrameTime(26))
        self.assertTrue(self._subs[1].start > self.createFrameTime(5))
        self.assertTrue(self._subs[1].end > self.createFrameTime(7))

        self.assertEqual(self._subs[3].start, self.createFrameTime(5))
        self.assertEqual(self._subs[3].end, self.createFrameTime(7))

        self.assertEqual(self._subs[-1].start, self.createFrameTime(30))
        self.assertEqual(self._subs[-1].end, self.createFrameTime(30))

    def test_syncWithTwoSyncPointsAtStartAndEnd(self):
        syncList = [
            self.createSyncPoint(0, 7, 8),
            self.createSyncPoint(5, 50, 60)
        ]
        self._testedTimeSync.sync(syncList)

        self.assertEqual(self._subs[0].start, self.createFrameTime(7))
        self.assertEqual(self._subs[0].end, self.createFrameTime(8))

        self.assertTrue(self._subs[2].start > self.createFrameTime(21))
        self.assertTrue(self._subs[2].end > self.createFrameTime(25))

        self.assertEqual(self._subs[-1].start, self.createFrameTime(50))
        self.assertEqual(self._subs[-1].end, self.createFrameTime(60))

    def test_syncWithTwoSyncPointNotAtStartOrEnd(self):
        syncList = [
            self.createSyncPoint(2, 7, 8),
            self.createSyncPoint(4, 50, 60)
        ]
        self._testedTimeSync.sync(syncList)

        # BEWARE! OGRES!
        # If some conditions are not clear, take a look at setUp method. We fill subs with some
        # silly values on purpose, sometimes lower than the previous ones. Syncing subtitles should
        # preserve these dependencies.
        self.assertEqual(self._subs[0].start, self.createFrameTime(1))
        self.assertEqual(self._subs[0].end, self.createFrameTime(2))

        self.assertTrue(self._subs[1].start > self.createFrameTime(7))
        self.assertTrue(self._subs[1].end > self.createFrameTime(8))

        self.assertEqual(self._subs[2].start, self.createFrameTime(7))
        self.assertEqual(self._subs[2].end, self.createFrameTime(8))

        self.assertTrue(self._subs[3].start > self.createFrameTime(7))
        self.assertEqual(self._subs[3].end, self.createFrameTime(8)) # see _calculateTime() comments
        self.assertTrue(self._subs[3].start < self.createFrameTime(50))

        self.assertEqual(self._subs[4].start, self.createFrameTime(50))
        self.assertEqual(self._subs[4].end, self.createFrameTime(60))

    def test_syncWithNotSortedSyncPoints(self):
        syncList = [
            self.createSyncPoint(2, 2, 3),
            self.createSyncPoint(1, 1, 2),
            self.createSyncPoint(5, 5, 6),
            self.createSyncPoint(4, 4, 5),
            self.createSyncPoint(3, 3, 4),
            self.createSyncPoint(0, 0, 1)
        ]

        self._testedTimeSync.sync(syncList)

        self.assertEqual(self._subs[0].start, self.createFrameTime(0))
        self.assertEqual(self._subs[0].end, self.createFrameTime(1))

        self.assertEqual(self._subs[1].start, self.createFrameTime(1))
        self.assertEqual(self._subs[1].end, self.createFrameTime(2))

        self.assertEqual(self._subs[2].start, self.createFrameTime(2))
        self.assertEqual(self._subs[2].end, self.createFrameTime(3))

        self.assertEqual(self._subs[3].start, self.createFrameTime(3))
        self.assertEqual(self._subs[3].end, self.createFrameTime(4))

        self.assertEqual(self._subs[4].start, self.createFrameTime(4))
        self.assertEqual(self._subs[4].end, self.createFrameTime(5))

        self.assertEqual(self._subs[5].start, self.createFrameTime(5))
        self.assertEqual(self._subs[5].end, self.createFrameTime(6))

