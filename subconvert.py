#!/usr/bin/python
#-*- coding: utf-8 -*-

import os
import sys
import re
import codecs
import logging
from optparse import OptionParser
import gettext

__VERSION__ = '0.0.1'
__AUTHOR__ = u'Michał Góral'

log = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

gettext.bindtextdomain('subconvert', '/usr/lib/subconvert/locale')
gettext.textdomain('subconvert')
_ = gettext.gettext

class SubError(Exception):
	pass

class FrameTime:
	hours = 0
	minutes = 0
	seconds = 0
	miliseconds = 0
	frame = 0

	def __init__(self, h=0, m=0, s=0, ms=0, frame=0):
		if int(h) < 0 or int(m) > 59 or int(m) < 0 or int(s) > 59 or int(s) < 0 or int(ms) > 999 or int(ms) < 0:
			raise ValueError, "Arguments not in allowed ranges."
		frame = int(frame)
		self.frame = frame
		self.hours = h
		self.minutes = m
		self.seconds = s
		self.miliseconds = ms

	def to_time(self, fps):
		fps = float(fps)
		tmp = self.frame / fps
		print tmp
		print fps
		seconds = int(tmp)
		self.miliseconds = int((tmp - seconds)*1000)
		self.hours = seconds / 3600
		seconds -= 3600 * self.hours
		self.minutes = seconds / 60
		self.seconds = seconds - 60 * self.minutes
		return (self.hours, self.minutes, self.seconds, self.miliseconds)
	
	def to_frame(self, fps):
		fps = float(fps)
		self.frame = int(fps * (3600*int(self.hours) + 60*int(self.minutes) + int(self.seconds) + float(self.miliseconds)/1000))
		return self.frame

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
	__FMT__ = 'Unknown' 	# time/frame
	time_pattern = r'(?P<time_from>\d+) (?P<time_to>\d+)'
	text_pattern = r'(?P<text>.+)'
	start_pattern = r'(?P<start>\n)'
	sub_fmt = ''			# output subtitle format
	sub_formatting = {}

	def __init__(self, f, encoding):
		'''Usually you will only need to call super __init__(filename, encoding)
		from a specialized class.'''

		assert os.path.isfile(f), "File %s doesn't exist." % f
		self.atom_t = {'time_from': '', 'time_to': '', 'text': '',}
		self.filename = f
		pattern = r'(?:%s)|(?:%s)' % (self.time_pattern, self.text_pattern)
		self.pattern = re.compile(pattern, re.X)
		self.start_pattern = re.compile(self.start_pattern)
		self.encoding = encoding
	
	def parse(self):
		'''Actual parser.
		Please note that time_to is not required 
		to process as not all subtitles provide it.'''

		atom = self.atom_t.copy()
		i = 0
		line_no = 0
		with codecs.open(self.filename, mode='r', encoding=self.encoding) as f:
			for line in f:
				line_no += 1
				it = self.pattern.finditer(line)
				st = self.start_pattern.search(line)
				try:
					if st:
						# yield parsing result if new start marker occurred, then clear results
						if atom['time_from'] and atom['text']:
							atom['text'] = self.format_text(atom['text'])
							yield { 'sub_no': i, 'fmt': self.__FMT__, 'sub': atom }
						i+=1
						atom = self.atom_t.copy()
				except IndexError:
					log.error(_('Start of sub catching not specified. Aborting.'))
					raise
				for m in it:
					try:
						if m.group('time_from'):
							if not atom['time_from']:
								atom['time_from'] = m.group('time_from')
								if self.__FMT__ not in ('frame', 'time'):
									self.__FMT__ = 'time' if re.search(r'[^A-Za-z0-9]', atom['time_from']) else 'frame'
								atom['time_from'] = self.str_to_frametime(atom['time_from'])
							else:
								raise SubError, 'time_from catched/specified twice at line %d: %s --> %s' % (line_no, atom['time_from'], m.group('time_from'))
						if m.group('time_to'):
							if not atom['time_to']:
								atom['time_to'] = m.group('time_to')
								if self.__FMT__ not in ('frame', 'time'):
									self.__FMT__ = 'time' if re.search(r'[^A-Za-z0-9]', atom['time_to']) else 'frame'
								atom['time_to'] = self.str_to_frametime(atom['time_to'])
							else:
								raise SubError, 'time_to catched/specified twice at line %d %s --> %s' % (line_no, atom['time_to'], m.group('time_to'))
						if m.group('text'):
							atom['text'] += m.group('text')
						if not i and (atom['time_from'] or atom['time_to'] or atom['text']):
							# return if we gathered something before start marker occurrence
							log.debug(_("Not a %s file." % self.__SUB_TYPE__))
							return
					except IndexError, msg:
						log.debug(msg)
		yield { 'sub_no': i, 'fmt': self.__FMT__, 'sub': atom }	# One last goodbye - no new start markers after the last one.	

	def convert(self, sub, sub_fmt=None, formatting=None):
		'''A function which gets dictionary containing single 
		sub info and returns appropriately formated string
		according to the passed sub format specification.'''
		# Switch to self.x values or default if none provided
		if not sub_fmt:
			sub_fmt = self.sub_fmt
			if not sub_fmt:
				fmt = r"{gsp_no}:\r\n{gsp_from} : {gsp_to}\r\n{gsp_text}"
		if not formatting:
			formatting = self.sub_formatting
			if not formatting:
				formatting = {
					'gsp_b':	r'', '_gsp_b': 	r'',
					'gsp_i': 	r'', '_gsp_i': 	r'',
					'gsp_u': 	r'', '_gsp_u': 	r'',
					'gsp_nl': 	r'/r/n',
				}

		try:
			sub_text = sub['sub']['text'].format(formatting)
		except KeyError:
			log.warning(_("Key exception occured when trying to format sub: %s" %sub['sub']['text']))
			sub_text = sub['sub']['text']
		return sub_fmt.format(gsp_no = sub['sub_no'],\
			gsp_from = self.get_time(sub['sub']['time_from'], 'time_from'),\
			gsp_to = self.get_time(sub['sub']['time_to'], 'time_to'),\
			gsp_text = sub_text.encode(self.encoding))
	
	# Following methods should probably be polymorphed
	def get_time(self, ft, which):
		'''Extract time (time_from or time_to) from FrameTime.'''
		return ft.frame

	def str_to_frametime(self, s):
		'''Convert string to frametime objects.'''
		return s
	
	def format_text(self, s):
		'''Convert sub-type specific formatting to the one known
		to GenericSubParser. Supported tags:
		{gsp_b}text{_gsp_b} -- bold
		{gsp_i}text{gsp_i} -- italics
		{gsp_u}text{_gsp_u} -- underline
		{gsp_nl} -- new line'''
		return s

class MicroDVD(GenericSubParser):
	__SUB_TYPE__ = 'Micro DVD'
	__OPT__ = 'microdvd'
	__FMT__ = 'frame'
	time_pattern = r'''
		^
		\{(?P<time_from>\d+)\}	# {digits} 
		\{(?P<time_to>\d+)\}	# {digits}
		'''
	text_pattern = r'''
		(?P<text>
		[^\r\n]+
		)		# End of asignment
		'''
	start_pattern = r'^(?P<start>\{\d+\})'
	
	def __init__(self, f, encoding):
		GenericSubParser.__init__(self, f, encoding)
	
	def str_to_frametime(self, s):
		return FrameTime(frame=s)
	
	def get_time(self, ft, which):
		return ft.frame
	
class SubRip(GenericSubParser):
	__SUB_TYPE__ = 'Sub Rip'
	__OPT__ = 'subrip'
	__FMT__ = 'time'
	time_pattern = r'''
	^
	(?P<time_from>\d+:\d{2}:\d{2},\d+)	# 00:00:00,000
	[ \t]*-->[ \t]*
	(?P<time_to>\d+:\d{2}:\d{2},\d+)
	\s*
	$
	'''
	text_pattern = r'''^(?:\d+\r?\n)|(?P<text>[^\r\v\n]+\s*)$'''
	start_pattern = r'^\d+\s*$'
	time_fmt = r'^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2}),(?P<ms>\d+)$'
	sub_fmt = "{gsp_no}\r\n{gsp_from} --> {gsp_to}\r\n{gsp_text}\r\n"
	sub_formatting = {}
	
	def __init__(self, f, encoding):
		self.time_fmt = re.compile(self.time_fmt)
		GenericSubParser.__init__(self, f, encoding)
	
	def str_to_frametime(self, s):
		time = self.time_fmt.search(s)
		return FrameTime(h=time.group('h'), m=time.group('m'), s=time.group('s'), ms=time.group('ms'))
	
	def get_time(self, ft, which):
		return '%02d:%02d:%02d,%03d' % (int(ft.hours), int(ft.minutes), int(ft.seconds), int(ft.miliseconds))

def main():
	optp = OptionParser(usage = _('Usage: %prog [options] input_file [output_file]'),\
		version = '%s' % __VERSION__ )
	optp.add_option('-f', '--fps',
		action='store', type='int', dest='fps', default = 25,
		help=_("select movie/subtitles frames per second. Default: 25"))
	optp.add_option('-F', '--format',
		action='store', type='string', dest='format', default = 'subrip',
		help=_("output file format. Default: subrip"))
	optp.add_option('-e', '--encoding',
		action='store', type='string', dest='encoding', default='ascii',
		help=_("input file encoding. Default: 'ascii'. For a list of available encodings, see: http://docs.python.org/library/codecs.html#standard-encodings"))
	
	(options, args) = optp.parse_args()
	
	if len(args) not in (1, 2,):
		log.error(_("Incorrect number of arguments."))
		return
	
	cls = GenericSubParser.__subclasses__()
	convert_to = None
	for c in cls:
		if c.__OPT__ == options.format:
			try:
				conv = c(args[1], options.encoding)
			except IndexError:
				filename, extension = os.path.splitext(args[0])
				conv = c(filename + '.' + c.__EXT__, options.encoding)
			break
	if not conv:
		log.error(_("%s not supported or mistyped." % options.format))
		return -1
	try:
		for cl in cls:
			c = cl(args[0], options.encoding)
			if c.__FMT__ != conv.__FMT__:
				if conv.__FMT__ == 'time':
					for p in c.parse():
						p['sub']['time_from'].to_time(options.fps)
						p['sub']['time_to'].to_time(options.fps)
						s = conv.convert(p)
						print s
				elif conv.__FMT__ == 'frame':
					for p in c.parse():
						p['sub']['time_from'].to_frame(options.fps)
						p['sub']['time_to'].to_frame(options.fps)
						s = conv.convert(p)
						print s
			else:
				for p in c.parse():
					s = conv.convert(p)
					print s
	except UnicodeDecodeError:
		log.error(_("I'm terribly sorry but it seems that I couldn't handle %s given %s encoding. Maybe try defferent encoding?" % (args[0], options.encoding)))

if __name__ == '__main__':
	main()

