Video Key Point Annotation Tool
===============================

.. todo::

  Write intro

Installation
------------

To follow these instructions locally you will need a local copy of this
package. Start by cloning this project with something like (shell commands are
marked with a ``$`` signal)::

  $ git clone --depth=1 https://github.com/bioidiap/annotation.git
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

Usage
-----

Please refer to the documentation inside the ``doc`` directory of this package
for further instructions on the functionality available.

Reference
---------

If you need to cite this work, please contact us.
