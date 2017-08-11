#-*- coding: utf-8 -*-

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

import re
import collections

from subconvert.parsing.Offset import SyncPoint
from subconvert.parsing.FrameTime import FrameTime
from subconvert.utils.SubException import SubException, SubAssert
from subconvert.utils.Locale import _

_Time = collections.namedtuple('Time', ['sign', 'h', 'm', 's', 'ms'])

class _Request:
    class Type:
        OFFSET = 1
        SYNC = 2

    def __init__(self):
        self.type_ = None
        self.sub_no = None
        self.time = None
        self.sign = None

    def to_frametime(self, fps):
        ts = self.time
        secs = 3600 * ts.h + 60 * ts.m + ts.s + float(ts.ms)/1000
        sign = self.time.sign if self.time.sign else 1
        return FrameTime(fps, seconds=secs * sign)


def _tokenize_time(timestr):
    timestr = re.sub(r'\s+', '', timestr)
    SubAssert(timestr, _('Sync: time spec cannot be empty'))

    time_args = dict(sign=None, h=0, m=0, s=0, ms=0)

    if timestr[0] in '+-':
        time_args['sign'] = int('%s1' % timestr[0])
        timestr = timestr[1:]

    found_units = set()

    expr = re.compile(r'''(?P<value>\d+)(?P<unit>[a-zA-Z]+)''')
    parsed_len = 0
    for elem in expr.finditer(timestr):
        val = elem.group('value')
        unit  = elem.group('unit')
        SubAssert(unit not in found_units,
                  _('Sync: non-unique time units in time spec'))
        found_units.add(unit)
        time_args[unit] = int(val)
        parsed_len += (len(unit) + len(val))

    SubAssert(parsed_len == len(timestr),
              _('Sync: some characters not parsed'))

    try:
        return _Time(**time_args)
    except TypeError:
        raise SubException(_('Sync: incorrect time spec units'))

def _tokenize_offset(offset):
    offset = offset.strip()

    req = _Request()
    req.type_ = _Request.Type.OFFSET
    req.time = _tokenize_time(offset)
    SubAssert(req.time.sign,
              _('Sync: offset must be relative. Did you forget a +/- sign?'))
    return req


def _tokenize_sync(sub_no, sync):
    sub_no = sub_no.strip()
    sync = sync.strip()

    SubAssert(sub_no, _('Sync: expected subtitle number'))
    SubAssert(sync, _('Sync: expected time spec'))

    try:
        sub_no = int(sub_no)
    except ValueError:
        raise SubException(_('Sync: incorrect subtitle number: %s' % sub_no))
    SubAssert(sub_no != 0, _('Sync: incorrect subtitle number: %s' % sub_no))

    req = _Request()
    req.type_ = _Request.Type.SYNC
    req.sub_no = sub_no if sub_no < 0 else sub_no - 1
    req.time = _tokenize_time(sync)
    return req


def _tokenize_request(s):
    requests = []
    for req in s.split(','):
        req = req.strip()
        if not req:
            continue

        left, sep, remainder = req.partition(':')

        if not sep:
            requests.append(_tokenize_offset(left))
        else:
            requests.append(_tokenize_sync(left, remainder))
    return requests


def _abs_index(index, list_len):
    if index >= 0:
        return index
    return list_len + index

def _offset_subtitles(req, subs):
    points = []
    ft = req.to_frametime(subs[0].fps)

    for i, sub in enumerate(subs):
        sp = SyncPoint(i, sub.start + ft, sub.end + ft)
        SubAssert(sp.start.fullSeconds >= 0 and sp.end.fullSeconds >= 0,
                  _('Sync: incorrect offset. '
                    'Resulting subtitle time would be lower than 0'))
        points.append(sp)
    return points


def _sync_subtitles(requests, subs):
    points = []
    for req in requests:
        SubAssert(req.type_ == _Request.Type.SYNC,
                  _('Sync: expected sync request'))

        abs_sub_no = _abs_index(req.sub_no, len(subs))
        SubAssert(abs_sub_no >= 0 and abs_sub_no < len(subs),
                  _('Sync: incorrect subtitle number: %d' % req.sub_no))

        sub = subs[abs_sub_no]
        ft = req.to_frametime(sub.fps)

        sp = None
        if req.time.sign is not None:
            sp = SyncPoint(abs_sub_no, sub.start + ft, sub.end + ft)
            SubAssert(sp.start.fullSeconds >= 0 and sp.end.fullSeconds >= 0,
                      _('Sync: incorrect time spec. '
                        'Resulting subtitle time would be lower than 0'))
        else:
            delta = sub.end - sub.start
            sp = SyncPoint(abs_sub_no, ft, ft + delta)
        points.append(sp)
    return points


def parse(s, subs):
    """Parses a given string and creates a list of SyncPoints."""
    if len(subs) == 0:
        return []

    points = []
    requests = _tokenize_request(s)

    if len(requests) == 1 and requests[0].type_ == _Request.Type.OFFSET:
        return _offset_subtitles(requests[0], subs)
    return _sync_subtitles(requests, subs)
