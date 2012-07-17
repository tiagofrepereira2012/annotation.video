#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Tue 17 Jul 2012 12:15:13 CEST 

"""A few algorithms for treating video keypoint annotations.
"""

import logging

def interpolate(data, length):
  """Interpolates the input keypoints so that between frames present a smooth
  transition.
  
  Parameters

    data
      Annotations

    length
      Total duration of video in number of frames

  Returns 'data', altered so all frames in the input video have annotations.
  """

  skeys = sorted(data.iterkeys())
  
  if skeys[0] != 0:
    idx = skeys[0]
    logging.info("Frame 0 is not annotated, borrowing from first annotated frame (%d)" % idx)
    skeys.insert(0,0)
    data[0] = data[idx]

  if skeys[-1] != (length-1):
    idx = skeys[-1]
    logging.info("Frame %d is not annotated, borrowing from last annotated frame (%d)" % (length-1,idx))
    skeys.append(length-1)
    data[length-1] = data[idx]

  intervals = [(skeys[i], skeys[i+1]) for i in range(len(skeys)-1)]

  for low, high in intervals:
    diff = high - low # number of points to interpolate
    delta = [((kp_high[0] - kp_low[0]) / float(diff), (kp_high[1] - kp_low[1]) / float(diff)) for kp_low, kp_high in zip(data[low], data[high])]
    for k in range(1, diff):
      data[low+k] = [(int(round(low_x+(delta[index][0]*k))),int(round(low_y+delta[index][1]*k))) for index, (low_x, low_y) in enumerate(data[low])]

  return data

def past_expand(data, length):
  """Expands the input data so that missing frames get their values from
  the first previous frame with a detection.
  
  Parameters

    data
      Annotations

    length
      Total duration of video in number of frames

  Returns 'data', altered so all frames in the input video have annotations.
  """

  skeys = sorted(data.iterkeys())
  
  if skeys[0] != 0:
    idx = skeys[0]
    logging.info("Frame 0 is not annotated, borrowing from first annotated frame (%d)" % idx)
    skeys.insert(0,0)
    data[0] = data[idx]

  for key in range(length):
    if key not in skeys: #borrow annotation from the past
      back = key - 1
      while back not in skeys: back -= 1
      data[key] = data[back]

  return data
