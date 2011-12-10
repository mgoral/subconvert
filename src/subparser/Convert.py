#-*- coding: utf-8 -*-

import os
import logging
import re
import gettext
import codecs
import datetime
import shutil

from subprocess import Popen, PIPE

import subparser.SubParser as SubParser

try:
	import chardet
	IS_CHARDET = True
except ImportError:
	IS_CHARDET = False


log = logging.getLogger('SubConvert.%s' % __name__)

gettext.bindtextdomain('subconvert', '/usr/lib/subconvert/locale')
gettext.textdomain('subconvert')
_ = gettext.gettext


def backup( filename ):
	new_arg = filename + datetime.datetime.now().strftime('_%y%m%d%H%M%S')
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


