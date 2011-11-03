#!/usr/bin/python

import os
import re
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class SubError(Exception):
	pass

class GenericParser:
	'''Generic class that should be inherited
	and polymorphed by the other, specialized
	classes. Usually only __init__ and patterns
	should be rewritten in successors.'''

	# Overwrite these in inherited classes
	time_pattern = r'(?P<time_from>\d+) (?P<time_to>\d+)'
	text_pattern = r'(?P<text>.+)'
	end_pattern = r'(?P<end>/n)'

	def __init__(self, f):
		'''Usually you will only need to call super.__init__(f)
		from a specialized class.'''

		assert os.path.isfile(f), "File %s doesn't exist." % f
		self.atom_t = {'time_from': '', 'time_to': '', 'text': '',}
		self.atom = self.atom_t.copy()
		self.filename = f
		pattern = r'(?:%s)|(?:%s)|(?:%s)' % (time_pattern, text_pattern, end_pattern)
		self.pattern = re.compile(pattern)

	def parse():
		'''Actual parser.'''

		with open(filename, 'r') as f:
			i = 0
			for line in f:
				it = self.pattern.finditer(line)
				for m in it:
					try:
						if m.group('time_from'):
							if not self.atom['time_from']:
								self.atom['time_from'] = m.group('time_from')
							else:
								raise SubError
						if m.group('time_to'):
							if not self.atom['time_to']:
								self.atom['time_to'] = m.group('time_to')
							else:
								raise SubError
						if m.group('text'):
							self.atom['text'] += m.group('text')
					except IndexError, msg:
						log.debug(msg)
					try:
						if m.group('end'):
							i += 1
							yield { 'sub_no': i, 'sub': self.atom }
							self.atom = self.atom_t.copy()
					except IndexError:
						log.error('End of sub catching not specified. Aborting.')
