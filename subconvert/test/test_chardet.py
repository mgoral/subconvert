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
import subutils.version as version
import subparser.FrameTime as FrameTime

class TestChardet(unittest.TestCase):
    """Chardet UnitTest.
    Please use enconv to convert enc.utf8 to other encodings."""

    def test_utf8(self):
        log.info(" \n... running UTF-8 test")
        original_file = 'subs/enc.utf8'
        converter = Convert.SubConverter(original_file)
        encoding = converter.getEncoding()
        self.assertEqual( encoding.lower(), 'utf-8' )

    def test_utf8_specif(self):
        log.info(" \n... running UTF-8 specif test")
        original_file = 'subs/enc.utf8'
        converter = Convert.SubConverter(original_file)
        encoding = converter.changeEncoding('utf8').getEncoding()
        self.assertEqual( encoding.lower(), 'utf8' )

    def test_cp1250(self):
        log.info(" \n... running CP 1250 test")
        original_file = 'subs/enc.cp1250'
        converter = Convert.SubConverter(original_file)
        encoding = converter.getEncoding()
        self.assertEqual( encoding.lower(), 'windows-1250' )

    def test_cp1250_specif(self):
        log.info(" \n... running CP 1250 specif test")
        original_file = 'subs/enc.cp1250'
        converter = Convert.SubConverter(original_file)
        encoding = converter.changeEncoding('cp1250').getEncoding()
        self.assertEqual( encoding.lower(), 'cp1250' )

    def test_iso_8859_2(self):
        log.info(" \n... running ISO 8859-2 test")
        original_file = 'subs/enc.iso88592'
        converter = Convert.SubConverter(original_file)
        encoding = converter.getEncoding()
        self.assertEqual( encoding.lower(), 'iso-8859-2' )

    def test_iso_8859_2_specif(self):
        log.info(" \n... running ISO 8859-2 specif test")
        original_file = 'subs/enc.iso88592'
        converter = Convert.SubConverter(original_file)
        encoding = converter.changeEncoding('iso-8859-2').getEncoding()
        self.assertEqual( encoding.lower(), 'iso-8859-2' )

if __name__ == "__main__":
    log = logging.getLogger('SubConvert')
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())
    log.info("Testing SubConvert, version %s." % version.__version__)
    log.info(datetime.datetime.now().isoformat())
    unittest.main()

