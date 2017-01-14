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

import itertools
import collections
import pytest

from subconvert.cli.syncparse import parse
from subconvert.parsing.Core import SubManager, Subtitle
from subconvert.parsing.FrameTime import FrameTime
from subconvert.utils.SubException import SubException

_Format = collections.namedtuple("Format", ['time', 'variants'])

@pytest.fixture
def fps():
    return 25

@pytest.fixture
def subs(fps):
    sm = SubManager()
    sm.append(Subtitle(start=FrameTime(fps, seconds=10),
                       end=FrameTime(fps, seconds=19),
                       text="subtitle 0"))
    sm.append(Subtitle(start=FrameTime(fps, seconds=20),
                       end=FrameTime(fps, seconds=29),
                       text="subtitle 1"))
    sm.append(Subtitle(start=FrameTime(fps, seconds=30),
                       end=FrameTime(fps, seconds=39),
                       text="subtitle 2"))
    return sm


def sync_variants(*args):
    def _str_variants(s, end):
        no, _, timestr = s.partition(':')
        no = no.strip()
        timestr = timestr.strip()

        return ['%s: %s%s' % (no, timestr, end),
                '%s:%s%s' % (no, timestr, end),
                ' %s:%s%s ' % (no, timestr, end),
                ' %s:%s, ' % (no, timestr),
               ]

    end = ',' if len(args) > 1 else ''
    variants = [_str_variants(s, end) for s in args]
    return [''.join(prod) for prod in itertools.product(*variants)]


def formats(hour=None, minute=None, second=None, ms=None):
    def _variants(no, unit):
        if no is None:
            return ['']
        return ['%d %s' % (no, unit),
                '%d%s' % (no, unit),
                '%d%s ' % (no, unit)]

    arg_mix = itertools.permutations([[hour, 'h'], [minute, 'm'], 
                                      [second, 's'], [ms, 'ms']])

    # different places of hour/minute/second/ms, ie:
    # 1m10ms vs 10ms1m (both should be correct)
    variants = []
    for a in arg_mix:
        v = [''.join(prod) 
             for prod in itertools.product(_variants(a[0][0], a[0][1]),
                                           _variants(a[1][0], a[1][1]),
                                           _variants(a[2][0], a[2][1]),
                                           _variants(a[3][0], a[3][1]))]
        variants.extend(v)

    if hour is None: hour = 0
    if minute is None: minute = 0
    if second is None: second = 0
    if ms is None: ms = 0
    seconds = (3600*hour + 60*minute + second + float(ms)/1000)

    return _Format(time=seconds, variants=variants)


def gen_fmts():
    """Generate formats where hour/minute/... number can be each of the numbers
    specified in `values` variable. When it's None, it is skipped in format
    string and is printed otherwise."""
    values = [23, 1, 0, None]  # Important: keep None as last element
    # we skip the last element: (None, None, None, None), which would produce
    # empty format string - there is a separate test for it
    return [formats(*prod) 
            for prod in itertools.product(values, values, values, values)][:-1]

def test_parse_empty(subs):
    assert 0 == len(parse("", subs))
    assert 0 == len(parse(",,,", subs))


@pytest.mark.parametrize('sync', sync_variants('1: +15s'))
def test_parse_add(subs, fps, sync):
    check = parse(sync, subs)
    assert len(check) == 1
    sp = check[0]
    assert sp.subNo == 0
    assert sp.start == FrameTime(fps, seconds=15) + subs[sp.subNo].start
    assert sp.end == FrameTime(fps, seconds=15) + subs[sp.subNo].end


@pytest.mark.parametrize('sync', sync_variants('1: -5s'))
def test_parse_substract(subs, fps, sync):
    check = parse(sync, subs)
    assert len(check) == 1
    sp = check[0]
    assert sp.subNo == 0
    assert sp.start == subs[sp.subNo].start - FrameTime(fps, seconds=5) 
    assert sp.end == subs[sp.subNo].end - FrameTime(fps, seconds=5) 

@pytest.mark.parametrize('sync', sync_variants('1: -30s'))
def test_parse_substract_too_much(subs, fps, sync):
    with pytest.raises(SubException):
        parse(sync, subs)


@pytest.mark.parametrize('sync', sync_variants('1: +5s', '2: -10s'))
def test_parse_mix_add_substract(subs, fps, sync):
    check = parse(sync, subs)
    assert len(check) == 2

    first, second = check
    assert first.subNo == 0
    assert first.start == FrameTime(fps, seconds=5) + subs[first.subNo].start
    assert first.end == FrameTime(fps, seconds=5) + subs[first.subNo].end

    assert second.subNo == 1
    assert second.start == subs[second.subNo].start - FrameTime(fps, seconds=10) 
    assert second.end == subs[second.subNo].end - FrameTime(fps, seconds=10) 

@pytest.mark.parametrize('sync', sync_variants('-1: +5s'))
def test_parse_negative_index(subs, fps, sync):
    check = parse(sync, subs)
    assert len(check) == 1
    sp = check[0]

    assert sp.subNo == len(subs) - 1
    assert sp.start == FrameTime(fps, seconds=5) + subs[sp.subNo].start
    assert sp.end == FrameTime(fps, seconds=5) + subs[sp.subNo].end


def test_parse_offset_add(subs, fps):
    check = parse('+3s', subs)
    assert len(check) == len(subs)

    for i, sp in enumerate(check):
        assert sp.subNo == i
        assert sp.start == subs[sp.subNo].start + FrameTime(fps, seconds=3)
        assert sp.end == subs[sp.subNo].end + FrameTime(fps, seconds=3)


def test_parse_offset_substract(subs, fps):
    check = parse('-3s', subs)
    assert len(check) == len(subs)

    for i, sp in enumerate(check):
        assert sp.subNo == i
        assert sp.start == subs[sp.subNo].start - FrameTime(fps, seconds=3)
        assert sp.end == subs[sp.subNo].end - FrameTime(fps, seconds=3)


def test_parse_offset_substract_too_much(subs):
    with pytest.raises(SubException):
        parse('-300s', subs)


def test_parse_mix_sync_and_offset(subs):
    with pytest.raises(SubException):
        parse('1: +3s, +2s', subs)

    with pytest.raises(SubException):
        parse('+2s, 1: +3s', subs)


def test_parse_single_time_for_all_subtitles(subs):
    with pytest.raises(SubException):
        parse('5s', subs)


def test_parse_multiple_offsets(subs):
    with pytest.raises(SubException):
        parse('+3s,+5s', subs)


def test_parse_incorrect_index(subs):
    # indexing starts from 1
    with pytest.raises(SubException):
        parse('0:+3s', subs)

    with pytest.raises(SubException):
        parse('%d:+3s' % (1 + len(subs)), subs)


@pytest.mark.slow
@pytest.mark.parametrize('fmt', gen_fmts())
def test_formats(subs, fps, fmt):
    fmt_ft = FrameTime(fps, seconds=fmt.time)
    for variant in fmt.variants:
        check = parse('1: %s' % variant, subs)
        assert len(check) == 1
        sp = check[0]
        assert sp.subNo == 0
        assert sp.start == fmt_ft
        assert sp.end == fmt_ft + (subs[sp.subNo].end - subs[sp.subNo].start)


def test_parse_multiple_same_units(subs):
    with pytest.raises(SubException):
        parse('1:+3s2s', subs)

    with pytest.raises(SubException):
        parse('1:+3h2h', subs)

    with pytest.raises(SubException):
        parse('1:+3m2m', subs)

    with pytest.raises(SubException):
        parse('1:+3ms2ms', subs)


def test_parse_incorrect_time_spec(subs):
    with pytest.raises(SubException):
        parse('1:+3msblah', subs)

    with pytest.raises(SubException):
        parse('a:+3ms', subs)

    with pytest.raises(SubException):
        parse('1:=3ms', subs)

    with pytest.raises(SubException):
        parse('1:h3ms', subs)

    with pytest.raises(SubException):
        parse('1: 1: +15s', subs)

    with pytest.raises(SubException):
        parse('1:', subs)

    with pytest.raises(SubException):
        parse(':_15s', subs)
