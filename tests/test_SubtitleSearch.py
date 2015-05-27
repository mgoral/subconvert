#-*- coding: utf-8 -*-

"""
Copyright (C) 2015 Michal Goral.

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
from subconvert.utils.SubtitleSearch import *
from tests.Mocks import SubtitleMock

def abcMatcher(sub):
    return "abc" in sub.text

class TestSubtitleSearch(unittest.TestCase):
    """SubtitleSearch test suite."""

    # for matchText tests
    sub = SubtitleMock(text = "zażółć Gęślą jaźń")

    # for SearchIterator tests
    subs = [
        SubtitleMock(text = "abc1"),
        SubtitleMock(text = "nothing"),
        SubtitleMock(text = "abc2"),
        SubtitleMock(text = "nothing"),
        SubtitleMock(text = "nothing"),
        SubtitleMock(text = "abc3")]
    subsAbcMatches = [0, 2, 5]

    #
    # matchText
    #
    def test_matchText_returnFalseWhenSearchPhraseIsEmpty(self):
        searchPhrase = ""
        case = True
        self.assertFalse(matchText(self.sub, searchPhrase, case))

    def test_matchText_matchCaseInsensitiveSearch(self):
        searchPhrase = self.sub.text.lower()
        case = False
        self.assertTrue(matchText(self.sub, searchPhrase, case))

    def test_matchText_doNotMatchCaseInsensitiveSearch(self):
        searchPhrase = "zaaażóóółćć Gęęślląąą jaaźńń"
        case = False
        self.assertFalse(matchText(self.sub, searchPhrase, case))

    def test_matchText_matchCaseSensitiveSearch(self):
        searchPhrase = self.sub.text
        case = True
        self.assertTrue(matchText(self.sub, searchPhrase, case))

    def test_matchText_doNotMatchCaseSensitiveSearch(self):
        searchPhrase1 = self.sub.text.lower()
        searchPhrase2 = "zaaażóóółćć Gęęślląąą jaaźńń"
        case = True
        self.assertFalse(matchText(self.sub, searchPhrase1, case))
        self.assertFalse(matchText(self.sub, searchPhrase2, case))

    #
    # SearchIterator
    #
    def test_SearchIterator_range(self):
        si = SearchIterator(self.subs, abcMatcher)
        self.assertEqual(si.range(), self.subsAbcMatches)

    def test_SearchIterator_lastAtBeginning(self):
        si = SearchIterator(self.subs, abcMatcher)
        self.assertEqual(si.last(), self.subsAbcMatches[0])

    def test_SearchIterator_lastAfterNext(self):
        si = SearchIterator(self.subs, abcMatcher)

        v1 = si.next()
        self.assertEqual(si.last(), v1)

        v2 = si.next()
        self.assertEqual(si.last(), v2)

    def test_SearchIterator_next(self):
        si = SearchIterator(self.subs, abcMatcher)

        self.assertEqual(si.next(), self.subsAbcMatches[0])
        self.assertEqual(si.next(), self.subsAbcMatches[1])
        self.assertEqual(si.next(), self.subsAbcMatches[2])
        self.assertEqual(si.next(), self.subsAbcMatches[0])

    def test_SearchIterator_prev(self):
        si = SearchIterator(self.subs, abcMatcher)

        self.assertEqual(si.prev(), self.subsAbcMatches[2])
        self.assertEqual(si.prev(), self.subsAbcMatches[1])
        self.assertEqual(si.prev(), self.subsAbcMatches[0])
        self.assertEqual(si.prev(), self.subsAbcMatches[2])

    def test_SearchIterator_nextAndPrev(self):
        si = SearchIterator(self.subs, abcMatcher)

        self.assertEqual(si.next(), self.subsAbcMatches[0])
        self.assertEqual(si.prev(), self.subsAbcMatches[2])

    def test_SearchIterator_setpos(self):
        si = SearchIterator(self.subs, abcMatcher)

        si.setpos(1)
        self.assertEqual(si.last(), self.subsAbcMatches[1])
        self.assertEqual(si.next(), self.subsAbcMatches[2])

        si.setpos(1)
        self.assertEqual(si.prev(), self.subsAbcMatches[0])
