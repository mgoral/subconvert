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
import os
import re

from subconvert.parsing.FrameTime import FrameTime
from subconvert.parsing.Core import Subtitle
from subconvert.utils.SubException import SubAssert
from subconvert.utils.Locale import _

class TimeFormat:
    UNKNOWN = 0
    FRAME = 1
    TIME = 2

class SubFormat:
    """A general description of subtitle format. Should be specialized for each format."""
    NAME = 'Generic'
    EXTENSION = 'sub'
    TIMEFORMAT = TimeFormat.UNKNOWN
    OPT = None
    WITH_HEADER = False

    def __init__(self, subFormat, subPattern = "", endPattern = "", formatting = None):
        """
        Init SubFormat. It should be called by derived class at the beginning of its __init__().
        Bad things could happen otherwise.

        @param subFormat:  subtitle template that describes how subtitle in a given format looks
                           like (when converting parsed subtitles). Might contain following tags:
                           {gsp_no} - subtitle number;
                           {gsp_from}, {gsp_to} - subtitle start and end times;
                           {gsp_text} - subtitle text.
                           Don't forget to escape curly braces when needed.
                           Example: {gsp_no}: [{gsp_from} {gsp_to}] {gsp_text}
        @param subPattern: regular expression describing single subtitle section. Might be verbose
                           (i.e. re.X is enabled). Should contain following named groups:
                           'time_from', 'time_to' and 'text'. If subPatter doesn't meet above
                           requirements or specific format is matched some other way,
                           'createSubtitle' method should be specialized in a derived class.
                           Default: ""
        @param endPattern: regular expression describing single subtitle section ending
                           mark/pattern. It should match an ending pattern in a group (i.e. it
                           should be placed inside parentheses).
                           Regex is a default way to describe ending pattern but if it's not
                           sufficent, 'subtitleEnds' method should be specialized in a derived
                           class.
                           Default: ""
        @param formatting: GSP formatting description. It describes dependencies between general
                           (SubConvert specific) formatting tags (GSP) and specific ones used by a
                           concrete format. Supported tags:
                           {gsp_b}, {_gsp_b} - bold;
                           {gsp_i}, {_gsp_i} - italics;
                           {gsp_u}, {_gsp_u} - underline;
                           {gsp_nl} - newline.
                           By default only {gsp_nl} is provided and equal to os-specific line
                           separator.
        """

        self._subFormat = subFormat
        self._endPattern = re.compile(endPattern, re.X)
        self._pattern = re.compile(subPattern, re.X)

        if formatting is not None:
            self._formatting = formatting
        else:
            self._formatting = {
                'gsp_b_':   r'', '_gsp_b':  r'',
                'gsp_i_':   r'', '_gsp_i':  r'',
                'gsp_u_':   r'', '_gsp_u':  r'',
                'gsp_nl':   os.linesep,
            }

    def __hash__(self):
        return self.NAME.__hash__()

    def _formatLinesep(self, string):
        if self.formatting["gsp_nl"]:
            if self.formatting["gsp_nl"] == os.linesep:
                if "\r\n" in string:
                    string = string.replace("\r\n", "{gsp_nl}")
                elif "\n" in string:
                    string = string.replace("\n", "{gsp_nl}")
                elif "\r" in string:
                    string = string.replace("\r", "{gsp_nl}")
            else:
                string = string.replace(self.formatting["gsp_nl"], "{gsp_nl}")
        return string

    def _formatWithTags(self, openTag, closeTag, string):
        if self.formatting[openTag]:
            fullOpenTag = ''.join(['{', openTag, '}'])
            openFormatTag = self.formatting[openTag].replace('{', '{{').replace('}', '}}')
            string = string.replace(openFormatTag, fullOpenTag)

        if self.formatting[closeTag]:
            fullCloseTag = ''.join(['{', closeTag, '}'])
            closeFormatTag = self.formatting[closeTag].replace('{', '{{').replace('}', '}}')
            string = string.replace(closeFormatTag, fullCloseTag)
        return string

    #
    # Parsing subtitle format.
    #

    def subtitleEnds(self, content):
        """Returns whether a given 'content' is an ending mark/pattern for a single subtitle (e.g.
        is double newline for SubRip, a single newline for MicroDVD, etc.).
        By default 'content' is checked against 'endPattern' regular expression."""
        return self._endPattern.search(content) is not None

    def createSubtitle(self, fps, section):
        """Returns a correct 'Subtitle' object from a text given in 'section'. If 'section' cannot
        be parsed, None is returned.
        By default 'section' is checked against 'subPattern' regular expression."""
        matched = self._pattern.search(section)
        if matched is not None:
            matchedDict = matched.groupdict()
            return Subtitle(
                self.frametime(fps, matchedDict.get("time_from")),
                self.frametime(fps, matchedDict.get("time_to")),
                self.formatSub(matchedDict.get("text"))
            )
        return None

    def addHeaderInfo(self, content, header):
        """Try to find header in a given subSection. Return True if header was parsed, False
        otherwise.  Header parsing results should be saved to the 'header' (which is passed by
        reference).  After it returns True, it will not be called again."""
        return True

    def frametime(self, fps, string):
        """Convert 'string' to a FrameTime objects. 'string' is a format specific time
        description."""
        return FrameTime(fps, 0)

    def formatSub(self, string):
        """Convert sub-type specific formatting to GSP formatting.
        By default formatSub will replace 1-to-1 all occurences of subtitle specific tags with
        their GSP equivalents. Due to performance reasons it will not parse given 'string' in any
        other way. That means that it cannot detect exotic situations like existance of opening tags
        only. This generic behaviour is good enough for most formats but in some cases it'll be
        necessary to provide a specialized version of this method.
        If 'gsp_nl' equals to os.linesep, then a given string will be checked against occurance of
        any of newline styles (Linux, Windows and Mac).
        Trivia: GSP stands for "GenericSubParser" which was SubParser class name before."""
        string = string.strip()
        string = string.replace('{', '{{').replace('}', '}}')
        string = self._formatWithTags("gsp_b_", "_gsp_b", string)
        string = self._formatWithTags("gsp_i_", "_gsp_i", string)
        string = self._formatWithTags("gsp_u_", "_gsp_u", string)
        string = self._formatLinesep(string)
        return string

    #
    # Converting to subtitle format from parsed content.
    #

    def convertHeader(self, header):
        """Convert a given Header object to format specific string that can be saved to file."""
        return None

    def convertTime(self, frametime, which):
        """Convert FrameTime object to properly formatted string that describes subtitle start or
        end time."""
        SubAssert(frametime.frame >= 0, _("Negative time present."))
        return frametime.frame

    @property
    def formatting(self):
        """Returns SubConvert GSP formatting dictionary. It describes dependencies between general
        formatting tags used by SubConvert and specific ones used by a concrete format. See
        self._formatting for a list o available GSP tags (their names should be
        self-explainatory)."""
        return self._formatting

    @property
    def subFormatTemplate(self):
        """Return a subtitle template which might contain the following tags: {gsp_no}, {gsp_from},
        {gsp_to} and {gsp_text}. Don't forget to escape curly braces ('{' and '}') when needed."""
        return self._subFormat

class MicroDVD(SubFormat):
    NAME = 'Micro DVD'
    OPT = 'microdvd'
    TIMEFORMAT = 'frame'
    EXTENSION = 'sub'

    def __init__(self):
        pattern = r'''
            ^
            \{(?P<time_from>\d+)\}  # {digits}
            \{(?P<time_to>\d+)\}    # {digits}
            (?P<text>[^\r\n]*)
            '''
        endPattern = r'(?P<end>(?:\r?\n)|(?:\r))$' # \r on mac, \n on linux, \r\n on windows
        subFormat = "{{{gsp_from}}}{{{gsp_to}}}{gsp_text}%s" % os.linesep
        formatting = {
            'gsp_b_':   r'{y:b}', '_gsp_b':     r'',
            'gsp_i_':   r'{y:i}', '_gsp_i':     r'',
            'gsp_u_':   r'{y:u}', '_gsp_u':     r'',
            'gsp_nl':   r'|',
        }
        super().__init__(subFormat, pattern, endPattern, formatting)

    def frametime(self, fps, string):
        return FrameTime(fps, frames=string)

    def formatSub(self, string):
        string = string.replace('{', '{{').replace('}', '}}')
        lines = string.split('|')
        for i, line in enumerate(lines):
            if '{{y:b}}' in line:
                line = line.replace('{{y:b}}', '{gsp_b_}')
                line = ''.join([line, '{_gsp_b}'])
            if '{{y:i}}' in line:
                line = line.replace('{{y:i}}', '{gsp_i_}')
                line = ''.join([line, '{_gsp_i}'])
            if '{{y:u}}' in line:
                line = line.replace('{{y:u}}', '{gsp_u_}')
                line = ''.join([line, '{_gsp_u}'])
            lines[i] = line
        string = '{gsp_nl}'.join(lines)
        return string

    def convertTime(self, frametime, which):
        SubAssert(frametime.frame >= 0, _("Negative time present."))
        return frametime.frame

class SubRip(SubFormat):
    NAME = 'Sub Rip'
    OPT = 'subrip'
    TIMEFORMAT = 'time'
    EXTENSION = 'srt'

    def __init__(self):
        pattern = r'''
        ^
        \d+\s+
        (?P<time_from>\d+:\d{2}:\d{2},\d+)  # 00:00:00,000
        [ \t]*-->[ \t]*
        (?P<time_to>\d+:\d{2}:\d{2},\d+)
        \s*
        (?P<text>[^\f\v\b]+)
        '''
        subFormat = "{gsp_no}%s{gsp_from} --> {gsp_to}%s{gsp_text}%s%s" % ( os.linesep, os.linesep, os.linesep, os.linesep)
        endPattern = r'^(?P<end>(?:\r?\n)|(?:\r))$'    # \r\n on windows, \r on mac
        formatting = {
            'gsp_b_':   r'<b>', '_gsp_b':   r'</b>',
            'gsp_i_':   r'<i>', '_gsp_i':   r'</i>',
            'gsp_u_':   r'<u>', '_gsp_u':   r'</u>',
            'gsp_nl':   os.linesep,
        }
        super().__init__(subFormat, pattern, endPattern, formatting)

        self.time_fmt = re.compile(
            r'^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2}),(?P<ms>\d+)$'
        )

    def frametime(self, fps, string):
        time = self.time_fmt.search(string)
        return FrameTime(fps, time = "%d:%02d:%02d.%03d" % \
            (int(time.group('h')), int(time.group('m')), int(time.group('s')), int(time.group('ms'))))

    def convertTime(self, frametime, which):
        SubAssert(frametime.fullSeconds >= 0, _("Negative time present."))
        t = frametime.time
        return '%02d:%02d:%02d,%03d' % (t['hours'], t['minutes'], t['seconds'],
                                        t['miliseconds'])

class SubViewer(SubFormat):
    NAME = 'SubViewer 1.0'
    OPT = 'subviewer'
    TIMEFORMAT = 'time'
    EXTENSION = 'sub'
    WITH_HEADER = True

    def __init__(self):
        pattern = r'''
            ^
            (?P<time_from>\d{2}:\d{2}:\d{2}.\d{2})
            ,
            (?P<time_to>\d{2}:\d{2}:\d{2}.\d{2})
            [\r\n]{1,2}     # linebreaks on different os's
            (?P<text>[^\f\v\b]+)
            '''
        endPattern = r'^(?P<end>(?:\r?\n)|(?:\r))$'    # \r\n on windows, \r on mac
        subFormat = "{gsp_from},{gsp_to}%s{gsp_text}%s%s" % (os.linesep, os.linesep, os.linesep)
        super().__init__(subFormat, pattern, endPattern)

        self.time_fmt = re.compile(
            r'^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2}).(?P<ms>\d+)$'
        )

    def frametime(self, fps, string):
        time = self.time_fmt.search(string)
        return FrameTime(fps, time = "%d:%02d:%02d.%03d" % \
            (int(time.group('h')), int(time.group('m')), int(time.group('s')), int(time.group('ms'))*10))

    def convertTime(self, frametime, which):
        SubAssert(frametime.fullSeconds >= 0, _("Negative time present."))
        t = frametime.time
        ms = int(round(t['miliseconds'] / float(10)))
        return '%02d:%02d:%02d.%02d' % (t['hours'], t['minutes'], t['seconds'], ms)

    def addHeaderInfo(self, content, header):
        if( '[colf]' in content.lower() and '[information]' in content.lower()):
            end = content.lower().find('[end information]')
            if -1 == end:
                end = content.lower().find('[subtitle]')
                if -1 == end:
                    return True

            header.registerAlias("prg", "program")
            tag_list = content[:end].splitlines()
            for tag in tag_list:
                if tag.strip().startswith('['):
                    parse_result = tag.strip()[1:].partition(']')
                    if parse_result[2]:
                        header.add(parse_result[0].replace(' ', '_').lower(), parse_result[2])
            tag_list = content[end:].split(',')
            for tag in tag_list:
                parse_result = tag.strip()[1:].partition(']')
                if parse_result[2]:
                    if parse_result[0].lower() == 'color':
                        header.add('color', parse_result[2])
                    elif parse_result[0].lower() == 'style':
                        header.add('font_style', parse_result[2])
                    elif parse_result[0].lower() == 'size':
                        header.add('font_size', parse_result[2])
                    elif parse_result[0].lower() == 'font':
                        header.add('font', parse_result[2])
            return True
        else:
            return False

    def convertHeader(self, header):
        title = header.get('title', '')
        author = header.get('author', '')
        source = header.get('source', '')
        program = header.get('program', 'SubConvert')
        filepath = header.get('filepath', '')
        delay = header.get('delay', '0')
        cd_track = header.get('cd_track', '0')
        comment = header.get('comment', 'Converted to subviewer format with SubConvert')
        color = header.get('color', '&HFFFFFF')
        font_style = header.get('font_style', 'no')
        font_size = header.get('font_size', '24')
        font = header.get('font', 'Tahoma')
        return os.linesep.join([ \
            '[INFORMATION]', '[TITLE]%s' % title, '[AUTHOR]%s' % author, \
            '[SOURCE]%s' % source, '[PRG]%s' % program, '[FILEPATH]%s' % filepath, \
            '[DELAY]%s' % delay, '[CD TRACK]%s' % cd_track, '[COMMENT]%s' % comment, \
            '[END INFORMATION]', '[SUBTITLE]',
            '[COLF]%s,[STYLE]%s,[SIZE]%s,[FONT]%s%s' % \
            (color, font_style, font_size, font, os.linesep)])

class TMP(SubFormat):
    NAME = 'TMP'
    OPT = 'tmp'
    TIMEFORMAT = 'time'
    EXTENSION = 'txt'

    def __init__(self):
        pattern = r'''
        ^
        (?P<time_from>\d+:\d{2}:\d{2})
        :
        (?P<text>[^\r\n]+)
        '''
        endPattern = r'(?P<end>(?:\r?\n)|(?:\r))$' # \r on mac, \n on linux, \r\n on windows
        subFormat = "{gsp_from}:{gsp_text}%s" % os.linesep
        formatting = {
            'gsp_b_':   r'', '_gsp_b':      r'',
            'gsp_i_':   r'', '_gsp_i':      r'',
            'gsp_u_':   r'', '_gsp_u':      r'',
            'gsp_nl':   r'|',
        }
        super().__init__(subFormat, pattern, endPattern, formatting)

        self.time_fmt = re.compile(
            r'^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2})$'
        )

    def frametime(self, fps, string):
        if string:
            time = self.time_fmt.search(string)
            return FrameTime(fps, time = "%d:%02d:%02d" % \
                (int(time.group('h')), int(time.group('m')), int(time.group('s'))))
        return None

    def convertTime(self, frametime, which):
        if which == 'time_from':
            SubAssert(frametime.fullSeconds >= 0, _("Negative time present."))
            t = frametime.time
            return '%02d:%02d:%02d' % (t['hours'], t['minutes'], t['seconds'])

class MPL2(SubFormat):
    NAME = 'MPL2'
    OPT = 'mpl2'
    TIMEFORMAT = 'time'
    EXTENSION = 'txt'

    def __init__(self):
        pattern = r'''
            ^
            \[(?P<time_from>\d+)\]  # {digits}
            \[(?P<time_to>\d+)\]    # {digits}
            (?P<text>[^\r\n]*)
            '''
        endPattern = r'(?P<end>(?:\r?\n)|(?:\r))$' # \r on mac, \n on linux, \r\n on windows
        subFormat = "[{gsp_from}][{gsp_to}]{gsp_text}%s" % os.linesep
        formatting = { # Once I had subs with <i> but I haven't found any official note about it
            'gsp_b_':   r'', '_gsp_b':     r'',
            'gsp_i_':   r'/', '_gsp_i':     r'',
            'gsp_u_':   r'', '_gsp_u':     r'',
            'gsp_nl':   r'|',
        }
        super().__init__(subFormat, pattern, endPattern, formatting)

    def frametime(self, fps, string):
        string = ''.join(['0', string]) # Parsing "[0][5] sub" would cause an error without this
        ms = int(string[-1]) / 10.0
        seconds = int(string[:-1]) + ms
        return FrameTime(fps, seconds=seconds)

    def convertTime(self, frametime, which):
        SubAssert(frametime.fullSeconds >= 0, _("Negative time present."))
        time = str(frametime.fullSeconds).split('.')
        time = ''.join([time[0].lstrip('0'), time[1][0]])
        return time

