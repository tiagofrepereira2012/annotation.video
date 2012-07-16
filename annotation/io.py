#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Fri 29 Jun 2012 13:42:57 CEST 

"""A set of utilities and library functions to handle keypoint annotations."""

import os

def save(data, fp, backup=False, fs=" "):
  """Saves a given data set to a file
  
  Parameters

  data
    A dictionary where the keys are frame numbers and the values are lists of
    tuples indicating each of the keypoints in (x, y)

  fp
    The name of a file, with full path, to be used for recording the data or an     already opened file-like object, that accepts the "write()" call.

  backup
    If set, backs-up a possibly existing file path before overriding it. Note
    this is not valid in case 'fp' above points to an opened file.

  fs
    The field separator to use. A single space by default.
  """

  if isinstance(fp, (str, unicode)):

    if backup and os.path.exists(fp):
      bname = fp + '~'
      if os.path.exists(bname): os.unlink(bname)
      os.rename(fp, bname)

    fp = open(fp, 'wt')

  frame_tmpl = "%d"
  coord_tmpl = "%d %d"
  rs = '\n'

  for key in sorted(data.iterkeys()):

    fp.write(frame_tmpl % key)

    for coord in data[key]: fp.write((fs + coord_tmpl) % tuple(coord))

    fp.write(rs)

def load(fp, fs=" "):
  """Loads a given data set from a file, returning a dictionary with annotations

  Parameters

  fp
    The name of a file, with full path, to be used for recording the data or an     already opened file-like object, that accepts the "read()" call.

  fs
    The field separator to use. A single space by default.
  """

  if isinstance(fp, (str, unicode)): fp = open(fp, 'rt')

  import csv

  r = csv.reader(fp, delimiter=fs)

  retval = {}

  for entry in r:
    retval[int(entry[0])] = zip([int(k) for k in entry[1::2]], 
        [int(k) for k in entry[2::2]])

  return retval
