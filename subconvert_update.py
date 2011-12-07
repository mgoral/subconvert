#!/usr/bin/env python
#-*- coding: utf-8 -*-

import urllib
import zipfile
import gettext
import os
import sys
import shutil
import re
from subprocess import Popen, PIPE
from datetime import datetime as dt
from optparse import OptionParser, OptionGroup

_ = gettext.gettext
ZIPFILE = "%s_%s.%s" % ('subconvert', dt.now().strftime("D%Y%m%%dT%H%M%S%f"), 'zip')

def cleanup(zip_path, extract_path):
	print _("Cleanup:")
	print _(" ...removing zipball")
	os.remove(zip_path)
	print _(" ...removing temporary extract directory")
	shutil.rmtree(extract_path)

def extract(zip_path,extract_path):
	if zipfile.is_zipfile(zip_path):
		print _(" ...extracting zipball")
		with zipfile.ZipFile(zip_path, 'r') as zf:
			members = zf.infolist()
			for member in members:
				if os.path.split(member.filename)[1] == 'subconvert.py':
					new_subconvert = member.filename
				elif os.path.split(member.filename)[1] == 'setup.py':
					setup_file = member.filename
				zf.extract(member, extract_path)

		try:
			new_subconvert = os.path.join(extract_path, new_subconvert)
		except NameError:
			print _("ERROR: subconvert.py not found in a zipball")
			return -1
		try:
			setup_file = os.path.join(extract_path, setup_file)
		except NameError:
			print _("ERROR: setup.py not found in a zipball")
			return -1
	else:
		print _("ERROR: '%s' is not correct zip file (or it is corrupted)") % ZIPFILE
		return -1
	return (setup_file, new_subconvert)


def check_versions(new_subconvert):
	try:
		command = ["subconvert", "--version"]
		v1 = Popen(command, stdout=PIPE).communicate()[0]
		print _(" ...current SubConvert version: %s") % v1.strip()
	except OSError:
		v1 = "unknown"

	command = ['python', new_subconvert, '--version']
	v2 = Popen(command, stdout=PIPE).communicate()[0]

	v1 = re.findall(r'\d+', v1)
	v2 = re.findall(r'\d+', v2)
	v1.reverse()
	v2.reverse()

	ver1 = 0
	ver2 = 0
	mult = 1
	for no in v1:
		ver1 += mult * int(no)
		mult *= 10
	mult = 1
	for no in v2:
		ver2 += mult * int(no)
		mult *= 10
		
	if ver1 < ver2:
		return 0
	else:
		return 1

def prepare_options():
	optp = OptionParser(usage = _('Usage: %prog [options]'))
	optp.add_option('--dir',\
		action='store', type='string', dest='scriptdir', default='',\
		help=_("install directory"))
	optp.add_option('--base-dir',\
		action='store', type='string', dest='prefix', default='',\
		help=_("python site-packages dir to install original scripts"))
		
	return optp

def main():
	optp = prepare_options()
	(options, args) = optp.parse_args()

	print _("Starting SubConvert Updater")

	path = os.path.split(os.path.realpath(__file__))[0]
	if len(sys.argv) > 1:
		if os.path.isdir(sys.argv[1]):
			path = sys.argv[1]
	zip_path = os.path.join(path, ZIPFILE)
	extract_path = os.path.join(path, 'subc_tmp')
	print _(" ...working directory: %s") % path

	print _(" ...downloading zipball to %s") % zip_path
	urllib.urlretrieve("https://github.com/virgoerns/subconvert/zipball/master", zip_path)

	try:
		setup_file, new_subconvert = extract(zip_path, extract_path)
	except TypeError:
		cleanup()
		return -1

	if check_versions(new_subconvert):
		print _("You have the latest version of SubConvert installed. No need to update.")
		cleanup(zip_path, extract_path)
		return 0
	else:
		print _(" ...newer version found. Executing installer\n")
		print "++++++++++++ [ SETUP LOG ] +++++++++++++"
		command = ['python', setup_file, 'install']
		if options.prefix:
			command.extend(['--prefix', options.prefix])
		if options.scriptdir:
			command.extend(['--install-scripts', options.scriptdir])
		Popen(command).communicate()
		print "++++++++++++ [ SETUP LOG END ] +++++++++++++\n"
		print _("Update process finished (but there might be some errors which are not handled by updater).")
		cleanup(zip_path, extract_path)
		print _("Bye bye!")
		return 0

if __name__ == '__main__':
	main()
