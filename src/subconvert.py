#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
This file is part of SubConvert.

SubConvert is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SubConvert is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SubConvert.  If not, see <http://www.gnu.org/licenses/>.
"""


import os
import codecs
import logging
from optparse import OptionParser, OptionGroup
import gettext

import subparser.SubParser as SubParser
import subparser.Convert as Convert
import subparser.version as version

t = gettext.translation('subconvert', '/usr/share/locale')
gettext.install('subconvert')
_ = t.ugettext

MAX_MEGS = 5 * 1048576


def prepare_options():
    """Define optparse options."""
    optp = OptionParser(usage = _('Usage: %prog [options] input_file [input_file(s)]'), \
        version = '%s' % version.__version__ )
    group_conv = OptionGroup(optp, _('Convert options'),
        _("Options which can be used to properly convert sub files."))
    optp.add_option('-f', '--force',
        action='store_true', dest='force', default=False,
        help=_("force all operations without asking (assuming yes)"))
    optp.add_option('-q', '--quiet',
        action='store_true', dest='quiet', default=False,
        help=_("quiet output"))
    optp.add_option('--debug',
        action='store_true', dest='debug_messages', default=False,
        help=_("Generate debug output"))
    group_conv.add_option('-e', '--encoding',
        action='store', type='string', dest='encoding', default=None,
        help=_("input file encoding. If no encoding is provided, SubConvert will try to automatically detect file encoding and switch to 'UTF-8' when unsuccessfull. For a list of available encodings, see: http://docs.python.org/library/codecs.html#standard-encodings"))
    group_conv.add_option('-E', '--output-encoding',
        action='store', type='string', dest='output_encoding', default=None,
        help=_("output file encoding. If no output encoding is provided, SubConvert will save output files with the same encoding as input."))
    group_conv.add_option('-m', '--format',
        action='store', type='string', dest='format_', default = 'subrip',
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

def main():
    """Main SubConvert function"""
    optp = prepare_options()
    (options, args) = optp.parse_args()

    log = logging.getLogger('SubConvert')

    if options.quiet:
        log.setLevel(logging.ERROR)
    else:
        log.setLevel(logging.INFO)
    if options.debug_messages:
        log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())

    if len(args)  < 1:
        log.error(_("Incorrect number of arguments."))
        return 1

    # A little hack to assure that translator won't make a mistake
    _choices = { 'yes': _('y'), 'no': _('n'), 'quit': _('q'), 'backup': _('b') }

    for arg in args:
        if not os.path.isfile(arg):
            log.error(_("No such file: %s") % arg)
            continue

        if os.path.getsize(arg) > MAX_MEGS:
            log.warning(_("File '%s' too large.") % arg)
            continue
        
        if options.auto_fps:
            if not options.movie_file:
                filename = os.path.splitext(arg)[0]
                for ext in ('.avi', '.mkv', '.mpg', '.mp4', '.wmv'):
                    if os.path.isfile(''.join((filename, ext))):
                        options.fps = Convert.mplayer_check(''.join((filename, ext)), options.fps)
                        break
            else:
                options.fps = Convert.mplayer_check(options.movie_file, options.fps)

        encoding = Convert.detect_encoding(arg, options.encoding)

        output_encoding = options.output_encoding
        if output_encoding is None:
            output_encoding = encoding
        log.debug( _("Input file encoding: %s.") % encoding)
        log.debug( _("Output file encoding: %s.") % output_encoding)

        try:
            conv, lines = Convert.convert_file(arg, encoding, output_encoding, options.fps, options.format_, options.ext)
        except NameError, msg:
            log.error(_("'%s' format not supported (or mistyped).") % options.format_)
            log.debug(msg)  # in case some other Name Error occured (i.e. while refactoring)
            return 1
        except LookupError, msg:
            log.error(msg)
            return 1
        except UnicodeDecodeError:
            log.error(_("Couldn't handle '%s' given '%s' encoding.") % (arg, encoding))
            continue
        except UnicodeEncodeError:
            log.error(_("Couldnt convert from '%s' encoding to '%s'") % (encoding, options.output_encoding))
            continue
        except SubParser.SubParsingError, msg:
            log.error(msg)
            continue

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
                        arg, _mvd = Convert.backup(arg) # We will read from backed up file
                        log.info(_("%s backed up as %s") % (_mvd, arg))
                    else:
                        _bck = Convert.backup(conv.filename)[0]
                        log.info(_("%s backed up as %s") % (conv.filename, _bck))
                elif choice == _choices['no']:
                    log.info(_("Skipping %s") % arg)
                    continue
                elif choice == _choices['yes']:
                    log.info(_("Overwriting %s") % conv.filename)
                elif choice == _choices['quit']:
                    log.info(_("Quitting converting work."))
                    return 0
            else:
                log.info("Writing to %s" % conv.filename)
        
            with codecs.open(conv.filename, 'w', encoding=conv.encoding) as output_file:
                output_file.writelines(lines)
        else:
            log.warning(_("%s not parsed.") % arg)

if __name__ == '__main__':
    main()
