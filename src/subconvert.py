#!/usr/bin/env python
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
from subprocess import Popen, PIPE
import logging
from optparse import OptionParser, OptionGroup
import gettext
from datetime import datetime

import subparser.SubParser as SubParser
import subparser.FrameTime as FrameTime
import subparser.Parsers

try:
	import chardet
	IS_CHARDET = True
except ImportError:
	IS_CHARDET = False

__VERSION__ = '0.8.1'
__AUTHOR__ = u'Michał Góral'

log = logging.getLogger(__name__)
ch = logging.StreamHandler()

gettext.bindtextdomain('subconvert', '/usr/lib/subconvert/locale')
gettext.textdomain('subconvert')
_ = gettext.gettext

	
def backup( filename ):
	new_arg = filename + datetime.now().strftime('_%y%m%d%H%M%S')
	try:
		os.remove(new_arg)
	except OSError:
		log.debug(_("No '%s' to remove before backuping.") % new_arg)
	shutil.move(filename, new_arg)
	return (new_arg, filename)

def mplayer_check( filename, fps ):
	command = ['mplayer', '-really-quiet', '-vo', 'null', '-ao', 'null', '-frames', '0', '-identify',]
	command.append(filename)
	try:
		mp_out = Popen(command, stdout=PIPE).communicate()[0]
		fps = re.search(r'ID_VIDEO_FPS=([\w/.]+)\s?', mp_out).group(1)
	except OSError:
		log.warning(_("Couldn't run mplayer. It has to be installed and placed in your $PATH in order to use auto_fps option."))
	except AttributeError:
		log.warning(_("Couldn't get FPS info from mplayer."))
	else:
		log.info(_("Got %s FPS from '%s'.") % (fps, filename))
	return fps

def prepare_options():
	optp = OptionParser(usage = _('Usage: %prog [options] input_file [input_file(s)]'),\
		version = '%s' % __VERSION__ )
	group_conv = OptionGroup(optp, _('Convert options'),
		_("Options which can be used to properly convert sub files."))
	optp.add_option('-f', '--force',
		action='store_true', dest='force', default=False,
		help=_("force all operations without asking (assuming yes)"))
	optp.add_option('-q', '--quiet',
		action='store_true', dest='quiet', default=False,
		help=_("verbose output"))
	optp.add_option('--debug',
		action='store_true', dest='debug_messages', default=False,
		help=_("Generate debug output"))
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
	group_conv.add_option('-v', '--video-file', default = '',
		action='store', type='string', dest='movie_file',
		help=_("movie file to get fps info from"))
	group_conv.add_option('-x', '--extension',
		action='store', type='string', dest='ext',
		help=_("specify extension of the output file if the default one is not what you like."))

	optp.add_option_group(group_conv)
	return optp

def convert_file(filepath, file_encoding, file_fps, output_format, output_extension = ''):
	cls = SubParser.GenericSubParser.__subclasses__()
	conv = None
	for c in cls:
		# Obtain user specified subclass
		if c.__OPT__ == output_format:
			filename, extension = os.path.splitext(filepath)
			extension = output_extension if output_extension else c.__EXT__
			conv = c(filename + '.' + extension, file_fps, file_encoding)
			break
	if not conv:
		raise NameError

	# Try to detect file encoding
	# 'is' keyword checks objects identity and it's the key to disabling
	# autodetect when '-e ascii' option is given. It seems that optparse
	# creates a new object (which is logical) when given an option from
	# shell and overrides a variable in program memory.
	if IS_CHARDET and file_encoding is 'ascii': 
		fs = os.path.getsize(filepath)
		size = 1400 if fs > 1400 else fs
		with open(filepath, mode='r',) as f:
			rd = f.read(size)
			enc = chardet.detect(rd)
			log.debug(_("Detecting encoding from %d bytes") % len(rd))
			log.debug(_(" ...chardet: %s") % enc)
		if enc['confidence'] > 0.60:
			file_encoding = enc['encoding']
			conv.encoding = file_encoding
			log.debug(_(" ...detected %s encoding.") % enc['encoding'])
		else:
			log.debug(_("I am not too confident about encoding. Skipping check."))

	with codecs.open(filepath, mode='r', encoding=file_encoding) as f:
		file_input = f.readlines()

	lines = []
	log.info(_("Trying to parse %s...") % filepath)
	sub_pair = [None, None]
	for cl in cls:
		if not lines:
			c = cl(filepath, file_fps, file_encoding, file_input)
			for p in c.parse():
				if not sub_pair[1] and conv.__WITH_HEADER__: # Only the first element
					header = p['sub'].get('header')
					if type(header) != dict:
						header = {}
					header = conv.convert_header(header)
					if header:
						lines.append(header.decode(conv.encoding))
				sub_pair[0] = sub_pair[1]
				sub_pair[1] = p
				try:
					if sub_pair[0]:
						if not sub_pair[0]['sub']['time_to']:
							sub_pair[0]['sub']['time_to'] = \
								sub_pair[0]['sub']['time_from'] + \
								(sub_pair[1]['sub']['time_from'] - sub_pair[0]['sub']['time_from']) * 0.85
						s = conv.convert(sub_pair[0])
						lines.append(s.decode(conv.encoding))
					else:
						if sub_pair[1]:
							if not sub_pair[1]['sub']['time_to']:
								sub_pair[1]['sub']['time_to'] = \
									sub_pair[1]['sub']['time_from'] + FrameTime(file_fps, 'ss', seconds = 2.5)
							s = conv.convert(sub_pair[1])
							lines.append(s.decode(conv.encoding))
				except AssertionError:
					log.warning(_("Correct time not asserted for subtitle %d. Skipping it...") % (sub_pair[0]['sub_no']))
					log.debug(_(".. incorrect subtitle pair times: (%s, %s)") % (sub_pair[0]['sub']['time_from'], sub_pair[1]['sub']['time_from']))
	return (conv, lines)

def main():
	MAX_MEGS = 5 * 1048576
	optp = prepare_options()
	(options, args) = optp.parse_args()
	
	if len(args)  < 1:
		log.error(_("Incorrect number of arguments."))
		return -1

	# A little hack to assure that translator won't make a mistake
	_choices = { 'yes': _('y'), 'no': _('n'), 'quit': _('q'), 'backup': _('b') }
	if options.quiet:
		log.setLevel(logging.ERROR)
	else:
		log.setLevel(logging.INFO)
	if options.debug_messages:
		log.setLevel(logging.DEBUG)
	log.addHandler(ch)
	
	for arg in args:
		if not os.path.isfile(arg):
			log.error(_("No such file: %s") % arg)
			continue

		if os.path.getsize(arg) > MAX_MEGS:
			log.warning(_("File '%s' too large.") % arg)
			continue
		
		if options.auto_fps:
			exts = ('.avi', '.mkv', '.mpg', '.mp4', '.wmv')
			if not options.movie_file:
				filename, extension = os.path.splitext(arg)
				for ext in exts:
					f = ''.join((filename, ext))
					if os.path.isfile(f):
						options.fps = mplayer_check(f, options.fps)
						break
			else:
				options.fps = mplayer_check(options.movie_file, options.fps)

		try:
			conv, lines = convert_file(arg, options.encoding, options.fps, options.format, options.ext)
		#except NameError:
	#		log.error(_("'%s' format not supported (or mistyped).") % options.format)
#			return -1
		except UnicodeDecodeError:
			log.error(_("Couldn't handle '%s' given '%s' encoding.") % (arg, options.encoding))
			continue
		except SubParser.SubParsingError, msg:
			log.error(msg)
			continue;

		if lines:
			log.info(_("Parsed."))
			if os.path.isfile(conv.filename):
				choice = ''
				if options.force:
					choice = _choices['yes']
				while( choice not in (_choices['yes'], _choices['no'], _choices['backup'], _choices['quit'])):
					choice = raw_input( _("File '%s' exists. Overwrite? [y/n/b/q] ") % conv.filename)
				if choice == _choices['backup']:
					if conv.filename == arg:
						arg, _mvd = backup(arg)	# We will read from backed up file
						log.info(_("%s backed up as %s") % (_mvd, arg))
					else:
						_bck, conv_filename = backup(conv.filename)
						log.info(_("%s backed up as %s") % (conv.filename, _bck))
				elif choice == _choices['no']:
					log.info(_("Skipping %s") % arg)
					continue
				elif choice == _choices['yes']:
					log.info(_("Overwriting %s") % conv.filename)
				elif choice == _choices['quit']:
					log.info(_("Quitting converting work."))
					return 1
			else:
				log.info("Writing to %s" % conv.filename)
		
			with codecs.open(conv.filename, 'w', encoding=conv.encoding) as cf:
				cf.writelines(lines)
		else:
			log.warning(_("%s not parsed.") % arg)

if __name__ == '__main__':
	main()
