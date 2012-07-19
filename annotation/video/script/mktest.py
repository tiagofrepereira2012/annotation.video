#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Thu 19 Jul 2012 10:29:27 CEST 

"""Creates a video file with a sequence of numbers to test the caching
mechanism available on the package.
"""

import os
import sys

def process_arguments():

  import argparse

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  parser.add_argument('output', metavar='FILE', type=str,
      help="Output file that will contain the test video")

  parser.add_argument('-n', '--number-of-frames', dest='N',
      metavar='N', type=int, default=100, 
      help="Number of frames to generate on the test video (defaults to %(default)s)")

  from ..version import __version__
  name = os.path.basename(os.path.splitext(sys.argv[0])[0])
  parser.add_argument('-V', '--version', action='version',
      version='Video Keypoint Annotation Tool v%s (%s)' % (__version__, name))
  
  args = parser.parse_args()

  if args.N <= 0:
    parser.error("Cannot have number of frames in output <= 0")

  if args.output:
    d = os.path.dirname(os.path.realpath(args.output))
    if not os.path.exists(d): 
      sys.stdout.write("Creating output directory '%s'..." % (d,))
      sys.stdout.flush()
      os.makedirs(d)
      sys.stdout.write(" OK")
      sys.stdout.flush()

  return args

def dump(output, N):
  """Dumps the annotated video"""

  import bob
  import numpy
  from PIL import Image, ImageDraw, ImageFont

  width = 640
  height = 480
  fontpath = '/usr/share/fonts/truetype/msttcorefonts/arial.ttf'
  fontsize = height/5
  if os.path.exists(fontpath):
    font = ImageFont.truetype(fontpath, fontsize)
  else:
    font = None

  sys.stdout.write('Saving %d frames at "%s"' % (N, output))
  sys.stdout.flush()
  outv = bob.io.VideoWriter(output, height, width, framerate=10)
  for k in range(N):
    frame = Image.new('RGB', (width, height)) #black background
    draw = ImageDraw.ImageDraw(frame)
    draw.text( (width/2-fontsize/2, height/2-fontsize/2), 
        str(k), fill='white', font=font )
    f = numpy.transpose(numpy.dstack(frame.split()), axes=(2,0,1))
    outv.append(f)
    sys.stdout.write('.')
    sys.stdout.flush()

  sys.stdout.write(' OK!\n')
  sys.stdout.flush()

def main():

  args = process_arguments()
 
  dump(args.output, args.N)

if __name__ == '__main__':
  main()
