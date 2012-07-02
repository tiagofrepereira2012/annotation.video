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

class App(object):
  """A wrapper for the current application object"""
  
  def on_quit(self):

    sys.exit(0)

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

  def add_keyboard_bindings(self, widget):
    """Adds mouse bindings to the given widget"""

    widget.bind("<Right>", self.goto_next_frame)
    widget.bind("<Left>", self.goto_previous_frame)

  def update_image(self):
    """Updates the image displayed on the given widget"""

    # set or replace the current frame image
    self.curr_photo = ImageTk.PhotoImage(self.video[self.curr_frame].resize(self.shape, Image.ANTIALIAS))
    if self.curr_image is None:
      self.curr_image = self.cv.create_image(self.shape[0], self.shape[1],
          anchor=tkinter.SE, image=self.curr_photo)
    else:
      self.cv.itemconfig(self.curr_image, image=self.curr_photo)

    # updates the status bar
    self.text_var.set('[%03d/%03d frames]' % (self.curr_frame+1, 
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

  def self.on_kp_button_press(self):
    """What happens when the user clicks close to a key point"""

    # Being drag of an object
    # record the item and its location

    self._drag_data["item"] = self.canvas.find_closest(event.x, event.y)[0]
    self._drag_data["x"] = event.x
    self._drag_data["y"] = event.y

  def self.on_kp_button_release(self):
    """What happens when the user releases a key point"""

    # End drag of an object'''
    # reset the drag information
    self._drag_data["item"] = None
    self._drag_data["x"] = 0
    self._drag_data["y"] = 0

  def self.on_kp_motion(self):
    """What happens when the user drags a key point"""

    # compute how much this object has moved
    delta_x = event.x - self._drag_data["x"]
    delta_y = event.y - self._drag_data["y"]

    # move the object the appropriate amount
    self.cv.move(self._drag_data["item"], delta_x, delta_y)

    # record the new position
    self._drag_data["x"] = event.x
    self._drag_data["y"] = event.y

  def self.add_drag_n_drop(self, widget):
    """Add bindings for clicking, dragging and releasing over any object with
    the "keypoint" tag"""

    widget.tag_bind("keypoint", "<ButtonPress-1>", self.on_kp_button_press)
    widget.tag_bind("keypoint", "<ButtonRelease-1>", self.on_kp_button_release)
    widget.tag_bind("keypoint", "<B1-Motion>", self.on_kp_motion)

  def self.show_keypoints(self, widget, annotations):
    """Shows keypoints acording to existing annotations"""

    if annotations is not None:
      for k in self.keypoints:
        widget.coords(k, ())

    for k in self.keypoints:
      widget.itemconfig(k, state=tkinter.NORMAL)
    self.keypoints.append(widget.create_oval(x-self.radius,
          y-self.radius, x+self.radius, y+self.radius, outline="yellow",
          fill=None, tags="keypoint", width=2.0, state=tkinter.HIDDEN))
    
  def self.create_keypoints(self, widget):
    """Creates the keypoints and draw them to the screen, hiding their
    locations"""

    self.keypoints = []

    # needs a better configuration
    x = self.shape[0]/2
    y = self.shape[1]/2
 
    self.keypoints.append(widget.create_oval(x-self.radius,
          y-self.radius, x+self.radius, y+self.radius, outline="yellow",
          fill=None, tags="keypoint", width=2.0, state=tkinter.HIDDEN))
    
  def __init__(self, master, video, zoom, radius):
 
    # holds a pointer to the video object being displayed
    self.video = video
    self.zoom = zoom
    self.radius = radius
    self.shape = (zoom*video[0].size[0], zoom*video[0].size[1])
    self.curr_frame = 0
    self.annotations = len(self.video) * [None]

    # the image widget
    self.cv = tkinter.Canvas(master, 
        width=self.shape[0], height=self.shape[1]+10)
    self.cv.pack(side=tkinter.TOP)

    #self.screen.onclick(self.on_click)
    #self.screen.tracer(0)

    # the status bar
    self.frame = tkinter.Frame(master)
    self.frame.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH)
    self.text_var = tkinter.StringVar()
    self.text_var.set('[%03d/%03d frames]' % (self.curr_frame+1, 
      len(self.video)))
    self.text_label = tkinter.Label(self.frame, textvariable=self.text_var)
    self.text_label.pack(side=tkinter.RIGHT)

    # place frame 0 on the screen and start the app
    self.curr_image = None
    self.update_image()

    self.create_keypoints(self.cv)

    # adds our keyboard bindings
    self.add_keyboard_bindings(master)

    # adds our mouse bindings
    self.add_drag_n_drop(self.cv)

    #self.screen.setworldcoordinates(0, 0, self.shape[0], self.shape[1])

def process_arguments():

  import argparse

  parser = argparse.ArgumentParser(description=__doc__)

  parser.add_argument('video', metavar='VIDEO', type=str,
      help="Video file to load")

  parser.add_argument('-z', '--zoom', dest='zoom', metavar='N',
      type=int, default=4,
      help="Zoom in by the given factor (defaults to %(default)s)")

  parser.add_argument('-d', '--annotation-radius', dest='radius',
      metavar='N', type=int, default=8, 
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

  root = tkinter.Tk()
  root.title("annotate")

  app = App(root, v, args.zoom, args.radius)

  tkinter.mainloop()

if __name__ == '__main__':
  main()
