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

from subconvert.parsing.FrameTime import FrameTime

from subconvert.apprunner import _

def gen_operands():
    lhs = [100, -100]
    rhs = [100, -100, 200, -200]
    return itertools.product(lhs, rhs)

def test_init_incorrect_fps():
    with pytest.raises(ValueError):
        FrameTime(0, frames=5)

    with pytest.raises(ValueError):
        FrameTime(0, frames=-5)


def test_default_frametimw():
    ft = FrameTime(5)
    assert ft.fps == 5
    assert ft.frame == 0
    assert ft.fullSeconds == 0
    assert ft.time['hours'] == 0
    assert ft.time['minutes'] == 0
    assert ft.time['seconds'] == 0
    assert ft.time['miliseconds'] == 0


def test_init_surplus_parameters():
    with pytest.raises(AttributeError):
        FrameTime(5, frames=5, seconds=10)

    with pytest.raises(AttributeError):
        FrameTime(5, frames=5, time="1:01:01.000", seconds=10)


def test_time_dict():
    # 1h 1m 1s 101ms
    ft = FrameTime(25, seconds=3661.101)

    expected = dict(hours=1, minutes=1, seconds=1, miliseconds=101)
    assert ft.time == expected


@pytest.mark.parametrize('param_pair', [(3661.101, '1:01:01.101'),
                                        (3661.101, '+1:01:01.101'),
                                        (-3661.101, '-1:01:01.101')])
def test_init_time_string(param_pair):
    full_secs, timestr = param_pair
    ft = FrameTime(25, time=timestr)
    assert ft.fps == 25
    assert ft.fullSeconds == full_secs
    assert ft.frame == round(full_secs * ft.fps)

@pytest.mark.parametrize('param', [3661.100, 3661.01, 3661.001,
                                   -3661.100, -3661.01, -3661.001])
def test_init_full_seconds(param):
    ft = FrameTime(25, seconds=param)
    assert ft.fps == 25
    assert ft.fullSeconds == param
    assert ft.frame == round(ft.fullSeconds * ft.fps)

@pytest.mark.parametrize('param', [100, 40120, -100, -40120])
def test_init_frames(param):
    ft = FrameTime(25, frames=param)
    assert ft.fps == 25
    assert ft.frame == param
    assert ft.fullSeconds == param / ft.fps


def test_incorrectly_formatted_time():
    with pytest.raises(ValueError):
        FrameTime(25, time="1:12;44-999")

@pytest.mark.parametrize('kw', [{'frames': 50}, {'frames': -50},
                                {'seconds': 50.123}, {'seconds': -50.123},
                                {'time': '1:01:01.123'},
                                {'time': '+1:01:01.123'},
                                {'time': '-1:01:01.123'}])
def test_eq(kw):
    assert FrameTime(25, **kw) == FrameTime(25, **kw)
    assert FrameTime(25, **kw) >= FrameTime(25, **kw)
    assert FrameTime(25, **kw) <= FrameTime(25, **kw)


@pytest.mark.parametrize('kws', [({'frames': 50}, {'frames': 49}),
                                 ({'frames': -50}, {'frames': -51}),
                                 ({'seconds': 50}, {'seconds': 49.999}),
                                 ({'seconds': -50}, {'seconds': -50.001}),
                                 ({'time': '0:00:00.001'}, {'time': '0:00:00.000'}),
                                 ({'time': '0:00:00.000'}, {'time': '-0:00:00.001'})])
def test_compare(kws):
    lhs, rhs = kws
    assert FrameTime(25, **lhs) > FrameTime(25, **rhs)
    assert FrameTime(25, **lhs) >= FrameTime(25, **rhs)
    assert not FrameTime(25, **lhs) < FrameTime(25, **rhs)
    assert not FrameTime(25, **lhs) <= FrameTime(25, **rhs)

    assert FrameTime(25, **rhs) < FrameTime(25, **lhs)
    assert FrameTime(25, **rhs) <= FrameTime(25, **lhs)
    assert not FrameTime(25, **rhs) > FrameTime(25, **lhs)
    assert not FrameTime(25, **rhs) >= FrameTime(25, **lhs)

    assert FrameTime(25, **rhs) != FrameTime(25, **lhs)
    assert not FrameTime(25, **rhs) == FrameTime(25, **lhs)


@pytest.mark.parametrize('secs', gen_operands())
def test_add(secs):
    lhs, rhs = secs
    check = FrameTime(25, seconds=lhs) + FrameTime(25, seconds=rhs)

    expected = lhs + rhs
    assert check.fps == 25
    assert check.fullSeconds == expected
    assert check.frame == expected * check.fps


@pytest.mark.parametrize('secs', gen_operands())
def test_sub(secs):
    lhs, rhs = secs
    check = FrameTime(25, seconds=lhs) - FrameTime(25, seconds=rhs)

    expected = lhs - rhs
    assert check.fps == 25
    assert check.fullSeconds == expected
    assert check.frame == expected * check.fps


@pytest.mark.parametrize('mul', [0, 1, 2, -1])
def test_mul(mul):
    secs = 10
    expected = secs * mul
    assert FrameTime(25, seconds=secs) * mul == FrameTime(25, seconds=expected)

    secs = -10
    expected = secs * mul
    assert FrameTime(25, seconds=secs) * mul == FrameTime(25, seconds=expected)


def test_str():
    assert "t: 2:02:02.200; f: 183055" == str(FrameTime(25, time="2:02:02.200"))
    assert "t: -2:02:02.200; f: -183055" == str(FrameTime(25, time="-2:02:02.200"))
    assert "t: -0:00:01.000; f: -25" == str(FrameTime(25, seconds=-1))


def test_change_fps():
    ft = FrameTime(25, time='0:00:01')
    assert ft.frame == 25
    ft.fps = 31
    assert ft.frame == 31


@pytest.mark.parametrize('bad_fps', [0, -1])
def test_change_fps_nook(bad_fps):
    ft = FrameTime(25, time="0:00:01")
    with pytest.raises(ValueError):
        ft.fps = bad_fps
    assert ft.fps == 25

