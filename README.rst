Subconvert - movie subtitles converter
======================================

.. image:: https://travis-ci.org/mgoral/subconvert.svg?branch=master
    :target: https://travis-ci.org/mgoral/subconvert

Subconvert is movie subtitles converter and editor aiming to be fast,
lightweight and easy to use. It supports a wide variety of subtitle formats, can
process files in batches and is available both as terminal application and with
a graphical frontend. Most things, like file encoding or movie framerate are
detected automatically so you can just sit and quickly enjoy your lovely
subtitles!

Installation
------------

Install from PYPI
~~~~~~~~~~~~~~~~~

.. code:: shell

    $ pip3 install --user subconvert

Install with tox
~~~~~~~~~~~~~~~~

If you cloned a git repository, you can install Subconvert with help of tox.

.. warning:: If your system has Python version lower than 3.5, you'll need to
   manually install PyQt as it's not available via PYPI.

.. code:: shell

    $ cd subconvert
    $ tox -e venv
    $ ln -s {.venv,$HOME/.local}/bin/subconvert
    $ ln -s {.venv,$HOME/.local}/share/applications/subconvert.desktop


Install with setup.py
~~~~~~~~~~~~~~~~~~~~~

.. warning:: these methods are not recommended for ordinary users as they don't
   manage some dependencies automatically. Installation methods from PYPI or
   with tox are preferable.

You can alternatively create a Python distribution (like bdist_wheel) and
install it:

.. code:: shell

    $ cd subconvert
    $ python3 setup.py bdist_wheel
    $ pip3 install dist/\*.whl

Or install it directly:

.. code:: shell

    $ cd subconvert
    $ python3 setup.py install


Removing
--------

If you installed Subconvert with pip, uninstalling it is simply calling
uninstall:

.. code:: shell

    $ pip3 uninstall subconvert

Otherwise you'll have to manually remove all subconvert files, i.e.:

* ``$prefix/lib/python*/site-packages/subconvert``
* ``$prefix/bin/subconvert``
* ``$prefix/share/applications/subconvert.desktop``
* ``$prefix/share/icons/hicolor/*/apps/aubconvert.{svg,png}``

Usage
-----

.. note:: Most recent usage description is always available by `subconvert
   --help`. You can also refer to the documentation included in ``docs/``
   directory.

You can use graphical or commandline interface. Default subconvert invocation
executes graphical interface. It is an interactive window in which you can
convert and edit movie subtitles.

To access commandline interface, use ``-c`` switch:

.. code:: shell

    $ subconvert -c file1.srt file2.txt

Above invocation will convert file1.srt and file2.txt to the default subtitles
format (which is SubRip). It will create file2.srt and will try to overwrite
file1.srt (don't worry, unless you used ``-f`` switch, Subconvert will first ask
you what to do).

Output filename syntax
~~~~~~~~~~~~~~~~~~~~~~
It's not uncommon to add some kind of prefix/suffix to converted subtitles. Like
this::

    my_subtitles.srt --> converted_my_subtitles.extension

When you specify output filename (via ``-o`` option), you can tell Subconvert to
use input file name base. Subconvert will substitute with it all appearances of
``%f`` in output file name. See an example:

.. code:: shell

    $ ls
    $ file1.srt  file2.txt
    $ subconvert -c file1.srt file2.txt -o "conv_%f.ABC"
    $ ls
    $ conv_file1.ABC  conv_file2.ABC  file1.srt  file2.txt

You can escape "%f" by adding second percent sign ("%"):

.. code:: shell

    $ subconvert -c file1.srt -o "conv_%%f.ABC"
    $ ls
    $ conv_%f.ABC  file1.srt  file2.txt

You can also substitute ``%e``, with original file extension (without a dot
``.``):

.. code:: shell

    $ subconvert -c file1.srt -o "conv_%f.%e_suffix"
    $ ls
    $ conv_file1.srt_suffix  file1.srt  file2.txt

Subtitle Property Files
~~~~~~~~~~~~~~~~~~~~~~~

You can create a common set of subtitle properties and apply all of them at
once. Say, your subtitles are usually iso-8859-4 encoded and you usually convert
them to TMP. You can set those settings with Subtitle Properties Editor
(available via GUI: ``Tools -> Subtitle Properties Editor``) and use them each
time:

.. code:: shell

    $ subconvert -c file1.srt file2.txt -o "~/subs/%f.tmp" -p ~/subs/iso88594_tmp.spf
    $ ls ~/subs
    $ file1.tmp  file2.tmp

Dependencies
------------
* Python 3.4+ (3.5+ is preferred)
* ``python3-pyqt5``
* ``python3-chardet``
* MPlayer

Additionaly, to build Subconvert you'll need:
* setuptools
* pyrcc5 (comes with ``pyqt5-dev-tools``)

To build documentation:
* ``asciidoctor``

License
-------
Subconvert is Free Software, available under terms of GNU General Public License
3, or (at your opinion) any later version. For details see LICENSE.txt which
should be delivered with Subconvert.

.. _AUR: https://aur.archlinux.org/packages/subconvert/
.. _PYPI: https://pypi.python.org/pypi/subconvert
