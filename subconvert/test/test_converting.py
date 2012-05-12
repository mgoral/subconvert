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
import re

import subparser.SubParser as SubParser
import subparser.Parsers as Parsers
import subparser.Convert as Convert
import subutils.version as version

from subconvert import _


class TestConverting(unittest.TestCase):
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
        conv, lines = Convert.convert_file(file_to_parse, self.encoding, self.encoding, self.fps, converter.__OPT__)
        with codecs.open(output_filename, mode='w', encoding=self.encoding) as file_:
            file_.writelines(lines)
        return lines

    def compare(self, original_file, assert_file, remove_empty_lines = False):
        with codecs.open(original_file, mode = 'r', encoding = self.encoding) as file_:
            original_lines = file_.readlines()
        with codecs.open(assert_file, mode = 'r', encoding = self.encoding) as file_:
            assert_lines = file_.readlines()

        if remove_empty_lines:
            while os.linesep in original_lines:
                original_lines.remove(os.linesep)
            while os.linesep in assert_lines:
                assert_lines.remove(os.linesep)

        self.assertEqual(original_lines, assert_lines)
        

    def two_way_parser_test(self, tested_parser, original_file, remove_empty_lines = False):
        test_file = "subs/Test_%s.%s" % (tested_parser.__OPT__, tested_parser.__EXT__)

        conv = tested_parser(original_file, self.fps, self.encoding)
        self.convert(conv, original_file, test_file)

        self.compare(original_file, test_file, remove_empty_lines)

    def test_subrip(self):
        log.info(" \n... running SubRip test")
        self.two_way_parser_test(Parsers.SubRip, 'subs/SubSample.subrip', True)

    def test_microdvd(self):
        log.info(" \n... running MicroDVD test")
        self.two_way_parser_test(Parsers.MicroDVD, 'subs/SubSample.microdvd', True)

    def test_mpl2(self):
        log.info(" \n... running MPL2 test")
        self.two_way_parser_test(Parsers.MPL2, 'subs/SubSample.mpl2', True)

    def test_subviewer(self):
        log.info(" \n... running SubViewer test")
        self.two_way_parser_test(Parsers.SubViewer, 'subs/SubSample.subviewer', True)
        
    def test_tmp(self):
        log.info(" \n... running TMP test")
        self.two_way_parser_test(Parsers.TMP, 'subs/SubSample.tmp', True)
        
if __name__ == "__main__":
    log = logging.getLogger('SubConvert')
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())
    log.info("Testing SubConvert, version %s." % version.__version__)
    log.info(datetime.datetime.now().isoformat())
    unittest.main()
        
