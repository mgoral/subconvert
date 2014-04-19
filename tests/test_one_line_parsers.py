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
import codecs

from subconvert.parsing import Formats
from subconvert.parsing import FrameTime

class TestParsers(unittest.TestCase):
    """Parsers UnitTest"""

    encoding = "utf8"
    fps = 25

    parsed = {
        'time_from': FrameTime.FrameTime(25, frames=28),
        'time_to': FrameTime.FrameTime(25, frames=75),
        'text': "Very simple subtitle parsing test.",
    }

    test_lines = [parsed.copy()]

    def parse(self, parser, file_to_parse, test_lines = None):
        lines = []

        if test_lines is None:
            test_lines = self.test_lines

        with codecs.open(file_to_parse, mode='r', encoding=self.encoding) as file_:
            file_input = file_.readlines()

        assert( 0 < len(file_input) )

        actual_parser = parser(file_to_parse, self.fps, self.encoding, file_input)
        actual_parser.parse()
        for i, parsed in enumerate(actual_parser.get_results()):
            lines.append(parsed)
            if parsed is not None:
                self.assertEqual( parsed['sub']['time_from'], test_lines[i]['time_from'] )
                self.assertEqual( parsed['sub']['time_to'], test_lines[i]['time_to'] )
                self.assertEqual( parsed['sub']['text'], test_lines[i]['text'] )

        assert( 0 < len(lines) )

    @unittest.skip("Whole test suite should be rewritten. No need to use real files.")
    def test_subrip(self):
        original_file = 'subs/Line.subrip'
        self.parse( Formats.SubRip, original_file )

    @unittest.skip("Whole test suite should be rewritten. No need to use real files.")
    def test_microdvd(self):
        original_file = 'subs/Line.microdvd'
        self.parse( Formats.MicroDVD, original_file )

    @unittest.skip("Whole test suite should be rewritten. No need to use real files.")
    def test_mpl2(self):
        original_file = 'subs/Line.mpl2'
        local_parsed = self.parsed.copy()
        local_parsed['time_to'] = FrameTime.FrameTime(25, seconds=3.0)
        local_parsed['time_from'] = FrameTime.FrameTime(25, seconds=1.1)
        self.parse( Formats.MPL2, original_file, [local_parsed] )

    @unittest.skip("Whole test suite should be rewritten. No need to use real files.")
    def test_subviewer(self):
        original_file = 'subs/Line.subviewer'
        self.parse( Formats.SubViewer, original_file )

    @unittest.skip("Whole test suite should be rewritten. No need to use real files.")
    def test_tmp(self):
        original_file = 'subs/Line.tmp'
        local_parsed = self.parsed.copy()
        local_parsed['time_to'] = ''
        local_parsed['time_from'] = FrameTime.FrameTime(25, frames=25)

        self.parse( Formats.TMP, original_file, [local_parsed] )

if __name__ == "__main__":
    unittest.main()
