#!/usr/bin/python
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
import logging
from optparse import OptionParser, OptionGroup
import gettext
from datetime import datetime

__VERSION__ = '0.6.0'
__AUTHOR__ = u'Michał Góral'

log = logging.getLogger(__name__)
ch = logging.StreamHandler()

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
	sub_fmt = "{gsp_no}:" + os.linesep + "{gsp_from} : {gsp_to}" + os.linesep + "{gsp_text}"	# output subtitle format
	sub_formatting = {
		'gsp_b_':	r'', '_gsp_b': 	r'',
		'gsp_i_': 	r'', '_gsp_i': 	r'',
		'gsp_u_': 	r'', '_gsp_u': 	r'',
		'gsp_nl': 	os.linesep,
		}
	
	# Do not overwrite further
	__PARSED__ = False

	def __init__(self, f, encoding):
		'''Usually you will only need to call super __init__(filename, encoding)
		from a specialized class.'''

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
			lines = f.readlines()
		try:
			for line_no, line in enumerate(lines):
				if not self.__PARSED__ and line_no > 35:
					log.debug(_("%s waited too long. Skipping.") % self.__SUB_TYPE__)
					return
				it = self.pattern.finditer(line)
				st = self.start_pattern.search(line)
				try:
					if st:
						# yield parsing result if new start marker occurred, then clear results
						if atom['time_from'] and atom['text']:
							atom['text'] = self.format_text(atom['text'])
							self.__PARSED__ = True
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
							log.debug(_("Not a %s file.") % self.__SUB_TYPE__)
							return
					except IndexError, msg:
						log.debug(msg)
			if atom['time_from'] and atom['text']:
				# One last goodbye - no new start markers after the last one.	
				atom['text'] = self.format_text(atom['text'])
				self.__PARSED__ = True
				yield { 'sub_no': i, 'fmt': self.__FMT__, 'sub': atom }	
		except IOError:
			log.error(_("No such file: '%s'" % self.filename))

	def convert(self, sub):
		'''A function which gets dictionary containing single 
		sub info and returns appropriately formated string
		according to the passed sub format specification.'''
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
	sub_fmt = "{{{gsp_from}}}{{{gsp_to}}}{gsp_text}" + os.linesep	# Looks weird but escaping '{}' curly braces requires to double them
	sub_formatting = {
		'gsp_b_':	r'{y:b}', '_gsp_b': 	r'',
		'gsp_i_': 	r'{y:i}', '_gsp_i': 	r'',
		'gsp_u_': 	r'{y:u}', '_gsp_u': 	r'',
		'gsp_nl': 	r'|',
	}
	
	def __init__(self, f, encoding):
		GenericSubParser.__init__(self, f, encoding)
	
	def str_to_frametime(self, s):
		return FrameTime(frame=s)

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
	sub_fmt = "{gsp_no}"+ os.linesep + "{gsp_from} --> {gsp_to}" + os.linesep + "{gsp_text}" + os.linesep + os.linesep
	sub_formatting = {
		'gsp_b_':	r'<b>', '_gsp_b': 	r'</b>',
		'gsp_i_': 	r'<i>', '_gsp_i': 	r'</i>',
		'gsp_u_': 	r'<u>', '_gsp_u': 	r'</u>',
		'gsp_nl': 	os.linesep,
	}
	
	def __init__(self, f, encoding):
		self.time_fmt = re.compile(self.time_fmt)
		GenericSubParser.__init__(self, f, encoding)
	
	def str_to_frametime(self, s):
		time = self.time_fmt.search(s)
		return FrameTime(h=time.group('h'), m=time.group('m'), s=time.group('s'), ms=time.group('ms'))
	
	def format_text(self, s):
		s = s.replace('{', '{{').replace('}', '}}')
		s = s.replace(r'<b>', '{gsp_b_}')
		s = s.replace(r'</b>', '{_gsp_b}')
		s = s.replace(r'<u>', '{gsp_u_}')
		s = s.replace(r'</u>', '{_gsp_u}')
		s = s.replace(r'<i>', '{gsp_i_}')
		s = s.replace(r'</i>', '{_gsp_i}')
		s = s.replace('\r\n', '{gsp_nl}')	# Windows
		s = s.replace('\n', '{gsp_nl}')	# Linux
		if s.endswith('{gsp_nl}'):
			s = s[:-8]
		return s
	
	def get_time(self, ft, which):
		return '%02d:%02d:%02d,%03d' % (int(ft.hours), int(ft.minutes), int(ft.seconds), int(ft.miliseconds))

def backup( filename ):
	new_arg = filename + datetime.now().strftime('_%y%m%d%H%M%S')
	try:
		os.remove(new_arg)
	except OSError:
		log.debug(_("No '%s' to remove before backuping.") % new_arg)
	shutil.move(filename, new_arg)
	return (new_arg, filename)

def main():
	optp = OptionParser(usage = _('Usage: %prog [options] input_file [output_file]'),\
		version = '%s' % __VERSION__ )
	group_conv = OptionGroup(optp, _('Convert options'),
		_("Options which can be used to properly convert sub files."))
	optp.add_option('-f', '--force',
		action='store_true', dest='force', default=False,
		help=_("force all operations without asking (assuming yes)"))
	optp.add_option('-v', '--verbose',
		action='store_true', dest='verbose', default=False,
		help=_("verbose output"))
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

	optp.add_option_group(group_conv)
	
	(options, args) = optp.parse_args()

	# A little hack to assure that translator won't make a mistake
	_choices = { 'yes': _('y'), 'no': _('n'), 'quit': _('q'), 'backup': _('b') }
	if options.verbose:
		log.setLevel(logging.INFO)
	else:
		log.setLevel(logging.ERROR)
	log.addHandler(ch)
	
	if len(args) not in (1, 2,):
		log.error(_("Incorrect number of arguments."))
		return
	
	if not os.path.isfile(args[0]):
		log.error(_("No such file: %s") % args[0])
		return -1
	
	if options.auto_fps:
		from subprocess import Popen, PIPE
		# -really-quiet seems to display some info (like FPS, resolution etc.)
		command = ['mplayer', '-really-quiet', '-vo', 'null', '-ao', 'null', '-frames', '0', '-identify',]
		exts = ('.avi', )
		filename, extension = os.path.splitext(args[0])
		for ext in exts:
			f = ''.join((filename, ext))
			if os.path.isfile(f):
				command.append(f)
				try:
					mp_out = Popen(command, stdout=PIPE).communicate()[0]
				except OSError:
					log.warning(_("Couldn't run mplayer. It has to be installed and placed in your $PATH in order to use auto_fps option."))
					break
				try:
					options.fps = re.search(r'ID_VIDEO_FPS=([\w/.]+)\s?', mp_out).group(1)
				except AttributeError:
					log.info(_("Couldn't get FPS info from mplayer."))
					break
	
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
		log.error(_("%s not supported or mistyped.") % options.format)
		return -1
	elif conv.filename == args[0]:
		# We will write to original path (conv.filename) but read from backup (new args[0])
		args[0], _bck = backup(args[0])
		log.warning(_("Trying to overwrite input file which is, generally speaking, not wise. Backing up %s as %s") % (_bck, args[0]))
	elif os.path.isfile(conv.filename):
		choice = ''
		if options.force:
			choice = _choices['yes']
		while( choice not in (_choices['yes'], _choices['no'], _choices['backup'])):
			choice = raw_input( _("File '%s' exists. Overwrite? [y/n/b] ") % conv.filename)
		if choice == _choices['backup']:
			_bck, conv_filename = backup(conv.filename)
			log.info(_("%s backed up as %s") % (conv_filename, _bck))
		elif choice == _choices['no']:
			log.info(_("%s wasn't converted.") % args[0])
			return 0
		elif choice == _choices['yes'] and options.verbose:
			log.info(_("Overwriting %s") % conv.filename)
	else:
		log.info("Writing to %s" % conv.filename)
	try:
		lines = []
		for cl in cls:
			c = cl(args[0], options.encoding)
			if not lines and c.__FMT__ != conv.__FMT__:
				if conv.__FMT__ == 'time':
					for p in c.parse():
						p['sub']['time_from'].to_time(options.fps)
						p['sub']['time_to'].to_time(options.fps)
						s = conv.convert(p)
						lines.append(s.decode(conv.encoding))
				elif conv.__FMT__ == 'frame':
					for p in c.parse():
						p['sub']['time_from'].to_frame(options.fps)
						p['sub']['time_to'].to_frame(options.fps)
						s = conv.convert(p)
						lines.append(s.decode(conv.encoding))
			elif not lines and c.__FMT__ == conv.__FMT__ :
				for p in c.parse():
					s = conv.convert(p)
					lines.append(s.decode(conv.encoding))
	except UnicodeDecodeError:
		log.error(_("I'm terribly sorry but it seems that I couldn't handle %s given %s encoding. Maybe try different encoding?") % (args[0], options.encoding))
	if lines:
		with codecs.open(conv.filename, 'w', encoding=conv.encoding) as cf:
			cf.writelines(lines)

if __name__ == '__main__':
	main()
