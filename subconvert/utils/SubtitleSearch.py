#-*- coding: utf-8 -*-

"""
Copyright (C) 2011-2015 Michal Goral.

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

def matchText(sub, text, case):
    if (text == ""): return False
    if case is True:
        if text in sub.text: return True
    else:
        if text.lower() in sub.text.lower(): return True
    return False

class SearchIterator:
    def __init__(self, subs, matcher):
        """
        subs: list of subtitles (list(subconvert.parsing.Subtitle))
        matcher: function returning True when single subtitle matches a given criteria
        """
        self._range = [i for i, sub in enumerate(subs) if matcher(sub)]
        self._idx = -1

    def __iter__(self):
        return self

    def range(self):
        return self._range

    def last(self):
        """Returns the last element accessed via next() or prev().
        Returns the first element of range() if neither of these was called."""
        if len(self._range) == 0:
            raise IndexError("range is empty")
        if self._idx == -1:
            return self._range[0]
        return self._get(self._idx)

    def next(self):
        return self._get(self._idx + 1)

    def prev(self):
        return self._get(self._idx - 1)

    def setpos(self, pos):
        self._idx = pos

    def _indexInRange(self, index):
        if index < 0:
            index = len(self._range) - 1
        elif index >= len(self._range):
            index = 0
        return index

    def _get(self, index):
        if len(self._range) == 0:
            raise StopIteration

        self._idx = self._indexInRange(index)
        return self._range[self._idx]
