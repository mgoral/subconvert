#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
    This file is part of Subconvert.

    Subconvert is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Subconvert is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Subconvert.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import shutil
import re
import codecs
from subprocess import Popen, PIPE
import logging
from optparse import OptionParser, OptionGroup
import gettext
from datetime import datetime

try:
	import chardet
	IS_CHARDET = True
except ImportError:
	IS_CHARDET = False

__VERSION__ = '0.8.1'
__AUTHOR__ = u'Michał Góral'

log = logging.getLogger(__name__)
ch = logging.StreamHandler()

gettext.bindtextdomain('subconvert', '/usr/lib/subconvert/locale')
gettext.textdomain('subconvert')
_ = gettext.gettext

class SubParsingError(Exception):
	pass

class FrameTime:
	def __init__(self, fps, value_type, **kwargs):
		'''Construct and convert value(s) given in kwargs.
		Kwargs should describe either 'frame' or 'h', 'm',
		's' and 'ms'. '''
		if fps >= 0:
			self.fps = float(fps)
		else:
			raise ValueError, _("Incorrect fps argument.")
		if value_type == 'frame':
			self.__set_time__( int(kwargs['frame']) / self.fps)
		elif value_type == 'time':
			if int(kwargs['h']) < 0 or int(kwargs['m']) > 59 or int(kwargs['m']) < 0 \
			or int(kwargs['s']) > 59 or int(kwargs['s']) < 0 or int(kwargs['ms']) > 999 \
			or int(kwargs['ms']) < 0:
				raise ValueError, "Arguments not in allowed ranges."
			self.miliseconds = int(kwargs['ms'])
			self.seconds = int(kwargs['s'])
			self.minutes = int(kwargs['m'])
			self.hours = int(kwargs['h'])
			self.frame = int(round(self.fps * (3600*self.hours + 60*self.minutes + self.seconds + float(self.miliseconds)/1000)))
			self.ss = self.frame / self.fps
		elif value_type == 'ss':
			self.__set_time__( kwargs['seconds'] )
		else:
			raise AttributeError, _("Not supported FrameTime type: '%s'") % value_type
	
	def __set_time__(self, seconds):
		if seconds >= 0:
			self.ss = float(seconds)
			self.frame = int(round(self.ss * self.fps))
		else:
			raise ValueError, _("Incorrect seconds value.")
		tmp = seconds
		seconds = int(seconds)
		self.miliseconds = int((tmp - seconds)*1000)
		self.hours = seconds / 3600
		seconds -= 3600 * self.hours
		self.minutes = seconds / 60
		self.seconds = seconds - 60 * self.minutes
	
	def __set_frame__(self, frame):
		if frame >= 0:
			self.__set_time__(frame / self.fps)
		else:
			raise ValueError, _("Incorrect frame value.")

	def __cmp__(self, other):
		assert(self.fps == other.fps)
		if self.ss < other.ss:
			return -1
		elif self.ss == other.ss:
			return 0
		elif self.ss > other.ss:
			return 1

	def __add__(self, other):
		assert(self.fps == other.fps)
		result = self.ss + other.ss
		return FrameTime(fps = self.fps, value_type = 'ss', seconds = result)
	
	def __sub__(self, other):
		assert(self.fps == other.fps)
		assert(self.ss >= other.ss)
		result = self.ss - other.ss
		return FrameTime(fps = self.fps, value_type = 'ss', seconds = result)
	
	def __mul__(self, n):
		result = self.ss * n
		return FrameTime(fps = self.fps, value_type = 'ss', seconds = result)
	
	def __div__(self, n):
		result = self.ss / n
		return FrameTime(fps = self.fps, value_type = 'ss', seconds = result)
	
	def __str__(self):
		return "t: %s:%s:%s.%s; f: %s" % \
			( self.hours, self.minutes, self.seconds, self.miliseconds, self.frame )

class GenericSubParser(object):
	'''Generic class that should be inherited
	and polymorphed by the other, specialized
	classes. Don't forget to change patterns
	in subclasses.'''

	# Overwrite these in inherited classes
	# Note that start_pattern is checked independently to 
	# time_pattern and text_pattern (which are OR-ed)
	__SUB_TYPE__ = 'Generic'
	__OPT__ = 'none'
	__EXT__ = 'sub'
	__FMT__ = 'Unknown'		# time/frame
	__WITH_HEADER__ = False
	__MAX_HEADER_LEN__ = 50
	end_pattern = r'(?P<end>\r?\n)$'
	pattern = r'(?P<time_from>\d+) (?P<time_to>\d+)(?P<text>.+)'
	sub_fmt = "{gsp_no}:%s{gsp_from} : {gsp_to} %s {gsp_text}%s" % (os.linesep, os.linesep, os.linesep)	# output subtitle format
	sub_formatting = {
		'gsp_b_':	r'', '_gsp_b':	r'',
		'gsp_i_':	r'', '_gsp_i':	r'',
		'gsp_u_':	r'', '_gsp_u':	r'',
		'gsp_nl':	os.linesep,
		}
	
	# Do not overwrite further
	__PARSED__ = False
	__HEADER_FOUND__ = False

	def __init__(self, filename, fps, encoding, lines = []):
		'''Usually you will only need to call super __init__(filename, encoding)
		from a specialized class.'''

		self.atom_t = {'time_from': '', 'time_to': '', 'text': ''}
		self.filename = filename
		self.pattern = re.compile(self.pattern, re.X)
		self.end_pattern = re.compile(self.end_pattern, re.X)
		self.encoding = encoding
		self.lines = lines
		self.fps = fps

	def message(self, line_no, msg = "parsing error."):
		return _("%s:%d %s") % (self.filename, line_no, msg)
	
	def parse(self):
		'''Actual parser.
		Please note that time_to is not required 
		to process as not all subtitles provide it.'''

		atom = self.atom_t.copy()
		i = 0
		line_no = 0
		sub_section = ''
		for line_no, line in enumerate(self.lines):
			if not self.__WITH_HEADER__ and not self.__PARSED__ and line_no > 35:
				log.debug(self.message(line_no, _("%s waited too long. Skipping.") % self.__SUB_TYPE__))
				return 
			sub_section = ''.join([sub_section, line])
			end = self.end_pattern.search(line)
			if self.__WITH_HEADER__ and not self.__HEADER_FOUND__:
				if line_no > self.__MAX_HEADER_LEN__:
					log.debug(self.message(line_no, _("Not a %s file.") % self.__SUB_TYPE__))
					return
				self.__HEADER_FOUND__ = self.get_header(sub_section, atom)
				if self.__HEADER_FOUND__:
					self.__PARSED__ = True
					sub_section = ''
			elif end:
				m = self.pattern.search(sub_section)
				try:
					if m.group('time_from'):
						atom['time_from'] = m.group('time_from')
						if self.__FMT__ not in ('frame', 'time'):
							self.__FMT__ = 'time' if re.search(r'[^A-Za-z0-9]', atom['time_from']) else 'frame'
						atom['time_from'] = self.str_to_frametime(atom['time_from'])
					if m.group('time_to'):
						atom['time_to'] = m.group('time_to')
						if self.__FMT__ not in ('frame', 'time'):
							self.__FMT__ = 'time' if re.search(r'[^A-Za-z0-9]', atom['time_to']) else 'frame'
						atom['time_to'] = self.str_to_frametime(atom['time_to'])
				except AttributeError, msg:
					if i > 0:
						raise SubParsingError, self.message(line_no, _("%s parsing error.") % self.__SUB_TYPE__)
					else:
						log.debug(self.message(line_no, _("Not a %s file.") % self.__SUB_TYPE__))
						return 
				except IndexError, msg:
					log.debug(self.message(line_no, msg))
				try:
					# There should be no more AttributeErrors as parse()
					# should return on it last time. If there is - we want
					# to know about it and fix it.
					if m.group('text'):
						atom['text'] = m.group('text')
				except IndexError, msg:
					log.debug(self.message(line_no, msg))

				# yield parsing result if new end marker occurred, then clear results
				if atom['time_from'] and atom['text']:
					atom['text'] = self.format_text(atom['text'])
					self.__PARSED__ = True
					yield { 'sub_no': i, 'fmt': self.__FMT__, 'sub': atom }
					i+= 1
				elif atom['time_from'] and not atom['text']:
					log.warning(self.message(line_no, _("No subtitle text found. Skipping that section.")))
				else:
					if i > 0:
						raise SubParsingError, self.message(line_no, _("%s parsing error.") % self.__SUB_TYPE__)
					else:
						log.debug(self.message(line_no, _("Not a %s file.") % self.__SUB_TYPE__))
						return 
				sub_section = ''
				atom = {'time_from': '', 'time_to': '', 'text': '',}
		log.info(_("Recognised %s.") % self.__SUB_TYPE__)

	def convert(self, sub):
		'''A function which gets dictionary containing single 
		sub info and returns appropriately formated string
		according to the passed sub format specification.
		First sub might also contain header info.'''
		try:
			sub_text = sub['sub']['text'].format(**self.sub_formatting)
		except KeyError, msg:
			log.warning(_("Key exception occured when trying to format sub: %s" %sub['sub']['text']))
			sub_text = sub['sub']['text']
		return self.sub_fmt.format(gsp_no = sub['sub_no'],\
			gsp_from = self.get_time(sub['sub']['time_from'], 'time_from'),\
			gsp_to = self.get_time(sub['sub']['time_to'], 'time_to'),\
			gsp_text = sub_text.encode(self.encoding))
	
	# Following methods should probably be polymorphed
	def get_header(self, sub_section , atom):
		'''Try to find header in a given sub_section. For example
		you can try to match precompiled regex or use Python string
		operations. Return True if header was parsed, False otherwise.
		Header parsing results should be saved as a dictionary to the
		atom['header']. After it returns True, it will not be called again.'''
		atom['header'] = {'info': sub_section.strip()}
		return True
	
	def convert_header(self, header):
		'''Convert parsed header keys and values to the string 
		that can be saved to file.'''
		header_str = ''
		for key, val in header.items():
			header_str = "%s[%s]:[%s]%s%s" % (header_str, key, val, os.linesep, os.linesep)
		return header_str.encode(self.encoding)

	def get_time(self, ft, which):
		'''Extract time (time_from or time_to) from FrameTime.
		Note that it usually needs to be first calculated using
		'to_frame or to_time methods. The output is properly formatted
		string according to sub specification.'''
		return ft.frame

	def str_to_frametime(self, s):
		'''Convert string to frametime objects.
		This one is called during file parsing to pass it
		to the other GenericSubParser subclass which can then
		recognize it and operate on it.'''
		return s
	
	def format_text(self, s):
		'''Convert sub-type specific formatting to the one known
		to GenericSubParser. Supported tags:
		{gsp_b}text{_gsp_b} -- bold
		{gsp_i}text{gsp_i} -- italics
		{gsp_u}text{_gsp_u} -- underline
		{gsp_nl} -- new line
		Don't forget to escape '{' and '}' curly braces.'''
		return s

class MicroDVD(GenericSubParser):
	__SUB_TYPE__ = 'Micro DVD'
	__OPT__ = 'microdvd'
	__FMT__ = 'frame'
	pattern = r'''
		^
		\{(?P<time_from>\d+)\}	# {digits} 
		\{(?P<time_to>\d+)\}	# {digits}
		(?P<text>[^\r\n]*)
		'''
	end_pattern = r'(?P<end>(?:\r?\n)|(?:\r))$'	# \r on mac, \n on linux, \r\n on windows
	sub_fmt = "{{{gsp_from}}}{{{gsp_to}}}{gsp_text}%s" % os.linesep	# Looks weird but escaping '{}' curly braces requires to double them
	sub_formatting = {
		'gsp_b_':	r'{y:b}', '_gsp_b':		r'',
		'gsp_i_':	r'{y:i}', '_gsp_i':		r'',
		'gsp_u_':	r'{y:u}', '_gsp_u':		r'',
		'gsp_nl':	r'|',
	}
	
	def __init__(self, f, fps, encoding, lines = []):
		GenericSubParser.__init__(self, f, fps, encoding, lines)
	
	def str_to_frametime(self, s):
		return FrameTime(fps=self.fps, value_type=self.__FMT__, frame=s)

	def format_text(self, s):
		s = s.replace('{', '{{').replace('}', '}}')
		lines = s.split('|')
		for i, l in enumerate(lines):
			if '{{y:b}}' in l:
				l = l.replace('{{y:b}}', '{gsp_b_}')
				l += '{_gsp_b}'
			if '{{y:i}}' in l:
				l = l.replace('{{y:i}}', '{gsp_i_}')
				l += '{_gsp_i}'
			if '{{y:u}}' in l:
				l = l.replace('{{y:u}}', '{gsp_u_}')
				l += '{_gsp_u}'
			lines[i] = l
		s = '{gsp_nl}'.join(lines)
		return s

	def get_time(self, ft, which):
		return ft.frame
	
class SubRip(GenericSubParser):
	__SUB_TYPE__ = 'Sub Rip'
	__OPT__ = 'subrip'
	__FMT__ = 'time'
	__EXT__ = 'srt'
	pattern = r'''
	^
	\d+\s+
	(?P<time_from>\d+:\d{2}:\d{2},\d+)	# 00:00:00,000
	[ \t]*-->[ \t]*
	(?P<time_to>\d+:\d{2}:\d{2},\d+)
	\s*
	(?P<text>[^\f\v\b]+)
	'''
	end_pattern = r'^(?P<end>(?:\r?\n)|(?:\r))$'	# \r\n on windows, \r on mac
	time_fmt = r'^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2}),(?P<ms>\d+)$'
	sub_fmt = "{gsp_no}%s{gsp_from} --> {gsp_to}%s{gsp_text}%s%s" % ( os.linesep, os.linesep, os.linesep, os.linesep)
	sub_formatting = {
		'gsp_b_':	r'<b>', '_gsp_b':	r'</b>',
		'gsp_i_':	r'<i>', '_gsp_i':	r'</i>',
		'gsp_u_':	r'<u>', '_gsp_u':	r'</u>',
		'gsp_nl':	os.linesep,
	}
	
	def __init__(self, f, fps, encoding, lines = []):
		self.time_fmt = re.compile(self.time_fmt)
		GenericSubParser.__init__(self, f, fps, encoding, lines)
	
	def str_to_frametime(self, s):
		time = self.time_fmt.search(s)
		return FrameTime(fps=self.fps, value_type=self.__FMT__, \
			h=time.group('h'), m=time.group('m'), \
			s=time.group('s'), ms=time.group('ms'))
	
	def format_text(self, s):
		s = s.strip()
		s = s.replace('{', '{{').replace('}', '}}')
		if r'<b>' in s:
			s = s.replace(r'<b>', '{gsp_b_}')
			s = s.replace(r'</b>', '{_gsp_b}')
		if r'<u>' in s:
			s = s.replace(r'<u>', '{gsp_u_}')
			s = s.replace(r'</u>', '{_gsp_u}')
		if r'<i>' in s:
			s = s.replace(r'<i>', '{gsp_i_}')
			s = s.replace(r'</i>', '{_gsp_i}')
		if '\r\n' in s:
			s = s.replace('\r\n', '{gsp_nl}')	# Windows
		elif '\n' in s:
			s = s.replace('\n', '{gsp_nl}')	# Linux
		elif '\r' in s:
			s = s.replace('\r', '{gsp_nl}')	# Mac
		return s
	
	def get_time(self, ft, which):
		return '%02d:%02d:%02d,%03d' % (int(ft.hours), int(ft.minutes), int(ft.seconds), int(ft.miliseconds))

class TMP(GenericSubParser):
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
	end_pattern = r'(?P<end>(?:\r?\n)|(?:\r))$'	# \r on mac, \n on linux, \r\n on windows
	time_fmt = r'^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2})$'
	sub_fmt = "{gsp_from}:{gsp_text}%s" % os.linesep	
	sub_formatting = {
		'gsp_b_':	r'', '_gsp_b':		r'',
		'gsp_i_':	r'', '_gsp_i':		r'',
		'gsp_u_':	r'', '_gsp_u':		r'',
		'gsp_nl':	r'|',
	}

	def __init__(self, f, fps, encoding, lines = []):
		self.time_fmt = re.compile(self.time_fmt)
		GenericSubParser.__init__(self, f, fps, encoding, lines)

	def str_to_frametime(self, s):
		time = self.time_fmt.search(s)
		return FrameTime(fps=self.fps, value_type=self.__FMT__, \
			h=time.group('h'), m=time.group('m'), \
			s=time.group('s'), ms=0)

	def format_text(self, s):
		s = s.strip()
		s = s.replace('{', '{{').replace('}', '}}')
		if '|' in s:
			s = s.replace('|', '{gsp_nl}')
		if '\r\n' in s:
			s = s.replace('\r\n', '{gsp_nl}')	# Windows
		elif '\n' in s:
			s = s.replace('\n', '{gsp_nl}')	# Linux
		elif '\r' in s:
			s = s.replace('\r', '{gsp_nl}')	# Mac
		return s

	def get_time(self, ft, which):
		if which == 'time_from':
			return '%02d:%02d:%02d' % (int(ft.hours), int(ft.minutes), int(ft.seconds))

class SubViewer(GenericSubParser):
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
		[\r\n]{1,2}		# linebreaks on different os's
		(?P<text>[^\f\v\b]+)
		'''
	end_pattern = r'^(?P<end>(?:\r?\n)|(?:\r))$'	# \r\n on windows, \r on mac
	time_fmt = r'^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2}).(?P<ms>\d+)$'
	sub_fmt = "{gsp_from},{gsp_to}%s{gsp_text}%s%s" % (os.linesep, os.linesep, os.linesep)
	sub_formatting = {
		'gsp_b_':	r'', '_gsp_b':	r'',
		'gsp_i_':	r'', '_gsp_i':	r'',
		'gsp_u_':	r'', '_gsp_u':	r'',
		'gsp_nl':	os.linesep,
	}
	
	def __init__(self, f, fps, encoding, lines = []):
		self.time_fmt = re.compile(self.time_fmt)
		GenericSubParser.__init__(self, f, fps, encoding, lines)
	
	def str_to_frametime(self, s):
		time = self.time_fmt.search(s)
		return FrameTime(fps=self.fps, value_type=self.__FMT__, \
			h=time.group('h'), m=time.group('m'), \
			s=time.group('s'), ms=time.group('ms'))

	def format_text(self, s):
		s = s.strip()
		s = s.replace('{', '{{').replace('}', '}}')
		if '\r\n' in s:
			s = s.replace('\r\n', '{gsp_nl}')	# Windows
		elif '\n' in s:
			s = s.replace('\n', '{gsp_nl}')	# Linux
		elif '\r' in s:
			s = s.replace('\r', '{gsp_nl}')	# Mac
		return s

	def get_time(self, ft, which):
		ms = int(round(ft.miliseconds / float(10)))
		return '%02d:%02d:%02d.%02d' % (int(ft.hours), int(ft.minutes), int(ft.seconds), ms)

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

def backup( filename ):
	new_arg = filename + datetime.now().strftime('_%y%m%d%H%M%S')
	try:
		os.remove(new_arg)
	except OSError:
		log.debug(_("No '%s' to remove before backuping.") % new_arg)
	shutil.move(filename, new_arg)
	return (new_arg, filename)

def mplayer_check( filename, fps ):
	command = ['mplayer', '-really-quiet', '-vo', 'null', '-ao', 'null', '-frames', '0', '-identify',]
	command.append(filename)
	try:
		mp_out = Popen(command, stdout=PIPE).communicate()[0]
		fps = re.search(r'ID_VIDEO_FPS=([\w/.]+)\s?', mp_out).group(1)
	except OSError:
		log.warning(_("Couldn't run mplayer. It has to be installed and placed in your $PATH in order to use auto_fps option."))
	except AttributeError:
		log.warning(_("Couldn't get FPS info from mplayer."))
	else:
		log.info(_("Got %s FPS from '%s'.") % (fps, filename))
	return fps

def prepare_options():
	optp = OptionParser(usage = _('Usage: %prog [options] input_file [input_file(s)]'),\
		version = '%s' % __VERSION__ )
	group_conv = OptionGroup(optp, _('Convert options'),
		_("Options which can be used to properly convert sub files."))
	optp.add_option('-f', '--force',
		action='store_true', dest='force', default=False,
		help=_("force all operations without asking (assuming yes)"))
	optp.add_option('-q', '--quiet',
		action='store_true', dest='quiet', default=False,
		help=_("verbose output"))
	optp.add_option('--debug',
		action='store_true', dest='debug_messages', default=False,
		help=_("Generate debug output"))
	group_conv.add_option('-e', '--encoding',
		action='store', type='string', dest='encoding', default='ascii',
		help=_("input file encoding. Default: 'ascii'. For a list of available encodings, see: http://docs.python.org/library/codecs.html#standard-encodings"))
	group_conv.add_option('-m', '--format',
		action='store', type='string', dest='format', default = 'subrip',
		help=_("output file format. Default: subrip"))
	group_conv.add_option('-s', '--fps',
		action='store', type='float', dest='fps', default = 25,
		help=_("select movie/subtitles frames per second. Default: 25"))
	group_conv.add_option('-S', '--auto-fps',
		action='store_true', dest='auto_fps', default=False,
		help=_("automatically try to get fps from mplayer"))
	group_conv.add_option('-v', '--video-file', default = '',
		action='store', type='string', dest='movie_file',
		help=_("movie file to get fps info from"))
	group_conv.add_option('-x', '--extension',
		action='store', type='string', dest='ext',
		help=_("specify extension of the output file if the default one is not what you like."))

	optp.add_option_group(group_conv)
	return optp

def convert_file(filepath, file_encoding, file_fps, output_format, output_extension = ''):
	cls = GenericSubParser.__subclasses__()
	conv = None
	for c in cls:
		# Obtain user specified subclass
		if c.__OPT__ == output_format:
			filename, extension = os.path.splitext(filepath)
			extension = output_extension if output_extension else c.__EXT__
			conv = c(filename + '.' + extension, file_fps, file_encoding)
			break
	if not conv:
		raise NameError

	# Try to detect file encoding
	# 'is' keyword checks objects identity and it's the key to disabling
	# autodetect when '-e ascii' option is given. It seems that optparse
	# creates a new object (which is logical) when given an option from
	# shell and overrides a variable in program memory.
	if IS_CHARDET and file_encoding is 'ascii': 
		fs = os.path.getsize(filepath)
		size = 1400 if fs > 1400 else fs
		with open(filepath, mode='r',) as f:
			rd = f.read(size)
			enc = chardet.detect(rd)
			log.debug(_("Detecting encoding from %d bytes") % len(rd))
			log.debug(_(" ...chardet: %s") % enc)
		if enc['confidence'] > 0.60:
			file_encoding = enc['encoding']
			conv.encoding = file_encoding
			log.debug(_(" ...detected %s encoding.") % enc['encoding'])
		else:
			log.debug(_("I am not too confident about encoding. Skipping check."))

	with codecs.open(filepath, mode='r', encoding=file_encoding) as f:
		file_input = f.readlines()

	lines = []
	log.info(_("Trying to parse %s...") % filepath)
	sub_pair = [None, None]
	for cl in cls:
		if not lines:
			c = cl(filepath, file_fps, file_encoding, file_input)
			for p in c.parse():
				if not sub_pair[1] and conv.__WITH_HEADER__: # Only the first element
					header = p['sub'].get('header')
					if type(header) != dict:
						header = {}
					header = conv.convert_header(header)
					if header:
						lines.append(header.decode(conv.encoding))
				sub_pair[0] = sub_pair[1]
				sub_pair[1] = p
				try:
					if sub_pair[0]:
						if not sub_pair[0]['sub']['time_to']:
							sub_pair[0]['sub']['time_to'] = \
								sub_pair[0]['sub']['time_from'] + \
								(sub_pair[1]['sub']['time_from'] - sub_pair[0]['sub']['time_from']) * 0.85
						s = conv.convert(sub_pair[0])
						lines.append(s.decode(conv.encoding))
					else:
						if sub_pair[1]:
							if not sub_pair[1]['sub']['time_to']:
								sub_pair[1]['sub']['time_to'] = \
									sub_pair[1]['sub']['time_from'] + FrameTime(file_fps, 'ss', seconds = 2.5)
							s = conv.convert(sub_pair[1])
							lines.append(s.decode(conv.encoding))
				except AssertionError:
					log.warning(_("Correct time not asserted for subtitle %d. Skipping it...") % (sub_pair[0]['sub_no']))
					log.debug(_(".. incorrect subtitle pair times: (%s, %s)") % (sub_pair[0]['sub']['time_from'], sub_pair[1]['sub']['time_from']))
	return (conv, lines)

def main():
	MAX_MEGS = 5 * 1048576
	optp = prepare_options()
	(options, args) = optp.parse_args()
	
	if len(args)  < 1:
		log.error(_("Incorrect number of arguments."))
		return -1

	# A little hack to assure that translator won't make a mistake
	_choices = { 'yes': _('y'), 'no': _('n'), 'quit': _('q'), 'backup': _('b') }
	if options.quiet:
		log.setLevel(logging.ERROR)
	else:
		log.setLevel(logging.INFO)
	if options.debug_messages:
		log.setLevel(logging.DEBUG)
	log.addHandler(ch)
	
	for arg in args:
		if not os.path.isfile(arg):
			log.error(_("No such file: %s") % arg)
			continue

		if os.path.getsize(arg) > MAX_MEGS:
			log.warning(_("File '%s' too large.") % arg)
			continue
		
		if options.auto_fps:
			exts = ('.avi', '.mkv', '.mpg', '.mp4', '.wmv')
			if not options.movie_file:
				filename, extension = os.path.splitext(arg)
				for ext in exts:
					f = ''.join((filename, ext))
					if os.path.isfile(f):
						options.fps = mplayer_check(f, options.fps)
						break
			else:
				options.fps = mplayer_check(options.movie_file, options.fps)

		try:
			conv, lines = convert_file(arg, options.encoding, options.fps, options.format, options.ext)
		except NameError:
			log.error(_("'%s' format not supported (or mistyped).") % options.format)
			return -1
		except UnicodeDecodeError:
			log.error(_("Couldn't handle '%s' given '%s' encoding.") % (arg, options.encoding))
			continue
		except SubParsingError, msg:
			log.error(msg)
			continue;

		if lines:
			log.info(_("Parsed."))
			if os.path.isfile(conv.filename):
				choice = ''
				if options.force:
					choice = _choices['yes']
				while( choice not in (_choices['yes'], _choices['no'], _choices['backup'], _choices['quit'])):
					choice = raw_input( _("File '%s' exists. Overwrite? [y/n/b/q] ") % conv.filename)
				if choice == _choices['backup']:
					if conv.filename == arg:
						arg, _mvd = backup(arg)	# We will read from backed up file
						log.info(_("%s backed up as %s") % (_mvd, arg))
					else:
						_bck, conv_filename = backup(conv.filename)
						log.info(_("%s backed up as %s") % (conv.filename, _bck))
				elif choice == _choices['no']:
					log.info(_("Skipping %s") % arg)
					continue
				elif choice == _choices['yes']:
					log.info(_("Overwriting %s") % conv.filename)
				elif choice == _choices['quit']:
					log.info(_("Quitting converting work."))
					return 1
			else:
				log.info("Writing to %s" % conv.filename)
		
			with codecs.open(conv.filename, 'w', encoding=conv.encoding) as cf:
				cf.writelines(lines)
		else:
			log.warning(_("%s not parsed.") % arg)

if __name__ == '__main__':
	main()