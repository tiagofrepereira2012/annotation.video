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

def check_input(data, header, shape):
  """Checks the input data for inconsistencies w.r.t. the input video
  shape.
  
  Parameters

  data
    The input data, as read by load()

  header
    The header tags

  shape
    The input video shape in the format (no_frames, height, width)
  """

  # checks that the overall length is OK
  if max(data.keys()) >= shape[0]:
    raise RuntimeError, 'Input data has too many frames - detected index = %d, but input video has only %d frames' % (max(data.keys()), shape[0])

  # checks that each individual keypoint is OK
  for frame in sorted(data.keys()):

    for i, (x,y) in enumerate(data[frame]):

      if x >= shape[2]:
        raise RuntimeError, 'Input data at frame %d for keypoint "%s" has an "x" value (%d) greater or equal the video width (%d)' % (frame, header[i], x, shape[2])
      if y >= shape[1]:
        raise RuntimeError, 'Input data at frame %d for keypoint "%s" has an "y" value (%d) greater or equal the video height (%d)' % (frame, header[i], y, shape[1])

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
  elif len(r[0]) != len(r[1]):
    print r[0]
    raise RuntimeError, "row 0 has a different length (%d) from row 1 (%d), but not quite as to make it a header - please verify" % (len(r[0]), len(r[1]))

  for i, entry in enumerate(r):
    data[int(entry[0])] = zip([int(k) for k in entry[1::2]],
        [int(k) for k in entry[2::2]])
    skeys = sorted(data.iterkeys())
    if i == 0:
      if header is not None:
        # check data[0] against header
        if len(data[skeys[i]]) != len(header):
          raise RuntimeError, "row 0 has different length (%d) than header (%d)" % (len(data[skeys[i]]), len(header))
      continue
    else:
      # checks data[i] against data[i-1]
      if len(data[skeys[i]]) != len(data[skeys[i-1]]):
        raise RuntimeError, "row %d has different length (%d) than its predecessor (%d)" % (i, len(data[skeys[i]]), len(data[skeys[i-1]]))

  if header is None: 
    header = [str(k) for k in range(len(data[min(data.keys())]))]

  return (data, header)
