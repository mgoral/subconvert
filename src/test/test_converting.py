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



class TestParsers(unittest.TestCase):
    """Parsers UnitTest"""

    original_file = "subs/SubSample.microdvd"
    encoding = "utf8"
    fps = 25
    with codecs.open(original_file, mode='r', encoding=encoding) as file_:
        file_input = file_.readlines()
    with codecs.open(original_file, mode='rb', encoding=encoding) as file_:
        orig_md5 = hashlib.md5(file_.read())
    subs_no = len(file_input)

    def convert(self, converter, file_to_parse, output_filename):
        lines = []

        conv, lines = Convert.convert_file(file_to_parse, self.encoding, self.fps, converter.__OPT__)

        with codecs.open(output_filename, mode='w', encoding=self.encoding) as file_:
            file_.writelines(lines)
        return lines


    def two_way_parser_test(self, tested_parser, head_lines = 0):
        test_file = "subs/Test_%s.%s" % (tested_parser.__OPT__, tested_parser.__EXT__)
        assert_file = "subs/Assert_%s.subc" % tested_parser.__OPT__
        lines = []

        conv = tested_parser(self.original_file, self.fps, self.encoding)
        lines = self.convert(conv, self.original_file, test_file)

        self.assertEqual(self.subs_no, len(lines) - head_lines)

        with codecs.open(test_file, mode='r', encoding=self.encoding) as file_:
            test_file_input = file_.readlines()

        conv = Parsers.MicroDVD(test_file, self.fps, self.encoding)
        lines = self.convert(conv, test_file, assert_file)
        
        with open(assert_file, mode='rb') as file_:
            assert_md5 = hashlib.md5(file_.read())
        
        self.assertEqual(self.orig_md5.hexdigest(), assert_md5.hexdigest())

    def test_subrip(self):
        log.info(" \n... running SubRip test")
        self.two_way_parser_test(Parsers.SubRip)

    def test_microdvd(self):
        log.info(" \n... running MicroDVD test")
        self.two_way_parser_test(Parsers.MicroDVD)

    def test_subviewer(self):
        log.info(" \n... running SubViewer test")
        self.two_way_parser_test(Parsers.SubViewer, 1)
        
    def test_tmp(self):
        log.info(" \n... running TMP test")
        tested_parser = Parsers.TMP
        test_file = "subs/Test_%s.%s" % (tested_parser.__OPT__, tested_parser.__EXT__)
        parser = Parsers.MicroDVD(self.original_file, self.fps, self.encoding, self.file_input)
        conv = tested_parser(self.original_file, self.fps, self.encoding)
        lines = self.convert(conv, self.original_file, test_file)
        self.assertEqual(self.subs_no, len(lines) ) # TMP will remove subs with incorrect timing
        
if __name__ == "__main__":
    log = logging.getLogger('SubConvert')
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())
    log.info("Testing SubConvert, version %s." % version.__version__)
    log.info(datetime.datetime.now().isoformat())
    unittest.main()
        
