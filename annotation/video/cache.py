#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Tue 17 Jul 2012 14:07:02 CEST 

"""Implements a Video access utility that allows one to load/unload the video
stream on the fly.
"""

from PIL import Image
import bob

def frame_to_pil_image(frame):
  """Transforms a Bob video frame into a PIL image"""

  return Image.merge('RGB', [Image.fromarray(frame[k]) for k in range(3)])

class Video(object):
  """Video cache object compatible with bob.io.VideoReader"""

  def __init__(self, filename, N=0):
    """Opens and preload N frames into memory. As soon as a non-loaded frame is
    required, load it and load the next N frames as well.
    """

    self.video = bob.io.VideoReader(filename)
    self.N = N
    self.prefix = None
    self.suffix = None
    
    self.start = 0
    
    if N >= 0:
      self.end = self.N if self.N < len(self.video) else len(self.video)
    else:
      self.end = len(self.video)

    self.loaded = [frame_to_pil_image(frame) for frame in self.video[self.start:self.end]]

    self.shape = (len(self.video), self.video.height, self.video.width)

  def framerate(self):
    return self.video.frame_rate

  def __getitem__(self, key):
    
    # sanity checks and range inversion
    if key < 0: key = len(self.video) + key
    if key >= len(self.video):
      raise IndexError, "input video only has %d frames" % len(self.video)

    # load if required
    if key >= self.end or key < self.start:
      if self.prefix is not None: self.prefix()
      self.start = (key-self.N) if (key-self.N) > 0 else 0
      self.end = (key+self.N) if (key+self.N) < len(self.video) else len(self.video)
      self.loaded = [frame_to_pil_image(frame) for frame in self.video[self.start:self.end]]
      if self.suffix is not None: self.suffix()

    # return
    return self.loaded[key-self.start]

  def __len__(self):

    return len(self.video)

  def on_cache_load(self, prefix=None, suffix=None):
    self.prefix = prefix
    self.suffix = suffix
