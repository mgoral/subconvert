import os
import codecs
import re

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

