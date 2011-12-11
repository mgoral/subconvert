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
        self.original_file = "SubSample.sub"
        self.encoding = "utf8"
        self.fps = 25
        print "Testing SubConvert, version %s.\n\n" % version.__version__
        with codecs.open(self.original_file, mode='r', encoding=self.encoding) as file_:
            self.file_input = file_.readlines()
        with codecs.open(self.original_file, mode='rb', encoding=self.encoding) as file_:
            self.orig_md5 = hashlib.md5(file_.read())
        self.subs_no = len(self.file_input)

    def convert(self, parser, converter, filename):
        lines = []
        for parsed in parser.parse():
            if parsed is None:
                break
            sub = converter.convert(parsed)
            lines.append(sub.decode(converter.encoding))
        with codecs.open(filename, mode='w', encoding=self.encoding) as file_:
            file_.writelines(lines)
        return lines

    def two_way_parser_test(self, tested_parser):
        test_file = "Test_%s.%s" % (tested_parser.__OPT__, tested_parser.__EXT__)
        assert_file = "Assert_%s.subc" % tested_parser.__OPT__
        lines = []
        parsed_1 = []
        subrip_lines = []
        parsed_2 = []

        parser = Parsers.MicroDVD(self.original_file, self.fps, self.encoding, self.file_input)
        conv = tested_parser(self.original_file, self.fps, self.encoding)
        lines = self.convert(parser, conv, test_file)

        self.assertEqual(self.subs_no, len(lines))

        with codecs.open(test_file, mode='r', encoding=self.encoding) as file_:
            test_file_input = file_.readlines()

        parser = tested_parser(test_file, self.fps, self.encoding, test_file_input)
        conv = Parsers.MicroDVD(test_file, self.fps, self.encoding)
        lines = self.convert(parser, conv, assert_file)
        
        with open(assert_file, mode='rb') as file_:
            assert_md5 = hashlib.md5(file_.read())

        if( not self.assertEqual(self.orig_md5.hexdigest(), assert_md5.hexdigest()) ):
            os.remove(test_file)
            os.remove(assert_file)

    def test_subrip(self):
        print " ... running SubRip test"
        self.two_way_parser_test(Parsers.SubRip)
        
if __name__ == "__main__":
    unittest.main()
        
