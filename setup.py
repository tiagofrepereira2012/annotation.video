#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
#  Mon 25 Jun 2012 13:21:06 CEST

from setuptools import setup, find_packages

# The only thing we do in this file is to call the setup() function with all
# parameters that define our package.
setup(

    name='annotation.video',
    version='1.0',
    description='Annotation tool for video streams',
    url='http://github.com/bioidiap/annotation.video',
    license='LICENSE.txt',
    author_email='Andre Anjos <andre.anjos@idiap.ch>',
    #long_description=open('doc/howto.rst').read(),

    # This line is required for any distutils based packaging.
    packages=find_packages(),

    install_requires=[
        "bob",      # base signal proc./machine learning library
        "argparse", # better option parsing
        "PIL",      # for ImageTK
    ],

    entry_points={
      'console_scripts': [
        'annotate = annotation.script.annotate:main',
        'play = annotation.script.play:main',
        ],
      },

)
