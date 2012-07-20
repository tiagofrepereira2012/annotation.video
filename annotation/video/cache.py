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

  def __init__(self, filename, N=0, mid=0):
    """Opens and preload N frames into memory. As soon as a non-loaded frame is
    required, load it and load the next N frames as well.

    Parameters

    filename
      The name of the file to read containing the video

    N
      The number of frames to cache. In reality (see below), we cache 2N.

    mid
      If you wouldn't like to start from 0, you can specify an arbitrary number
      here. This number corresponds to the middle of the range you want to have
      loaded. The cache will operate from this point minus N to this point plus
      N, loading a total of 2N frames each time a non-cached frame is
      requested.
    """

    self.video = bob.io.VideoReader(filename)
    self.N = N
    self.prefix = None
    self.suffix = None
    
    if N > 0 and N < len(self.video) and mid >=0:
      self.start = mid-N if (mid-N) >= 0 else 0
      self.end = mid+N if (mid+N) <= len(self.video) else len(self.video)
    else:
      self.start = 0
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
