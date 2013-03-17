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
import re

from subparser.SubParser import GenericSubParser
from subparser.FrameTime import FrameTime

class MicroDVD(GenericSubParser):
    """See a GenericSubParser for a documentation."""

    __SUB_TYPE__ = 'Micro DVD'
    __OPT__ = 'microdvd'
    __FMT__ = 'frame'
    __EXT__ = 'sub'
    pattern = r'''
        ^
        \{(?P<time_from>\d+)\}  # {digits}
        \{(?P<time_to>\d+)\}    # {digits}
        (?P<text>[^\r\n]*)
        '''
    end_pattern = r'(?P<end>(?:\r?\n)|(?:\r))$' # \r on mac, \n on linux, \r\n on windows
    sub_fmt = "{{{gsp_from}}}{{{gsp_to}}}{gsp_text}%s" % os.linesep # Looks weird but escaping '{}' curly braces requires to double them
    sub_formatting = {
        'gsp_b_':   r'{y:b}', '_gsp_b':     r'',
        'gsp_i_':   r'{y:i}', '_gsp_i':     r'',
        'gsp_u_':   r'{y:u}', '_gsp_u':     r'',
        'gsp_nl':   r'|',
    }

    def __init__(self, filename, fps, lines = None):
        GenericSubParser.__init__(self, filename, fps, lines)

    def str_to_frametime(self, string):
        return FrameTime(fps=self.fps, value_type=self.__FMT__, frame=string)

    def format_text(self, string):
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

    def get_time(self, frametime, which):
        return frametime.frame

class SubRip(GenericSubParser):
    """See a GenericSubParser for a documentation."""

    __SUB_TYPE__ = 'Sub Rip'
    __OPT__ = 'subrip'
    __FMT__ = 'time'
    __EXT__ = 'srt'
    pattern = r'''
    ^
    \d+\s+
    (?P<time_from>\d+:\d{2}:\d{2},\d+)  # 00:00:00,000
    [ \t]*-->[ \t]*
    (?P<time_to>\d+:\d{2}:\d{2},\d+)
    \s*
    (?P<text>[^\f\v\b]+)
    '''
    end_pattern = r'^(?P<end>(?:\r?\n)|(?:\r))$'    # \r\n on windows, \r on mac
    time_fmt = r'^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2}),(?P<ms>\d+)$'
    sub_fmt = "{gsp_no}%s{gsp_from} --> {gsp_to}%s{gsp_text}%s%s" % ( os.linesep, os.linesep, os.linesep, os.linesep)
    sub_formatting = {
        'gsp_b_':   r'<b>', '_gsp_b':   r'</b>',
        'gsp_i_':   r'<i>', '_gsp_i':   r'</i>',
        'gsp_u_':   r'<u>', '_gsp_u':   r'</u>',
        'gsp_nl':   os.linesep,
    }

    def __init__(self, filename, fps, lines = None):
        self.time_fmt = re.compile(self.time_fmt)
        GenericSubParser.__init__(self, filename, fps, lines)

    def str_to_frametime(self, string):
        time = self.time_fmt.search(string)
        return FrameTime(fps=self.fps, value_type=self.__FMT__, \
            h=time.group('h'), m=time.group('m'), \
            s=time.group('s'), ms=time.group('ms'))

    def format_text(self, string):
        string = string.strip()
        string = string.replace('{', '{{').replace('}', '}}')
        if r'<b>' in string:
            string = string.replace(r'<b>', '{gsp_b_}')
            string = string.replace(r'</b>', '{_gsp_b}')
        if r'<u>' in string:
            string = string.replace(r'<u>', '{gsp_u_}')
            string = string.replace(r'</u>', '{_gsp_u}')
        if r'<i>' in string:
            string = string.replace(r'<i>', '{gsp_i_}')
            string = string.replace(r'</i>', '{_gsp_i}')
        if '\r\n' in string:
            string = string.replace('\r\n', '{gsp_nl}')   # Windows
        elif '\n' in string:
            string = string.replace('\n', '{gsp_nl}') # Linux
        elif '\r' in string:
            string = string.replace('\r', '{gsp_nl}') # Mac
        return string

    def get_time(self, frametime, which):
        return '%02d:%02d:%02d,%03d' % (int(frametime.hours), int(frametime.minutes), int(frametime.seconds), int(frametime.miliseconds))

class SubViewer(GenericSubParser):
    """See a GenericSubParser for a documentation."""

    __SUB_TYPE__ = 'SubViewer 1.0'
    __OPT__ = 'subviewer'
    __FMT__ = 'time'
    __EXT__ = 'sub'
    __WITH_HEADER__ = True
    pattern = r'''
        ^
        (?P<time_from>\d{2}:\d{2}:\d{2}.\d{2})
        ,
        (?P<time_to>\d{2}:\d{2}:\d{2}.\d{2})
        [\r\n]{1,2}     # linebreaks on different os's
        (?P<text>[^\f\v\b]+)
        '''
    end_pattern = r'^(?P<end>(?:\r?\n)|(?:\r))$'    # \r\n on windows, \r on mac
    time_fmt = r'^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2}).(?P<ms>\d+)$'
    sub_fmt = "{gsp_from},{gsp_to}%s{gsp_text}%s%s" % (os.linesep, os.linesep, os.linesep)
    sub_formatting = {
        'gsp_b_':   r'', '_gsp_b':  r'',
        'gsp_i_':   r'', '_gsp_i':  r'',
        'gsp_u_':   r'', '_gsp_u':  r'',
        'gsp_nl':   os.linesep,
    }

    def __init__(self, filename, fps, lines = None):
        self.time_fmt = re.compile(self.time_fmt)
        GenericSubParser.__init__(self, filename, fps, lines)

    def str_to_frametime(self, string):
        time = self.time_fmt.search(string)
        return FrameTime(fps=self.fps, value_type=self.__FMT__, \
            h=time.group('h'), m=time.group('m'), \
            s=time.group('s'), ms=int(time.group('ms'))*10)

    def format_text(self, string):
        string = string.strip()
        string = string.replace('{', '{{').replace('}', '}}')
        if '\r\n' in string:
            string = string.replace('\r\n', '{gsp_nl}')   # Windows
        elif '\n' in string:
            string = string.replace('\n', '{gsp_nl}') # Linux
        elif '\r' in string:
            string = string.replace('\r', '{gsp_nl}') # Mac
        return string

    def get_time(self, frametime, which):
        ms = int(round(frametime.miliseconds / float(10)))
        return '%02d:%02d:%02d.%02d' % (int(frametime.hours), int(frametime.minutes), int(frametime.seconds), ms)

    def get_header(self, header, atom):
        if( '[colf]' in header.lower() and '[information]' in header.lower()):
            atom['header'] = {}
            end = header.lower().find('[end information]')
            if -1 == end:
                end = header.lower().find('[subtitle]')
                if -1 == end:
                    return True

            tag_list = header[:end].splitlines()
            for tag in tag_list:
                if tag.strip().startswith('['):
                    parse_result = tag.strip()[1:].partition(']')
                    if parse_result[2]:
                        if parse_result[0].lower() == 'prg':
                            atom['header']['program'] = parse_result[2]
                        else:
                            atom['header'][parse_result[0].replace(' ', '_').lower()] = parse_result[2]
            tag_list = header[end:].split(',')
            for tag in tag_list:
                parse_result = tag.strip()[1:].partition(']')
                if parse_result[2]:
                    if parse_result[0].lower() == 'color':
                        atom['header']['color'] = parse_result[2]
                    elif parse_result[0].lower() == 'style':
                        atom['header']['font_style'] = parse_result[2]
                    elif parse_result[0].lower() == 'size':
                        atom['header']['font_size'] = parse_result[2]
                    elif parse_result[0].lower() == 'font':
                        atom['header']['font'] = parse_result[2]
            return True
        else:
            return False

    def convert_header(self, header):
        keys = header.keys()
        filename = os.path.split(self.filename)[-1]
        title = header.get('title') if 'title' in keys else os.path.splitext(filename)[0]
        author = header.get('author') if 'author' in keys else ''
        source = header.get('source') if 'source' in keys else ''
        program = header.get('program') if 'program' in keys else 'SubConvert'
        filepath = header.get('filepath') if 'filepath' in keys else self.filename
        delay = header.get('delay') if 'delay' in keys else '0'
        cd_track = header.get('cd_track') if 'cd_track' in keys else '0'
        comment = header.get('comment') if 'comment' in keys else 'Converted to subviewer format with SubConvert'
        color = header.get('color') if 'color' in keys else '&HFFFFFF'
        font_style = header.get('font_style') if 'font_style' in keys else 'no'
        font_size = header.get('font_size') if 'font_size' in keys else '24'
        font = header.get('font') if 'font' in keys else 'Tahoma'
        return os.linesep.join([ \
            '[INFORMATION]', '[TITLE]%s' % title, '[AUTHOR]%s' % author, \
            '[SOURCE]%s' % source, '[PRG]%s' % program, '[FILEPATH]%s' % filepath, \
            '[DELAY]%s' % delay, '[CD TRACK]%s' % cd_track, '[COMMENT]%s' % comment, \
            '[END INFORMATION]', '[SUBTITLE]',
            '[COLF]%s,[STYLE]%s,[SIZE]%s,[FONT]%s%s' % \
            (color, font_style, font_size, font, os.linesep)])

class TMP(GenericSubParser):
    """See a GenericSubParser for a documentation."""

    __SUB_TYPE__ = 'TMP'
    __OPT__ = 'tmp'
    __FMT__ = 'time'
    __EXT__ = 'txt'
    pattern = r'''
    ^
    (?P<time_from>\d+:\d{2}:\d{2})
    :
    (?P<text>[^\r\n]+)
    '''
    end_pattern = r'(?P<end>(?:\r?\n)|(?:\r))$' # \r on mac, \n on linux, \r\n on windows
    time_fmt = r'^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2})$'
    sub_fmt = "{gsp_from}:{gsp_text}%s" % os.linesep
    sub_formatting = {
        'gsp_b_':   r'', '_gsp_b':      r'',
        'gsp_i_':   r'', '_gsp_i':      r'',
        'gsp_u_':   r'', '_gsp_u':      r'',
        'gsp_nl':   r'|',
    }

    def __init__(self, filename, fps, lines = None):
        self.time_fmt = re.compile(self.time_fmt)
        GenericSubParser.__init__(self, filename, fps, lines)

    def str_to_frametime(self, string):
        time = self.time_fmt.search(string)
        return FrameTime(fps=self.fps, value_type=self.__FMT__, \
            h=time.group('h'), m=time.group('m'), \
            s=time.group('s'), ms=0)

    def format_text(self, string):
        string = string.strip()
        string = string.replace('{', '{{').replace('}', '}}')
        if '|' in string:
            string = string.replace('|', '{gsp_nl}')
        if '\r\n' in string:
            string = string.replace('\r\n', '{gsp_nl}')   # Windows
        elif '\n' in string:
            string = string.replace('\n', '{gsp_nl}') # Linux
        elif '\r' in string:
            string = string.replace('\r', '{gsp_nl}') # Mac
        return string

    def get_time(self, frametime, which):
        if which == 'time_from':
            return '%02d:%02d:%02d' % (int(frametime.hours), int(frametime.minutes), int(frametime.seconds))

class MPL2(GenericSubParser):
    """See a GenericSubParser for a documentation."""

    __SUB_TYPE__ = 'MPL2'
    __OPT__ = 'mpl2'
    __FMT__ = 'time'
    __EXT__ = 'txt'
    pattern = r'''
        ^
        \[(?P<time_from>\d+)\]  # {digits}
        \[(?P<time_to>\d+)\]    # {digits}
        (?P<text>[^\r\n]*)
        '''
    end_pattern = r'(?P<end>(?:\r?\n)|(?:\r))$' # \r on mac, \n on linux, \r\n on windows
    sub_fmt = "[{gsp_from}][{gsp_to}]{gsp_text}%s" % os.linesep # Looks weird but escaping '{}' curly braces requires to double them
    # Once I had subs with <i> but I haven't found any official note about it
    sub_formatting = {
        'gsp_b_':   r'', '_gsp_b':     r'',
        'gsp_i_':   r'/', '_gsp_i':     r'',
        'gsp_u_':   r'', '_gsp_u':     r'',
        'gsp_nl':   r'|',
    }

    def __init__(self, filename, fps, lines = None):
        GenericSubParser.__init__(self, filename, fps, lines)

    def str_to_frametime(self, string):
        string = ''.join(['0', string]) # Parsing "[0][5] sub" would cause an error without this
        ms = int(string[-1]) / 10.0
        seconds = int(string[:-1]) + ms
        return FrameTime(fps=self.fps, value_type='full_seconds', seconds=seconds)

    def format_text(self, string):
        string = string.replace('{', '{{').replace('}', '}}')
        lines = string.split('|')
        for i, line in enumerate(lines):
            if line.startswith('/'):
                line = ''.join(['{gsp_i_}', line[1:], '{_gsp_i}'])
                lines[i] = line
        string = '{gsp_nl}'.join(lines)
        return string

    def get_time(self, frametime, which):
        time = str(frametime.full_seconds).split('.')
        time = ''.join([time[0].lstrip('0'), time[1][0]])
        return time
