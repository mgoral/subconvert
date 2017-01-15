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

import itertools
import pytest
import collections

from subconvert.parsing.FrameTime import FrameTime, ms2f, f2ms
import subconvert.utils.version as version

from subconvert.apprunner import _

_FTVals = collections.namedtuple('FrameTimeValues', ['fps', 'ms', 'frame'])

def gen_operands():
    lhs = [100, -100]
    rhs = [100, -100, 200, -200]
    return itertools.product(lhs, rhs)


def gen_ftvals():
    positives = [_FTVals(25, 1000, 25),
                 _FTVals(25, 300, 7.5),
                 _FTVals(25, 777, 19.425),
                ]

    ret = []
    for val in positives:
        ret.append(val)
        ret.append(_FTVals(val.fps, -1 * val.ms, -1 * val.frame))
    return ret


@pytest.mark.parametrize('params', gen_ftvals())
def test_ms2f(params):
    assert round(params.frame) == ms2f(params.ms, params.fps)


@pytest.mark.parametrize('params', gen_ftvals())
def test_f2ms(params):
    assert params.ms == f2ms(params.frame, params.fps)


def test_init_incorrect_fps():
    with pytest.raises(ValueError):
        FrameTime(0, 5)

    with pytest.raises(ValueError):
        FrameTime(0, -5)


def test_time_dict():
    # 1h 1m 1s 101ms
    ft = FrameTime(25, 3661101)

    expected = dict(hours=1, minutes=1, seconds=1, milliseconds=101)
    assert ft.time == expected


@pytest.mark.parametrize('param_pair', [(3661101, '1:01:01.101'),
                                        (3661101, '+1:01:01.101'),
                                        (-3661101, '-1:01:01.101')])
def test_init_time_string(param_pair):
    ms, timestr = param_pair
    ft = FrameTime.InitTimeStr(25, timestr)
    assert ft.fps == 25
    assert ft.ms == ms
    assert ft.frame == ms2f(ms, 25)

@pytest.mark.parametrize('param', [3661100, 3661010, 3661001,
                                   -3661100, -3661010, -3661001])
def test_init(param):
    ft = FrameTime(23.1, param)
    assert ft.fps == 23.1
    assert ft.ms == param
    assert ft.frame == ms2f(param, 23.1)

@pytest.mark.parametrize('param', [100, 40120, -100, -40120, 11, 13, 13346871])
def test_init_frames(param):
    ft = FrameTime.InitFrames(23.1, param)
    assert ft.fps == 23.1
    assert ft.frame == param
    assert ft.ms == f2ms(param, 23.1)


def test_incorrectly_formatted_time():
    with pytest.raises(ValueError):
        FrameTime.InitTimeStr(25, "1:12;44-999")


@pytest.mark.parametrize('same', [(FrameTime(25, 1000),
                                   FrameTime.InitFrames(25, 25),
                                   FrameTime.InitTimeStr(25, '0:00:01.000')
                                  ),
                                  (FrameTime(25, -1000),
                                   FrameTime.InitFrames(25, -25),
                                   FrameTime.InitTimeStr(25, '-0:00:01.000')
                                  )])
def test_eq(same):
    for lhs, rhs in itertools.permutations(same, 2):
        assert lhs == lhs
        assert rhs == rhs
        assert lhs == rhs
        assert lhs >= rhs
        assert lhs <= rhs
        assert rhs >= lhs
        assert rhs <= lhs


@pytest.mark.parametrize('lhs_higher_than_rhs',
                         [(FrameTime(25, 50),
                             FrameTime(25, 49)),
                          (FrameTime(25, -50),
                              FrameTime(25, -51)),
                          (FrameTime.InitFrames(25, 50),
                              FrameTime.InitFrames(25, 49)),
                          (FrameTime.InitFrames(25, -50),
                              FrameTime.InitFrames(25, -51)),
                          (FrameTime.InitTimeStr(25, '0:00:00.001'),
                              FrameTime.InitTimeStr(25, '0:00:00.000')),
                          (FrameTime.InitTimeStr(25, '0:00:00.000'),
                              FrameTime.InitTimeStr(25, '-0:00:00.001'))])
def test_compare(lhs_higher_than_rhs):
    lhs, rhs = lhs_higher_than_rhs
    assert lhs > rhs
    assert lhs >= rhs
    assert not lhs < rhs
    assert not lhs <= rhs

    assert rhs < lhs
    assert rhs <= lhs
    assert not rhs > lhs
    assert not rhs >= lhs

    assert rhs != lhs
    assert not rhs == lhs


@pytest.mark.parametrize('secs', gen_operands())
def test_add(secs):
    lhs, rhs = secs
    check = FrameTime(25, lhs) + FrameTime(25, rhs)

    expected = lhs + rhs
    assert check.fps == 25
    assert check.ms == expected
    assert check.frame == ms2f(expected, check.fps)


@pytest.mark.parametrize('secs', gen_operands())
def test_sub(secs):
    lhs, rhs = secs
    check = FrameTime(25, lhs) - FrameTime(25, rhs)

    expected = lhs - rhs
    assert check.fps == 25
    assert check.ms == expected
    assert check.frame == ms2f(expected, check.fps)


@pytest.mark.parametrize('mul', [0, 1, 2, -1])
def test_mul(mul):
    ms = 10
    expected = ms * mul
    assert FrameTime(25, ms) * mul == FrameTime(25, expected)

    ms = -10
    expected = ms * mul
    assert FrameTime(25, ms) * mul == FrameTime(25, expected)


def test_str():
    assert "t: 2:02:02.200; f: 183055" == str(FrameTime.InitTimeStr(25, "2:02:02.200"))
    assert "t: -2:02:02.200; f: -183055" == str(FrameTime.InitTimeStr(25, "-2:02:02.200"))
    assert "t: -0:00:01.000; f: -25" == str(FrameTime(25, -1000))


def test_change_fps_time_origin():
    ft = FrameTime(25, 1000)
    assert ft.fps == 25
    assert ft.frame == 25
    assert ft.ms == 1000

    ft.fps = 31
    assert ft.fps == 31
    assert ft.frame == 31
    assert ft.ms == 1000


def test_change_fps_frame_origin():
    ft = FrameTime.InitFrames(25, 25)
    assert ft.fps == 25
    assert ft.frame == 25
    assert ft.ms == 1000

    ft.fps = 31
    assert ft.fps == 31
    assert ft.frame == 25
    assert ft.ms == f2ms(25, 31)


@pytest.mark.parametrize('bad_fps', [0, -1])
def test_change_fps_nook(bad_fps):
    ft = FrameTime.InitTimeStr(25, "0:00:01")
    with pytest.raises(ValueError):
        ft.fps = bad_fps
    assert ft.fps == 25
