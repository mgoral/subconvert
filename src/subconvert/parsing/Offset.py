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

import logging

from subconvert.utils.Locale import _
from subconvert.utils.SubException import SubAssert
from subconvert.parsing.FrameTime import FrameTime

log = logging.getLogger('Subconvert.%s' % __name__)

class SyncPoint:
    subNo = None # int
    start = None # FrameTime
    end = None # FrameTime

    def __init__(self, subNo, timeStart, timeEnd):
        SubAssert(isinstance(subNo, int), "Subtitle number is not an integer", TypeError)
        SubAssert(subNo >= 0, "Subtitle number is less than 0!", ValueError)
        SubAssert(type(timeStart) is FrameTime, "Sync start is not a FrameTime!", TypeError)
        SubAssert(type(timeEnd) is FrameTime, "Sync end is not a FrameTime!", TypeError)

        self.subNo = subNo
        self.start = timeStart
        self.end = timeEnd

    def __eq__(self, other):
        return self.subNo == other.subNo

    def __lt__(self, other):
        return self.subNo < other.subNo

    def __str__(self):
        return "%d: [%s][%s]" % (self.subNo, self.start, self.end)

class TimeSync():
    """In-place subtitles synchronizer."""

    def __init__(self, subtitles):
        self._subs = subtitles

    def sync(self, syncPointList):
        """Synchronise subtitles using a given list of SyncPoints."""

        if len(syncPointList) == 0:
            return

        subsCopy = self._subs.clone()

        syncPointList.sort()

        SubAssert(syncPointList[0].subNo >= 0)
        SubAssert(syncPointList[0].subNo < subsCopy.size())
        SubAssert(syncPointList[-1].subNo < subsCopy.size())

        # Always start from the first subtitle.
        firstSyncPoint = self._getLowestSyncPoint(syncPointList, subsCopy)
        if firstSyncPoint != syncPointList[0]:
            syncPointList.insert(0, firstSyncPoint)

        for i, syncPoint in enumerate(syncPointList):

            # Algorithm:
            # 1. Calculate time deltas between sync points and between subs:
            #        DE_OLD = subTime[secondSyncSubNo] - subTime[firstSyncSubNo]
            #        DE_NEW = secondSyncTime - firstSyncTime
            # 2. Calculate proportional sub position within DE_OLD:
            #        d = (subTime - subTime[firstSubNo]) / DE_OLD
            # 3. "d" is constant within deltas, so we can now calculate newSubTime:
            #        newSubTime = DE_NEW * d + firstSyncTime

            firstSyncPoint = syncPointList[i]
            secondSyncPoint = self._getSyncPointOrEnd(i + 1, syncPointList, subsCopy)

            log.debug(_("Syncing times for sync points:"))
            log.debug("  %s" % firstSyncPoint)
            log.debug("  %s" % secondSyncPoint)

            # A case for the last one syncPoint
            if firstSyncPoint == secondSyncPoint:
                continue

            secondSubNo = secondSyncPoint.subNo
            firstSubNo = firstSyncPoint.subNo

            firstOldSub = subsCopy[firstSubNo]
            secondOldSub = subsCopy[secondSubNo]

            oldStartDelta, oldEndDelta = self._getDeltas(firstOldSub, secondOldSub)
            newStartDelta, newEndDelta = self._getDeltas(firstSyncPoint, secondSyncPoint)

            for subNo in range(firstSubNo, secondSubNo + 1):
                sub = subsCopy[subNo]
                newStartTime = self._calculateTime(sub.start, firstOldSub.start,
                    firstSyncPoint.start, oldStartDelta, newStartDelta)
                newEndTime = self._calculateTime(sub.end, firstOldSub.end,
                    firstSyncPoint.end, oldEndDelta, newEndDelta)

                self._subs.changeSubStart(subNo, newStartTime)
                self._subs.changeSubEnd(subNo, newEndTime)

    def _getDeltas(self, firstSub, secondSub):
        """Arguments must have "start" and "end" properties which are FrameTimes."""
        startDelta = max(firstSub.start, secondSub.start) - min(firstSub.start, secondSub.start)
        endDelta = max(firstSub.end, secondSub.end) - min(firstSub.end, secondSub.end)
        return (startDelta, endDelta)

    def _calculateTime(self, currentSubTime, firstOldTime, firstSyncTime, oldDelta, newDelta):
        if currentSubTime < firstOldTime:
            log.warning(_("Currently synced subtitle has lower time than a previous one:" "%s < %s")
                % (currentSubTime, firstOldTime))

        # Safety fuse. FrameTime disallows substracting higher time from the lower one but in some
        # corner cases this might be the case.
        # For example, when current time is lower than the previous one (i.e. firstOldTime), it
        # clearly means that subs are incorrect, but we'll still try to do something with them.
        # Because of basic physics (time continuity), we can safely assume that a given sub occurs
        # AT LEAST at firstOldTime (which will be the case when secondsWithoutOffset is set to 0)
        secondsWithoutOffset = max(0.0, currentSubTime.fullSeconds - firstOldTime.fullSeconds)

        proportion = secondsWithoutOffset / oldDelta.fullSeconds
        newTime = firstSyncTime + newDelta * proportion
        return newTime

    def _getLowestSyncPoint(self, syncPointList, subs):
        """Get the lowest possible sync point. If it is not the first one on the **sorted**
        syncPointList, first subtitle will be converted to the one."""
        if syncPointList[0].subNo == 0:
            return syncPointList[0]
        return SyncPoint(0, subs[0].start, subs[0].end)

    def _getSyncPointOrEnd(self, index, syncPointList, subs):
        if index < len(syncPointList):
            return syncPointList[index]

        lastSubIndex = subs.size() - 1
        lastSub = subs[-1]
        ret = SyncPoint(lastSubIndex, lastSub.start, lastSub.end)
        return ret

