#!/usr/bin/python
#-*- coding: utf-8 -*-

import os
import sys
import re
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

class GenericSubParser:
	'''Generic class that should be inherited
	and polymorphed by the other, specialized
	classes. Usually only __init__ and patterns
	should be rewritten in successors.'''

	# Overwrite these in inherited classes
	# Note that start_pattern is checked independently to 
	# time_pattern and text_pattern (which are OR-ed)
	__SUB_TYPE__ = 'Generic'
	time_pattern = r'(?P<time_from>\d+) (?P<time_to>\d+)'
	text_pattern = r'(?P<text>.+)'
	start_pattern = r'(?P<start>\n)'

	def __init__(self, f):
		'''Usually you will only need to call super __init__()
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
		fmt = ''
		i = 0
		line_no = 0
		with open(self.filename, 'r') as f:
			for line in f:
				line_no += 1
				it = self.pattern.finditer(line)
				st = self.start_pattern.search(line)
				try:
					if st:
						# yield parsing result if new start marker occurred, then clear results
						if atom['time_from'] and atom['text']:
							yield { 'sub_no': i, 'fmt': fmt, 'sub': atom }
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
								if not fmt:
									# if there are any not-alphanumeric characters,
									# suppose it's time format
									fmt = 'time' if re.search(r'[^A-Za-z0-9]', atom['time_from']) else 'frame'
							else:
								raise SubError, 'time_from catched/specified twice at line %d: %s --> %s' % (line_no, atom['time_from'], m.group('time_from'))
						if m.group('time_to'):
							if not atom['time_to']:
								atom['time_to'] = m.group('time_to')
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
		yield { 'sub_no': i, 'fmt': fmt, 'sub': atom }	# One last goodbye - no new start markers after the last one.

class MicroDVD(GenericSubParser):
	__SUB_TYPE__ = 'Micro DVD'
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
	
	def __init__(self, f):
		GenericSubParser.__init__(self, f)

class SubRip(GenericSubParser):
	__SUB_TYPE__ = 'Sub Rip'
	time_pattern = r'''
	^
	(?P<time_from>\d+:\d{2}:\d{2},\d+)	# 00:00:00,000
	[ \t]*-->[ \t]*
	(?P<time_to>\d+:\d{2}:\d{2},\d+)
	\s*
	$
	'''
	text_pattern = r'''^(?P<text>[^\r\v\n]+\s*)$'''
	start_pattern = r'^\d+\s*$'
	
	def __init__(self, f):
		GenericSubParser.__init__(self, f)
	
def main():
	optp = OptionParser(usage = _('Usage: %prog [options] input_file [output_file]'),\
		version = '%s' % __VERSION__ )
	optp.add_option('-f', '--fps',
		action='store', type='int', dest='fps', default = 25,
		help=_("select movie/subtitles frames per second"))
	optp.add_option('-F', '--format',
		action='store', type='string', dest='format', default = 'subrip',
		help=_("output file format"))
	
	(options, args) = optp.parse_args()

	if len(args) not in (1, 2,):
		log.error(_("Incorrect number of arguments."))
		return
	
	c = MicroDVD(args[0])
	for p in c.parse():
		print '1'
		print p
	c = SubRip(args[0])
	for p in c.parse():
		print '2'
		print p

if __name__ == '__main__':
	main()

