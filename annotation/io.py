#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Fri 29 Jun 2012 13:42:57 CEST 

"""A set of utilities and library functions to handle keypoint annotations."""

import os

def save(data, fp, header=None, backup=False, fs=" "):
  """Saves a given data set to a file
  
  Parameters

  data
    A dictionary where the keys are frame numbers and the values are lists of
    tuples indicating each of the keypoints in (x, y)

  fp
    The name of a file, with full path, to be used for recording the data or an     already opened file-like object, that accepts the "write()" call.

  header
    If set, should be a python iterable with the names of each (double) column
    in the annotation file. In this case, this will be the first entry in the
    annotation file output.

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
  coord_tmpl = "%d" + fs + "%d"
  rs = '\n'

  if header is not None:
    fp.write(fs.join(header) + rs)

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

  Returns the loaded data as a tuple (data, header). If there is no header,
  then the entry in the output data is set a sequence of numbers (as strings),
  starting from '0' (e.g. ['0', '1', '2', '3'], for a 4-keypoint
  configuration).
  """

  if isinstance(fp, (str, unicode)): fp = open(fp, 'rt')

  import csv

  # load all file at once
  r = list(csv.reader(fp, delimiter=fs))

  data = {}
  header = None

  if len(r[0]) == ((len(r[1])-1)/2):
    header = r[0]
    del r[0]

  for i, entry in enumerate(r):
    data[int(entry[0])] = zip([int(k) for k in entry[1::2]],
        [int(k) for k in entry[2::2]])
    if i == 0: 
      if header is not None:
        # check data[0] against header
        if len(data[i]) != len(header):
          raise RuntimeError, "row 0 has different length (%d) than header (%d)" % (len(data[i]), len(header))
      continue
    else:
      # checks data[i] against data[i-1]
      if len(data[i]) != len(data[i-1]):
        raise RuntimeError, "row %d has different length (%d) than its predecessor (%d)" % (i, len(data[i]), len(data[i-1]))

  if header is None: 
    header = [str(k) for k in range(len(data[min(data.keys())]))]

  return (data, header)
