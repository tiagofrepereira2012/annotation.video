#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Tue 17 Jul 2012 13:04:44 CEST 

"""Post processes video annotations with stock algorithms.
"""

import os
import sys
from PIL import Image

def load_input(filename, shape):
  """Loads the keypoint input file, checks the input shape for problems."""

  from ...io import load, check_input

  data, header = load(filename)

  if not data:
    raise RuntimeError, 'No keypoints found at %s' % filename

  check_input(data, header, shape)

  return data, header

def shape(filename):
  """Returns the number of frames in the input video"""

  import bob
  reader = bob.io.VideoReader(filename)
  return len(reader), reader.height, reader.width

def process_arguments():

  import argparse

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  parser.add_argument('video', metavar='VIDEO', type=str,
      help="Video file to load")

  parser.add_argument('keypoints', metavar='FILE', type=str,
      help="Files with annotations for the input video")

  parser.add_argument('output', metavar='FILE', type=str,
      help="Output file that will contain the modified annotations")

  algo_choices = ('interpolate', 'expand', 'none')
  parser.add_argument('-a', '--algorithm', dest='algo',
      type=str, choices=algo_choices, default=algo_choices[0],
      help="Post-processing algorithm for annotations (options are one of '%s'; defaults to '%s')" % ('|'.join(algo_choices), '%(default)s'))

  from ..version import __version__
  name = os.path.basename(os.path.splitext(sys.argv[0])[0])
  parser.add_argument('-V', '--version', action='version',
      version='Video Keypoint Annotation Tool v%s (%s)' % (__version__, name))
  
  args = parser.parse_args()

  args.algo = args.algo.lower()

  if not os.path.exists(args.video):
    parser.error("Input video file '%s' cannot be read" % args.video)

  if not os.path.exists(args.keypoints):
    parser.error("Input keypoint file '%s' cannot be read" %
        args.config)

  if args.output:
    d = os.path.dirname(os.path.realpath(args.output))
    if not os.path.exists(d): 
      sys.stdout.write("Creating output directory '%s'..." % (d,))
      sys.stdout.flush()
      os.makedirs(d)
      sys.stdout.write(" OK")
      sys.stdout.flush()

  return args

def main():

  args = process_arguments()
 
  sys.stdout.write("Loading input at '%s'..." % (args.video,))
  sys.stdout.flush()
  video_shape = shape(args.video)

  sys.stdout.write("OK!\nLoading keypoint configuration at '%s'..." % \
      (args.keypoints,))
  sys.stdout.flush()
  data, header = load_input(args.keypoints, video_shape)

  if args.algo != 'none':
    sys.stdout.write("OK!\nPost-processing annotations with '%s'..." %
        args.algo.lower())
    sys.stdout.flush()
    if args.algo == 'interpolate':
      from ...algorithm import interpolate
      data = interpolate(data, video_shape[0])
    elif args.algo == 'expand':
      from ...algorithm import past_expand
      data = past_expand(data, video_shape[0])
    sys.stdout.write(" OK!\n")
    sys.stdout.flush()

  from ...io import save
  sys.stdout.write("Saving post-processed annotations at '%s'..." % args.output)
  sys.stdout.flush()
  save(data, args.output, header=header, backup=True)
  sys.stdout.write(" OK!\n")
  sys.stdout.flush()

if __name__ == '__main__':
  main()
