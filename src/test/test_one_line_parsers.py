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

import os
import sys
import unittest
import codecs
import logging
import hashlib
import datetime

import subparser.SubParser as SubParser
import subparser.Parsers as Parsers
import subparser.Convert as Convert
import subparser.version as version
import subparser.FrameTime as FrameTime



class TestParsers(unittest.TestCase):
    """Parsers UnitTest"""

    encoding = "utf8"
    fps = 25

    parsed = {
        'time_from': FrameTime.FrameTime(25, 'frame', frame=28),
        'time_to': FrameTime.FrameTime(25, 'frame', frame=75),
        'text': u'Very simple subtitle parsing test.',
    }

    test_lines = [parsed.copy()]

    def parse(self, parser, file_to_parse, test_lines = None):
        lines = []

        if test_lines is None:
            test_lines = self.test_lines

        with codecs.open(file_to_parse, mode='r', encoding=self.encoding) as file_:
            file_input = file_.readlines()

        assert( 0 < len(file_input) )

        for i, parsed in enumerate(parser(file_to_parse, self.fps, self.encoding, file_input).parse()):
            lines.append(parsed)
            if parsed is not None:
                self.assertEqual( parsed['sub']['time_from'], test_lines[i]['time_from'] )
                self.assertEqual( parsed['sub']['time_to'], test_lines[i]['time_to'] )
                self.assertEqual( parsed['sub']['text'], test_lines[i]['text'] )

        assert( 0 < len(lines) )

    def test_subrip(self):
        log.info(" \n... running SubRip test")
        original_file = 'subs/Line.subrip'
        self.parse( Parsers.SubRip, original_file )

    def test_microdvd(self):
        log.info(" \n... running MicroDVD test")
        original_file = 'subs/Line.microdvd'
        self.parse( Parsers.MicroDVD, original_file )

    def test_mpl2(self):
        log.info(" \n... running MPL2 test")
        original_file = 'subs/Line.mpl2'
        local_parsed = self.parsed.copy()
        local_parsed['time_to'] = FrameTime.FrameTime(25, 'full_seconds', seconds=3.0)
        local_parsed['time_from'] = FrameTime.FrameTime(25, 'full_seconds', seconds=1.1)
        self.parse( Parsers.MPL2, original_file, [local_parsed] )

    def test_subviewer(self):
        log.info(" \n... running SubViewer test")
        original_file = 'subs/Line.subviewer'
        self.parse( Parsers.SubViewer, original_file )
        
    def test_tmp(self):
        log.info(" \n... running TMP test")
        original_file = 'subs/Line.tmp'
        local_parsed = self.parsed.copy()
        local_parsed['time_to'] = ''
        local_parsed['time_from'] = FrameTime.FrameTime(25, 'frame', frame=25)
        
        self.parse( Parsers.TMP, original_file, [local_parsed] )
        
if __name__ == "__main__":
    log = logging.getLogger('SubConvert')
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())
    log.info("Testing SubConvert, version %s." % version.__version__)
    log.info(datetime.datetime.now().isoformat())
    unittest.main()
        
