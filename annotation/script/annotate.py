#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Fri 29 Jun 2012 13:42:57 CEST 

"""A TkInter-based keypoint annotation tool for videos
"""

import os
import sys
import Tkinter as tkinter

class App(object):
  """A wrapper for the current application object"""

  def on_quit(self):

    sys.exit(0)

  def on_write(self):

    pass

  def on_click(self, x, y):

    pass
    #self.screen.update()

  def on_drag(self, x, y):

    pass
    #self.screen.update()

  def __init__(self, master, video):
 
    from PIL import Image, ImageTk

    shape = video.shape[2:]
    
    # place frame 0 on the screen and start the app
    self.photo = ImageTk.PhotoImage(Image.fromarray(video[0][1]))

    self.cv = tkinter.Canvas(master, width=shape[1], height=shape[0]+20)
    self.cv.create_image(shape[1], shape[0], anchor=tkinter.SE, 
        image=self.photo)
    self.cv.pack(side=tkinter.TOP)

    #self.screen.setworldcoordinates(0, 0, shape[1], shape[0])

    self.frame = tkinter.Frame(master)
    self.frame.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH)
    #self.screen.tracer(0)

    self.text_var = tkinter.StringVar()
    self.text_var.set('%03d/%03d frames' % (0, len(video)))
    self.text_label = tkinter.Label(self.frame, textvariable=self.text_var)
    self.text_label.pack(side=tkinter.RIGHT)

    #self.screen.onclick(self.on_click)

def process_arguments():

  import argparse

  parser = argparse.ArgumentParser(description=__doc__)

  parser.add_argument('video', metavar='VIDEO', type=str,
      help="Video file to load")

  args = parser.parse_args()

  if not os.path.exists(args.video):
    parser.error("Input video file '%s' cannot be read" % args.video)

  return args

def main():

  import bob

  args = process_arguments()
 
  sys.stdout.write("Loading input at '%s'..." % args.video)
  sys.stdout.flush()
  v = bob.io.load(args.video)

  sys.stdout.write("OK!\nLaunching annotation interface...\n")
  sys.stdout.flush()

  root = tkinter.Tk()
  root.title("annotate")

  app = App(root, v)

  tkinter.mainloop()

if __name__ == '__main__':
  main()
