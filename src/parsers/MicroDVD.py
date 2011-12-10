import os
import codecs
import re

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

