import os
import codecs
import re

from SubParser import GenericSubParser
from FrameTime import FrameTime

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

