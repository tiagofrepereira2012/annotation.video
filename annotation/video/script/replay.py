#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Tue 17 Jul 2012 10:59:18 CEST 

"""Plays the input video overlaid with annotations.
"""

import os
import sys
import bob

def load_input(filename, shape):
  """Loads the keypoint input file, checks the input shape for problems."""

  from ...io import load, check_input

  data, header = load(filename)

  if not data:
    raise RuntimeError, 'No keypoints found at %s' % filename

  check_input(data, header, shape)

  return data, header

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

  algo_choices = ('none', 'interpolate', 'expand')
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

  from PIL import Image, ImageDraw
  import numpy

  img = Image.merge('RGB', [Image.fromarray(frame[i]) for i in range(3)])
  draw = ImageDraw.ImageDraw(img)
  for (x,y) in annotations:
    draw.ellipse((x-R,y-R,x+R,y+R), fill='yellow', outline='black')
  return numpy.transpose(numpy.dstack(img.split()), axes=(2,0,1))

def dump(video, data, header, radius, output):
  """Dumps the annotated video"""

  sys.stdout.write("Creating video file with annotations")
  sys.stdout.flush()
  outv = bob.io.VideoWriter(output, video.height, video.width, framerate=video.frame_rate)

  for k, frame in enumerate(video):
    if data.has_key(k):
      outv.append(annotate(frame, data[k], header, radius))
      sys.stdout.write('.')
      sys.stdout.flush()
    else:
      outv.append(frame)
      sys.stdout.write('x')
      sys.stdout.flush()

  sys.stdout.write(' OK!\n')
  sys.stdout.flush()

def main():

  args = process_arguments()
 
  sys.stdout.write("Loading input at '%s'..." % (args.video,))
  sys.stdout.flush()
  v = bob.io.VideoReader(args.video)

  sys.stdout.write("OK!\nLoading keypoint configuration at '%s'..." % \
      (args.keypoints,))
  sys.stdout.flush()
  data, header = load_input(args.keypoints, (len(v), v.height, v.width))

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

  dump(v, data, header, args.radius, args.output)

if __name__ == '__main__':
  main()
