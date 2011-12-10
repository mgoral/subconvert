import os
import sys
import codecs
import logging
import gettext
import re

log = logging.getLogger('SubConvert.%s' % __name__)

gettext.bindtextdomain('subconvert', '/usr/lib/subconvert/locale')
gettext.textdomain('subconvert')
_ = gettext.gettext


class SubParsingError(Exception):
	pass

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

