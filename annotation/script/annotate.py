#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Fri 29 Jun 2012 13:42:57 CEST 

"""A TkInter-based keypoint annotation tool for videos
"""

import os
import sys
import logging
import Tkinter as tkinter
from PIL import Image, ImageTk
import numpy.linalg
from operator import itemgetter

class AnnotatorApp(tkinter.Tk):
  """A wrapper for the annotation application"""
  
  def __init__(self, video, zoom, radius, *args, **kwargs):

    tkinter.Tk.__init__(self, *args, **kwargs)
    self.title("annotate")
 
    # holds a pointer to the video object being displayed
    self.video = video
    self.zoom = zoom
    self.radius = radius
    self.shape = (zoom*video[0].size[0], zoom*video[0].size[1])
    self.curr_frame = 0
    self.annotations = len(self.video) * [None]

    # creates the image canvas
    self.canvas = tkinter.Canvas(self, 
        width=self.shape[0], height=self.shape[1]+10)
    self.canvas.pack(side=tkinter.TOP)

    # creates the status bar - bellow the image canvas
    self.bottom_frame = tkinter.Frame(self)
    self.bottom_frame.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH)
    self.text_frame = tkinter.StringVar()
    self.text_frame.set('[%03d/%03d frames]' % (self.curr_frame+1, 
      len(self.video)))
    self.text_label = tkinter.Label(self.bottom_frame,
        textvariable=self.text_frame)
    self.text_label.pack(side=tkinter.RIGHT)

    # place frame 0 on the screen and start the app
    self.curr_image = None
    self.keypoints = None
    self.dragged = [0, 0, None]
    self.update_image()

    # some keyboard and mouse bindings
    self.add_keyboard_bindings()
    self.add_drag_n_drop()

  def goto_next_frame(self, *args, **kwargs):
    """Advances to the next frame to be shown"""

    if (self.curr_frame+1) >= len(self.video): 
      logging.warn("Cannot go beyond frame %d on a video with %d frames" % \
          (self.curr_frame+1, len(self.video)))
      return
    self.curr_frame += 1
    self.update_image()

  def goto_previous_frame(self, *args, **kwargs):
    """Rewinds to the previous frame"""

    if (self.curr_frame-1) < 0:
      logging.warn("Cannot go beyond frame %d while rewinding" % \
          (self.curr_frame+1))
      return
    self.curr_frame -= 1
    self.update_image()

  def add_keyboard_bindings(self):
    """Adds mouse bindings to the given widget"""

    self.bind("<Right>", self.goto_next_frame)
    self.bind("<Left>", self.goto_previous_frame)

  def update_image(self):
    """Updates the image displayed on the given widget"""

    # set or replace the current frame image
    self.curr_photo = ImageTk.PhotoImage(self.video[self.curr_frame].resize(self.shape, Image.ANTIALIAS))
    if self.curr_image is None:
      self.curr_image = self.canvas.create_image(self.shape[0], self.shape[1],
          anchor=tkinter.SE, image=self.curr_photo)
    else:
      self.canvas.itemconfig(self.curr_image, image=self.curr_photo)

    # updates the status bar
    self.text_frame.set('[%03d/%03d frames]' % (self.curr_frame+1, 
      len(self.video)))

    # show keypoints
    use_annotation = self.annotations[self.curr_frame]
    if use_annotation is None:
      use_frame = self.curr_frame - 1
      while use_frame > 0:
        if self.annotations[use_frame] is not None:
          use_annotation = self.annotations[use_frame]
          break
        use_frame -= 1
    self.show_keypoints(use_annotation)

  def on_keypoint_button_press(self, event):
    """What happens when the user clicks close to a key point
    
    Find the closest keypoint that applies, set an internal variable marking
    it. Re-paint the keypoint in white to visually mark the keypoint being
    edited.
    """

    def find_closest(x, y):
      """My own implementation to find the closest keypoint to the location
      clicked by the user."""
      dist = [numpy.linalg.norm((x-k[0],y-k[1])) for k in self.keypoints]
      return min(enumerate(dist), key=itemgetter(1))[1]
   
    kp = find_closest(event.x, event.y)
    self.dragged = [event.x, event.y, self.keypoints[kp]]
    print "Found kp", self.dragged[kp]
    #self.canvas.itemconfig(kp, outline='white')

  def on_keypoint_button_release(self, event):
    """What happens when the user releases a key point
    
    Re-paint the current keypoint in yellow. 
    """
    #self.canvas.itemconfig(self.dragged[2], outline='yellow')
    self.dragged = [0, 0, None]

  def on_keypoint_motion(self, event):
    """What happens when the user drags a key point
    
    Finds out how much the user has dragged the keypoint. Move the circle drawn
    on the screen to the new location on the canvas. Update the annotations or
    create new annotations if none existed so far for the current frame.
    """

    # move the object the appropriate amount
    self.canvas.move(self.dragged[2], event.x - self.dragged[0],
        event.y - self.dragged[1])
    self.dragged[0] = event.x
    self.dragged[1] = event.y

    # record the point the marking was dropped in the annotations
    if self.annotations[self.curr_frame] is None:
      # if it is the first time, save all points
      self.annotations[self.curr_frame] = \
          [self.canvas.coords(k) for k in self.keypoints]

    else:
      # otherwise, just save the one that moved
      index = self.keypoints.index(self.dragged[2])
      self.annotations[self.curr_frame][index] = \
          self.canvas.coords(self.dragged[2])

  def add_drag_n_drop(self):
    """Add bindings for clicking, dragging and releasing over any object with
    the "keypoint" tag"""

    self.canvas.tag_bind("keypoint", "<ButtonPress-1>", 
        self.on_keypoint_button_press)
    self.canvas.tag_bind("keypoint", "<ButtonRelease-1>",
        self.on_keypoint_button_release)
    self.canvas.tag_bind("keypoint", "<B1-Motion>",
        self.on_keypoint_motion)

  def create_keypoints(self):
    """Creates the keypoints and draw them to the screen, hiding their
    locations"""

    def cross(x, y, r):
      """Defines a cross in terms of a center and a radius"""
      return (x, y-r, x, y+r, x, y, x-r, y, x+r, y, x, y)

    self.keypoints = []

    # needs a better configuration
    x = self.shape[0]/3
    y = self.shape[1]/3

    self.keypoints.append(self.canvas.create_polygon(cross(x, y, self.radius), 
      outline="yellow", fill=None, tags="keypoint", width=2.0, 
      state=tkinter.HIDDEN))

  def show_keypoints(self, annotations):
    """Shows keypoints acording to existing annotations"""

    if self.keypoints is None: self.create_keypoints()

    if annotations is not None:
      for i, k in enumerate(self.keypoints):
        self.canvas.coords(k, annotations[i])

    for k in self.keypoints: self.canvas.itemconfig(k, state=tkinter.NORMAL)
    
def process_arguments():

  import argparse

  parser = argparse.ArgumentParser(description=__doc__)

  parser.add_argument('video', metavar='VIDEO', type=str,
      help="Video file to load")

  parser.add_argument('-z', '--zoom', dest='zoom', metavar='N',
      type=int, default=4,
      help="Zoom in by the given factor (defaults to %(default)s)")

  parser.add_argument('-d', '--annotation-radius', dest='radius',
      metavar='N', type=int, default=6, 
      help="Diameter of annotations (defaults to %(default)s)")

  args = parser.parse_args()

  if not os.path.exists(args.video):
    parser.error("Input video file '%s' cannot be read" % args.video)

  if args.zoom <= 0:
    parser.error("This app does not accept zooming out ! Choose a zoom factor that is >= 1.")

  if args.radius <= 0:
    parser.error("Cannot have annotations with a radius <= 0")

  return args

def load_video(filename):
  """Transforms the input numpy ndarray sequence into something more suitable
  for TkInter interaction"""

  import bob

  retval = []
  reader = bob.io.VideoReader(filename)
  for frame in reader: retval.append(Image.merge('RGB', [Image.fromarray(frame[k]) for k in range(3)]))

  return retval

def main():

  args = process_arguments()
 
  sys.stdout.write("Loading input at '%s'..." % args.video)
  sys.stdout.flush()
  v = load_video(args.video)

  sys.stdout.write("OK!\nLaunching annotation interface...\n")
  sys.stdout.flush()

  app = AnnotatorApp(v, args.zoom, args.radius)
  app.mainloop()

if __name__ == '__main__':
  main()
