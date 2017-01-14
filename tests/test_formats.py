"""
Copyright (C) 2016 Michal Goral.

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

import os
import glob
import collections
import json

import pytest

from subconvert.utils.SubFile import File
from subconvert.parsing.Core import SubParser, Subtitle
from subconvert.parsing.FrameTime import FrameTime 
from subconvert.parsing.Formats import MicroDVD, SubRip, SubViewer, TMP, MPL2

_SubParams = collections.namedtuple('SubParams', ['contents', 'description'])


def _json_decoder(dct):
    if '__FrameTime__' in dct:
        fps = dct.get('fps', 25)
        kw = {}
        for arg in ('time', 'frames', 'seconds'):
            if arg in dct:
                kw[arg] = dct[arg]
        return FrameTime(fps, **kw)
    elif '__Subtitle__' in dct:
        return Subtitle(dct.get('start'), dct.get('end'), dct.get('text'))
    return dct


def gen_params():
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    subtitles = glob.glob(os.path.join(curr_dir, 'subs', '*.txt'))

    ret = []
    for sub_name in subtitles:
        descr_name = '%s.json' % os.path.splitext(sub_name)[0]
        with open(descr_name) as f:
            descr = json.load(f, object_hook=_json_decoder)
            ret.append(_SubParams(contents=File(sub_name).read(),
                                  description=descr))
    return ret


@pytest.fixture
def parser():
    parser = SubParser()
    parser.registerFormat(MicroDVD)
    parser.registerFormat(SubRip)
    parser.registerFormat(SubViewer)
    parser.registerFormat(TMP)
    parser.registerFormat(MPL2)
    return parser


@pytest.mark.parametrize('params', gen_params())
def test_correct_subs(parser, params):
    contents, descr = params

    parser.parse(contents)
    fmt = parser.parsedFormat()
    subs = parser.results

    assert fmt.NAME == descr['format']
    assert fmt.OPT == descr['opt']

    assert len(descr['subs']) == len(subs)
    for i, check in enumerate(descr['subs']):
        sub = subs[i]
        assert sub.start == check.start
        assert not check.end or sub.end == check.end
        assert sub.text == check.text

    if descr.get('header') is not None:
        for key in descr['header']:
            subs.header().get(key) == descr['header'][key]
