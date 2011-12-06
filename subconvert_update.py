#!/usr/bin/env python
#-*- coding: utf-8 -*-

import urllib
import zipfile
import gettext
import os
import sys
import shutil
from subprocess import Popen, PIPE
from datetime import datetime as dt

_ = gettext.gettext
ZIPFILE = "%s_%s.%s" % ('subconvert', dt.now().strftime("D%Y%m%%dT%H%M%S%f"), 'zip')

def main():
	print _("Starting SubConvert Updater")

	path = os.path.split(os.path.realpath(__file__))[0]
	if len(sys.argv) > 1:
		if os.path.isdir(sys.argv[1]):
			path = sys.argv[1]
	zip_path = os.path.join(path, ZIPFILE)
	print _(" ...working directory: %s") % path

	command = ["subconvert", "--version"]
	v1 = Popen(command, stdout=PIPE).communicate()[0]

	print _(" ...current SubConvert version: %s") % v1.strip()
	
	print _(" ...downloading zipball to %s") % zip_path

	urllib.urlretrieve("https://github.com/virgoerns/subconvert/zipball/master", zip_path)

	if zipfile.is_zipfile(zip_path):
		extract_path = os.path.join(path, 'subc_tmp')
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

		command = ['python', new_subconvert, '--version']
		v2 = Popen(command, stdout=PIPE).communicate()[0]

		if v1.strip() == v2.strip():
			print _("You have the latest version of SubConvert installed. No need to update.")
			return 0
		else:
			print _(" ...newer version found. Executing installer\n")
			print "++++++++++++ [ SETUP LOG ] +++++++++++++"
			command = ['python', setup_file, 'install']
			Popen(command).communicate()
			print "++++++++++++ [ SETUP LOG END ] +++++++++++++\n"

			print _("Update process finished (but there might be some errors which are not handled by updater).")
			print _("Cleanup:")
			print _(" ...removing zipball")
			os.remove(zip_path)
			print _(" ...removing temporary extract directory")
			shutil.rmtree(extract_path)
			print _("This was a triumph. Bye bye!")
			return 0
	else:
		print _("ERROR: '%s' is not correct zip file (or it is corrupted)") % ZIPFILE
		return -1

if __name__ == '__main__':
	main()
