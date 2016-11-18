Subconvert - movie subtitles converter.
====================

[![Build Status](https://travis-ci.org/mgoral/subconvert.svg?branch=master)](https://travis-ci.org/mgoral/subconvert)

Subconvert is movie subtitles converter and editor aiming to be fast,
lightweight and easy to use. It supports a wide variety of subtitle formats, can
process files in batches and is available both as terminal application and with
a graphical frontend. Most things, like file encoding or movie framerate are
detected automatically so you can just sit and quickly enjoy your lovely
subtitles!

## Installation
*Arch users: you can install Subconvert from [AUR][aur].*

Since a version 1.0.0, autotools have been introduced. Most probably, they are already installed on
your system. If not, install `automake` and `autoconf`.

From now on we'll suppose that you changed directory to the one in which this `README.md` file is
located.

To create Subconvert build system, run:

```
$ ./autogen.sh
```

*Note: above command creates a bunch of files. If you ever want do remove all of them, just use
git: `git clean -f -d`.*

Now it's time to configure your build/installation. You do this via `configure` script (see
`./configure --help` for details). The most common option is to change prefix, i.e. a directory
where Subconvert will be installed. Suppose that you would like to install Subconvert into
`~/.local/share/subconvert`. Your prefix in that case will be `${HOME}/.local`. It is a parent
directory for `share`, `bin`, `lib`, etc. Default prefix (the one used when you don't specify
`--prefix`) is `/usr`. *Note: you'll need a root access to install Subconvert into /usr.*

Suppose you want to use `~/.local` prefix:

```
$ ./configure --prefix ${HOME}/local
```

To build and install Subconvert:

```
$ make
$ make install
```

*Note: If you have previous Subconvert installation, remove it first: `make reinstall`.*

If `${prefix}/bin` isn't in your $PATH, you might consider adding Subconvert to it:

```
$ mkdir -p ${HOME}/bin
$ cd ${HOME}/bin && ln -s ${prefix}/bin/subconvert
```

## Removing
To remove Subconvert, proceed with Installation steps. After invoking `configure` script (with a
correct Subconvert prefix), simply run:

```
$ make uninstall
```

## Usage
*Note: Most recent usage description is always available by `subconvert --help`. There are also
[wiki pages][wiki] that describe some aspects of Subconvert usage more precisely.*

You can use graphical or commandline interface. Default subconvert invocation executes graphical
interface. It is an interactive window in which you can convert and edit movie subtitles. It's
described more thoroughly on Subconvert [wiki][wiki-gui].

To access commandline interface, use `-c` switch:

```
$ subconvert -c file1.srt file2.txt
```

Above invocation will convert file1.srt and file2.txt to the default subtitles format (which is
SubRip). It will create file2.srt and will try to overwrite file1.srt (don't worry, unless you used
`-f` switch, Subconvert will first ask you what to do).

### Output filename syntax
It's not uncommon to add some kind of prefix/suffix to converted subtitles. Like this:

```
my_subtitles.srt --> converted_my_subtitles.extension
```

When you specify output filename (via `-o` option), you can tell Subconvert to use input file name
base. Subconvert will substitute with it all appearances of `%f` in output file name. See an
example:

```
$ ls
$ file1.srt  file2.txt
$ subconvert -c file1.srt file2.txt -o "conv_%f.ABC"
$ ls
$ conv_file1.ABC  conv_file2.ABC  file1.srt  file2.txt
```

You can escape "%f" by adding second percent sign ("%"):
```
$ subconvert -c file1.srt -o "conv_%%f.ABC"
$ ls
$ conv_%f.ABC  file1.srt  file2.txt
```

You can also substitute `%e`, with original file extension (without a dot `.`):

```
$ subconvert -c file1.srt -o "conv_%f.%e_suffix"
$ ls
$ conv_file1.srt_suffix  file1.srt  file2.txt
```

### Subtitle Property Files
You can create a common set of subtitle properties and apply all of them at once. Say, your
subtitles are usually iso-8859-4 encoded and you usually convert them to TMP. You can set those
settings with Subtitle Properties Editor (available via GUI: `Tools -> Subtitle Properties Editor`)
 and use them each time:

```
$ subconvert -c file1.srt file2.txt -o "~/subs/%f.tmp" -p ~/subs/iso88594_tmp.spf
$ ls ~/subs
$ file1.tmp  file2.tmp
```

## Dependencies
* Python 3.2+
* python3-pyqt5
* python3-chardet
* MPlayer
* gettext

Additionaly, to build and install Subconvert you'll need:
* autotools (autoconf + automake)
* intltool
* pyrcc5 (comes with pyqt5-dev-tools)

To build documentation:
* asciidoctor

## License
Subconvert is free software, available under terms of GNU General Public License 3. For details see
`License.txt` which should be delivered with Subconvert.

[wiki]: https://github.com/mgoral/subconvert/wiki
[wiki-gui]: https://github.com/mgoral/subconvert/wiki/Graphical-User-Interface
[aur]: https://aur.archlinux.org/packages/subconvert/
