# PROGRAM OPTIONS

The most simple Subconvert call contains only list of files to be opened:

    $ subconvert [FILE [FILE ...]]

Above call is the most complex call that starts [graphical interface][gui]
(although it also can be started without specifying any files).  If you'd like
to perform a quick converting task however, you have to add `-c` switch:

    $ subconvert -c FILE [FILE ...]

Now there are some additional options available.

## Specify output files

    -o FILE, --output-file FILE

By default Subconvert tries to overwrite subtitle files. You can change all your
work to a different (or completely new) file by specifying it with `-o` option,
followed by so-called [output file syntax][faq]. It can be as simple as a
single file name, but in that case Subconvert will try to write each file to a
given output file.

If output file already exists (and unless `-f` option is on), Subconvert will
fall back to interactive mode and ask you what to do next (overwrite, backup,
skip that file or cancel all operations).

Examples:

    $ subconvert -c sub.srt -o sub.txt                        # results with sub.txt
    $ subconvert -c sub1.srt sub2.txt -o prefix_%f.%e_suffix  # results with prefix_sub1.srt_suffix

## Change subtitles format

    -t FMT, --format FMT

Probably the most important Subconvert feature (the one it got its name from) is
*converting* from one type of subtitles to the other one (like from Subrip to
Micro DVD). While input file format is automatically detected, to change it you
have to name it.  All newly created files will be saved in a specified format.
If this option is not used, subtitles format won't be changed from the original
one.

For a list of available subtitle formats, see [available formats][av-fmts] page.

There are several available subtitle formats. Each of them has a specific code
that can be used. For a list consult the [available formats][av-fmts] page.

Examples:

    $ subconvert -c sub.srt -t subviewer

## Specify or change file encoding

    -e IN_ENC, --encoding IN_ENC
    -E OUT_ENC, --reencode OUT_ENC

By default Subconvert will try to automatically detect subtitle encodings and
keep it for output files. But detecting file encodings is quite hard (really, it
is!), so it might detect it incorrectly or not detect it at all and fall back to
the default one. If you'd like to force input file encoding, you can use `-e`
option.

On the other hand, you might want to change the output file encoding. To do
that, use `-E` option (capital "E").

Note that those two options are independent, so you can auto detect input
encoding and change it to desired one. Just remember that it might be impossible
to convert one encoding to another one (like Japanese to Latin), so use these
options with caution.

If you are unsure about encodings you'd like to use, it's probably the best to
run graphical interface and experiment with encodings to find a correct one
(i.e. the one without silly characters in your subtitles).

See also: [list of available encodings][enc]

Examples:

    $ subconvert -c -e windows-1250 -E iso-885902 sub.srt

## Use Property File

    -p PFILE, --property-file PFILE

Property Files is a nice feature that allows you to easily use frequently used
options. Say, most of time you convert subtitles to a one specific encoding and
format. It means that each time you'd have to type those options by hand (or
create an alias). With Property Files you don't have to do that because you can
group these options in a single file and ask Subconvert to use it instead. For
more informations see [Property Files][pfile] page.

Examples:

    $ subconvert -c -p my_properties.spf subtitles.txt

## Specify number of frames

    -A, --auto-fps
    --fps NO
    -v VIDEO, --video VIDEO

Without FPS value converting between time-based and frame-based subtitles (e.g.
Subrip -> Micro DVD) is impossible. That's why Subconvert employs several
methods of obtaining this crucial value from a movie associated with subtitles.

By default Subconvert won't try to find number of movie frames but will use some
default number instead. If you wish to manually pass this value to Subconvert,
you'll have to use `--fps` switch. Let's say that you'd like to use '23.976' as
your FPS value:

    $ alias subconvert="subconvert -t microdvd" # assume for all examples
                                                # in this section that we'd like
                                                # to convert from subrip to microdvd

    $ subconvert -c --fps 23.976 subtitles.srt

This method is tedious and error prone (you'd have to use another program to get
FPS). That's why you can specify a movie file for each of your subtitles. What
is more, you can use similar syntax to the "output file syntax" (see above):
`%f` will be replaced with a subtitle file name and `%e` with extension
(although using %e is not very useful):

    $ subconvert -c -v "%f.avi" sub1.srt sub2.srt  # will search for
                                                   # sub1.avi and sub2.avi

    # subconvert -c -v common_video.avi sub1.srt sub2.srt  # for both subtitles
                                                           # FPS of common_video.avi
                                                           # will be used

But probably the most common case is when subtitles and a video share a file
name (and are placed in the same directory). In this case you can simply use
`-A` option and Subconvert will try to automatically find a video matching your
subtitles:

    $ ls
    sub1.avi  sub1.srt  sub2.srt  sub2.mp4  sub3.srt  sub3.mpg

    $ subconvert -c *.srt -A  # will match and get FPS this way:
                              # sub1.srt -> sub1.avi
                              # sub2.srt -> sub2.mp4
                              # sub3.srt -> sub3.mpg

## Other options:

    -f, --force  assume 'yes' when Subconvert would normally ask for your
                 permission (e.g. whether to overwrite existing file or not)

    --debug      show some debug prints. Useful for developer or when issuing a
                 bug.

    --quiet      the opposite of '--debug'. Subconvert will print only when 
                 there's a critical error of some kind.

    --help       displays a built-in help with a summary of all Subconvert
                 options.

    --version    displays used version of Subconvert

  [faq]: ../faq.md
  [gui]: gui.md
  [av-fmts]: available-formats.md
  [enc]: encodings.md
  [pfile]: property-files.md


<!-- vim: set tw=80 colorcolumn=81 : -->
