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

import subparser.SubParser as SubParser
import subparser.Parsers as Parsers
import subparser.Convert as Convert
import subparser.version as version



class TestParsers(unittest.TestCase):
    """Parsers UnitTest"""

    def setUp(self):
        log = logging.getLogger('SubConvert')
        log.setLevel(logging.DEBUG)
        log.addHandler(logging.StreamHandler())
        self.original_filename = "SubSample.sub"
        self.encoding = "utf8"
        self.fps = 25
        print "Testing SubConvert, version %s.\n\n" % version.__version__
        with codecs.open(self.original_filename, mode='r', encoding=self.encoding) as file_:
            self.file_input = file_.readlines()
        self.subs_no = len(self.file_input)
        #self.original_hash = hash(self.file_input)

    def test_subrip(self):
        print " ... running SubRip test"
        lines = []
        parsed_1 = []
        subrip_lines = []
        parsed_2 = []
        cl = Parsers.MicroDVD(self.original_filename, self.fps, self.encoding, self.file_input)
        conv = Parsers.SubRip(self.original_filename, self.fps, self.encoding)
        for parsed in cl.parse():
            parsed_1.append(parsed)
            if parsed is None:
                break
            sub = conv.convert(parsed)
            lines.append(sub.decode(conv.encoding))

        self.assertEqual(self.subs_no, len(lines))

        cl = Parsers.SubRip(self.original_filename, self.fps, self.encoding, lines)
        conv = Parsers.MicroDVD(self.original_filename, self.fps, self.encoding)

        for parsed in cl.parse():
            print 'a'
            parsed_2.append(parsed)
            if parsed is None:
                break
            sub = conv.convert(parsed)
            subrip_lines.append(sub.decode(conv.encoding))

        self.assertEqual(self.subs_no, len(lines))
        self.assertEqual(parsed_1, parsed_2)
        
        #self.assertEqual(self.original_hash, hash(subrip_lines))


if __name__ == "__main__":
    unittest.main()


        
        
