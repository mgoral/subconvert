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
import sys
import codecs
import locale
import logging
import optparse
import gettext

import subparser.SubParser as SubParser
import subparser.Convert as Convert
import subutils.version as version
import subutils.path as subpath
import subutils.suboptparse as suboptparse

t = gettext.translation(
    domain='subconvert',
    localedir=subpath.get_locale_path(__file__),
    fallback=True)
gettext.install('subconvert')
_ = t.ugettext

MAX_MEGS = 5 * 1048576


def prepare_options():
    """Define optparse options."""

    optp = suboptparse.SubOptionParser(
        usage = _('Usage: %prog [options] input_file [input_file(s)]'),
        version = '%s' % version.__version__,
        formatter = suboptparse.SubHelpFormatter()
    )

    group_file = optparse.OptionGroup(optp, _('File options'),
        _("Options that describe how subtitle files should be handled."))
    group_movie = optparse.OptionGroup(optp, _('Movie options'),
        _("Options that describe the corelations between subtitle and movie files."))

    optp.group_general.add_option('-f', '--force',
        action='store_true', dest='force', default=False,
        help=_("Force all operations without asking (assuming yes)."))
    optp.group_general.add_option('-q', '--quiet',
        action='store_true', dest='quiet', default=False,
        help=_("Silence SubConvert output."))
    optp.group_general.add_option('-g', '--gui',
        action='store_true', dest='run_gui', default=False,
        help=_("Execute Subconvert in graphical mode."))
    optp.group_general.add_option('--debug',
        action='store_true', dest='debug_messages', default=False,
        help=_("Generate debug output."))

    group_file.add_option('-e', '--encoding',
        action='store', type='string', dest='encoding', default=None,
        help=_("Input file encoding. If no encoding is provided, SubConvert will try to automatically detect file encoding and switch to 'UTF-8' when unsuccessfull. For a list of available encodings, see: http://docs.python.org/library/codecs.html#standard-encodings."))
    group_file.add_option('--output-encoding',
        action='store', type='string', dest='output_encoding', default=None,
        help=_("Output file encoding. If no output encoding is provided, SubConvert will save output files with the same encoding as input."))
    group_file.add_option('-t', '--format',
        action='store', type='string', dest='format_', default = 'subrip',
        help=_("Output subtitle format. Default: subrip."))
    group_file.add_option('-x', '--extension',
        action='store', type='string', dest='ext',
        help=_("Specify extension of the output file if the default one is not what you like."))

    group_movie.add_option('--fps',
        action='store', type='float', dest='fps', default = 25,
        help=_("Movie/subtitles frames per second. Default: 25."))
    group_movie.add_option('-A', '--auto-fps',
        action='store_true', dest='auto_fps', default=False,
        help=_("Automatically try to get fps from MPlayer."))
    group_movie.add_option('-v', '--video', default = '',
        action='store', type='string', dest='movie_file',
        help=_("Movie file to get FPS info from."))

    optp.add_option_group(optp.group_general)
    optp.add_option_group(group_file)
    optp.add_option_group(group_movie)
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

    if options.run_gui is True:
        import subconvert_gui
        subconvert_gui.start_app(args, None)
        return 0

    if len(args)  < 1:
        log.error(_("Incorrect number of arguments."))
        return 1

    # A little hack to ensure that translator won't make a mistake
    _choices = { 'yes': _('y'), 'no': _('n'), 'quit': _('q'), 'backup': _('b') }

    for arg in args:
        arg = arg.decode(locale.getpreferredencoding())
        if not os.path.isfile(arg):
            log.error(_("No such file: %s") % arg)
            continue

        if os.path.getsize(arg) > MAX_MEGS:
            log.warning(_("File '%s' too large.") % arg)
            continue

        if options.auto_fps or options.movie_file:
            if not options.movie_file:
                filename = os.path.splitext(arg)[0]
                for ext in ('.avi', '.mkv', '.mpg', '.mp4', '.wmv', '.rmvb', '.mov', '.mpeg'):
                    if os.path.isfile(''.join((filename, ext))):
                        options.fps = Convert.mplayer_check(''.join((filename, ext)), options.fps)
                        break
                    elif os.path.isfile(''.join((filename, ext.upper()))):
                        options.fps = Convert.mplayer_check(''.join((filename, ext.upper())), options.fps)
                        break
            else:
                options.fps = Convert.mplayer_check(options.movie_file, options.fps)
        elif options.fps <= 0:
            log.warning(_("Incorrect FPS value: %s. Switching back to default") % options.fps)
            options.fps = 25;

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
                    choice = raw_input(
                        _("File '%s' exists. Overwrite? [%s/%s/%s/%s] ").encode(sys.stdin.encoding) %
                        ( conv.filename.encode(sys.stdin.encoding),
                        _choices['yes'].encode(sys.stdin.encoding),
                        _choices['no'].encode(sys.stdin.encoding),
                        _choices['backup'].encode(sys.stdin.encoding),
                        _choices['quit'].encode(sys.stdin.encoding) )
                        )
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
                log.info(_("Writing to %s") % conv.filename)

            with codecs.open(conv.filename, 'w', encoding=conv.encoding) as output_file:
                output_file.writelines(lines)
        else:
            log.warning(_("%s not parsed.") % arg)
