import os
import codecs
import re

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

