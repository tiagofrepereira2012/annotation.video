Video Key Point Annotation Tool
===============================

A small TkInter-based keypoint annotation tool for videos written in Python.

Installation
------------

To follow these instructions locally you will need a local copy of this
package. Start by cloning this project with something like (shell commands are
marked with a ``$`` signal)::

  $ git clone --depth=1 https://github.com/bioidiap/annotation.video.git
  $ cd annotation
  $ rm -rf .git # you don't need the git directories...

Installation of the toolkit uses the `buildout <http://www.buildout.org/>`_
build environment. You don't need to understand its inner workings to use this
package. Here is a recipe to get you started::
  
  $ python bootstrap.py
  $ ./bin/buildout

These 2 commands should download and install all non-installed dependencies and
get you a fully operational test and development environment.

.. note::

  The python shell used in the first line of the previous command set
  determines the python interpreter that will be used for all scripts developed
  inside this package. Because this package makes use of `Bob
  <http://idiap.github.com/bob>`_, you must make sure that the ``bootstrap.py``
  script is called with the **same** interpreter used to build Bob, or
  unexpected problems might occur.

  If Bob is installed by the administrator of your system, it is safe to
  consider it uses the default python interpreter. In this case, the above 3
  command lines should work as expected. If you have Bob installed somewhere
  else on a private directory, edit the file ``localbob.cfg`` and use that
  with ``buildout`` instead::

    $ python boostrap.py
    $ # edit localbob.cfg
    $ ./bin/buildout -c localbob.cfg

Annotation format
-----------------

The annotation file is composed of an (optional) header followed by rows with
the frame number and `x` and `y` point coordinates. Numbers are all 0-based.
The first frame of a video sequence is numbered 0, as well as the first row or
column of a frame. The record (number) separator is a space and the field (row)
separator is a new-line character. The resulting file can be read and parsed by
most CSV parsers available freely on the internet. 

If a header line is available, it should have length equal to (N-1)/2 where N 
is the number of entries in a non-header line.

Here is a 4-point annotation example::

  OutR InR InL OutL
  0 130 87 146 86 171 86 186 86
        
Usage
-----

To start using the current infrastructure, you need to generate a base keypoint
configuration set like the one bellow::

  OutR InR InL OutL
  0 130 87 146 86 171 86 186 86
 
Save these contents at a file named, for instance, ``config.txt``. To start a
new annotation session, use the ``annotate.py`` program::

  $ bin/annotate.py --output=annotations.txt example/video.avi example/config.txt

The program will load the video file and display the first frame with the
annotations as defined on ``config.txt`` preloaded. Read the help message of
``annotate.py`` (with ``annotate.py --help``) for more instructions on how
key/mouse bindings and how to operate that program properly.

After a successful annotation session, the file ``annotations.txt`` should be
filled with all the frames that you have touched during the annotation process.
It is not customary, but entirely possible, to annotate every frame in a video
sequence. Normally, one annotates a few frames only. After this sparse
annotation, it is possible to fill in the gaps using the application
``postproc.py``, that can either interpolate the annotations or just take the
closest one from the past. The following command line will interpolate the
previous output annotations and generate a new annotation file
(``interpolated.txt``)::

  $ bin/postproc.py example/video.avi example/annotations.txt interpolated.txt

The program ``replay.py`` can read the original video and annotation file and
generate a new video with (yellow) markings on annotated keypoints::

  $ bin/replay.py example/video.avi example/interpolated.txt annotated.avi

You can play with options for all the above cited programs and fine-tune the
behavior of the annotation procedure to suit your needs.
