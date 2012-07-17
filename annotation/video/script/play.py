#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Tue 17 Jul 2012 10:59:18 CEST 

"""Plays the input video overlaid with annotations.
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

def load_video(filename):
  """Transforms the input numpy ndarray sequence into something more suitable
  for TkInter interaction"""

  import bob

  retval = []
  reader = bob.io.VideoReader(filename)
  for frame in reader: 
    sys.stdout.write('.')
    sys.stdout.flush()
    retval.append(Image.merge('RGB', [Image.fromarray(frame[k]) for k in range(3)]))

  return retval, reader.frame_rate

def process_arguments():

  import argparse

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  parser.add_argument('video', metavar='VIDEO', type=str,
      help="Video file to load")

  parser.add_argument('keypoints', metavar='FILE', type=str,
      help="Files with annotations for the input video")

  parser.add_argument('output', metavar='FILE', type=str,
      help="Output file that will contain the annotated video")

  parser.add_argument('-d', '--annotation-radius', dest='radius',
      metavar='N', type=int, default=4, 
      help="Diameter of visual keypoints while annotating (defaults to %(default)s)")

  algo_choices = ('interpolate', 'expand', 'none')
  parser.add_argument('-a', '--algorithm', dest='algo',
      type=str, choices=algo_choices, default=algo_choices[0],
      help="Post-processing algorithm for annotations (options are one of '%s'; defaults to '%s')" % ('|'.join(algo_choices), '%(default)s'))

  args = parser.parse_args()

  args.algo = args.algo.lower()

  if not os.path.exists(args.video):
    parser.error("Input video file '%s' cannot be read" % args.video)

  if args.radius <= 0:
    parser.error("Cannot have annotations with a radius <= 0")

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

def annotate(frame, annotations, header, R):
  """Annotates the frame with nice markings"""

  from PIL import ImageDraw

  draw = ImageDraw.ImageDraw(frame)
  for (x,y) in annotations:
    draw.ellipse((x-R,y-R,x+R,y+R), fill='yellow', outline='black')
  return frame

def dump(video, data, header, radius, output, framerate):
  """Dumps the annotated video"""

  import bob
  import numpy

  sys.stdout.write("Creating video file with annotations")
  sys.stdout.flush()
  for k in range(len(video)):
    if data.has_key(k):
      sys.stdout.write('.')
      sys.stdout.flush()
      video[k] = annotate(video[k], data[k], header, radius)
    else:
      sys.stdout.write('x')
      sys.stdout.flush()

  sys.stdout.write(' OK!\nSaving %d frames at "%s"' % (len(video), output))
  sys.stdout.flush()
  outv = bob.io.VideoWriter(output, video[0].size[1], video[0].size[0], framerate=framerate)
  for frame in video:
    f = numpy.transpose(numpy.dstack(frame.split()), axes=(2,0,1))
    outv.append(f)
    sys.stdout.write('.')
    sys.stdout.flush()

  sys.stdout.write(' OK!\n')
  sys.stdout.flush()

def main():

  args = process_arguments()
 
  sys.stdout.write("Loading input at '%s'..." % (args.video,))
  sys.stdout.flush()
  v, rate = load_video(args.video)

  sys.stdout.write("OK!\nLoading keypoint configuration at '%s'..." % \
      (args.keypoints,))
  sys.stdout.flush()
  data, header = load_input(args.keypoints, (len(v), v[0].size[1], v[0].size[0]))

  if args.algo != 'none':
    sys.stdout.write("OK!\nPost-processing annotations with '%s'..." %
        args.algo.lower())
    sys.stdout.flush()
    if args.algo == 'interpolate':
      from ...algorithm import interpolate
      data = interpolate(data, len(v))
    elif args.algo == 'expand':
      from ...algorithm import past_expand
      data = past_expand(data, len(v))
    sys.stdout.write(" OK!\n")
    sys.stdout.flush()

  dump(v, data, header, args.radius, args.output, rate)

if __name__ == '__main__':
  main()
