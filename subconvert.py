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
	time_pattern = r'(?P<time_from>\d+) (?P<time_to>\d+)'
	text_pattern = r'(?P<text>.+)'
	end_pattern = r'(?P<end>\n)'

	def __init__(self, f):
		'''Usually you will only need to call super.__init__(f)
		from a specialized class.'''

		assert os.path.isfile(f), "File %s doesn't exist." % f
		self.atom_t = {'time_from': '', 'time_to': '', 'text': '',}
		self.filename = f
		pattern = r'(?:%s)|(?:%s)|(?:%s)' % (self.time_pattern, self.text_pattern, self.end_pattern)
		self.pattern = re.compile(pattern, re.X)

	def parse(self):
		'''Actual parser.'''
		atom = self.atom_t.copy()
		fmt = ''
		with open(self.filename, 'r') as f:
			i = 0
			line_no = 0
			for line in f:
				line_no += 1
				it = self.pattern.finditer(line)
				for m in it:
					try:
						if m.group('time_from'):
							if not atom['time_from']:
								atom['time_from'] = m.group('time_from')
							else:
								pass
								#raise SubError, 'time_from catched/specified twice at line %d: %s --> %s' % (line_no, self.atom['time_from'], m.group('time_from'))
						if m.group('time_to'):
							if not atom['time_to']:
								atom['time_to'] = m.group('time_to')
							else:
								pass
								#raise SubError, 'time_to catched/specified twice at line %d %s --> %s' % (line_no, self.atom['time_to'], m.group('time_to'))
						if m.group('text'):
							atom['text'] += m.group('text')
					except IndexError, msg:
						log.debug(msg)
					try:
						if m.group('end'):
							i += 1
							if not atom['time_from']:
								return
							if not fmt:
								# if there are any not-alphanumeric characters,
								# suppose it's time format
								fmt = 'time' if re.search(r'[^A-Za-z0-9]', atom['time_from']) else 'frame'
							yield { 'sub_no': i, 'fmt': fmt, 'sub': atom }
							atom = self.atom_t.copy()
					except IndexError:
						log.error(_('End of sub catching not specified. Aborting.'))
						raise

class MicroDVD(GenericSubParser):
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
	end_pattern = r'(?P<end>\r?\n$)'
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
		print p
	

if __name__ == '__main__':
	main()

