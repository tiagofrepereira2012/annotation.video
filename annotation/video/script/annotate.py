#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Fri 29 Jun 2012 13:42:57 CEST 

"""A TkInter-based keypoint annotation tool for videos

This simple application can annotate multiple keypoints in videos. It works
by defining preset keypoints on the image structure and allowing the user to
modify such keypoints either with the mouse, keyboard, or a combination of
both. Once the user modifies the location of one of the keypoints, the
annotations for the given frame are permanently recorded. Frames in which the
user has not modified the keypoints on do not get annotations recorded.

Annotation format
-----------------

The annotation file is composed of an (optional) header followed by rows with
the frame number and `x` and `y` point coordinates. Numbers are all 0-based.
The first frame of a video sequence is numbered 0, as well as the first row or
column of a frame. The record (number) separator is a space and the field (row)
separator is a new-line character. The resulting file can be read and parsed by
most CSV parsers available freely on the internet. 

If a header line is available, it should have length equal to (N-1)/2 where N 
is the number of entries in a non-header line.

Here is a 4-point annotation example::

  OutR InR InL OutL
  0 130 87 146 86 171 86 186 86
        
Available key bindings
----------------------

Default mode
============

  ?
    this help message
  1,2,3,4...g
    place keypoint under cursor
  h, <Left>
    rewind N frames
  l, <Right>
    forward N frames
  D
    Delete annotations for the current frame
  S
    Saves or dumps current annotations
  Q
    Quits the application, saving annotations if required
  <Escape>
    Quits the application, does not save anything, even if required

.. note::

  "N" is the "skip factor" as defined by the command line parameter.

.. note::

  Use <Shift> to move in single frame steps.

Keypoint placement mode
=======================

Use <Space> to switch focus to the next keypoint (highlighted). This
effectively alternates between the "Default" and "Keypoint placement" modes.

  h, <Left>
    move cursor left N pixels
  l, <Right>
    move cursor right N pixels
  j, <Down>
    move cursor down N pixels
  k, <Up>
    move cursor up N pixels
  <Escape>
    go back to default mode
  
.. note::

  "N" is the "skip factor" as defined by the command line parameter
  
.. note::
  
  Use <Shift> to move in single pixel steps

If you use the left <Control> key, you can move all keypoints at once. Use the
same combination of keys for moving individual single points.

Mouse
=====

You can use the mouse to either drag-and-drop keypoints or move the closest keypion to the clicked location.
"""

import os
import sys
import Tkinter as tkinter
from PIL import Image, ImageTk
import numpy.linalg
from operator import itemgetter

COLOR_ACTIVE = "yellow"
COLOR_INACTIVE = "white"
SHIFT = 0x0001

class HelpDialog(tkinter.Toplevel):

  def __init__(self, parent, message):

    tkinter.Toplevel.__init__(self, parent)
    self.transient(parent)
    self.title('help')
    self.parent = parent
    self.result = None

    body = tkinter.Frame(self, width=100, height=400)

    # Now build the dialog geometry
    buttonbox = tkinter.Frame(body, height=20)
    w = tkinter.Button(buttonbox, text="Dismiss", command=self.on_dismiss, 
        default=tkinter.ACTIVE)
    w.pack(side=tkinter.RIGHT)
    self.bind("<Return>", self.on_dismiss)
    self.bind("<Escape>", self.on_dismiss)
    buttonbox.pack(side=tkinter.BOTTOM)

    textbox = tkinter.Frame(body, height=380)
    self.initial_focus = t = tkinter.Text(textbox)
    t.insert(tkinter.INSERT, message) #fill in contents
    scrollbar = tkinter.Scrollbar(textbox)
    scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    t.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=t.yview)
    t.config(state=tkinter.DISABLED)

    t.pack(side=tkinter.TOP)
    textbox.pack(side=tkinter.TOP)

    body.pack(padx=5, pady=5)

    self.grab_set()

    if not self.initial_focus: self.initial_focus = self

    self.protocol("WM_DELETE_WINDOW", self.on_dismiss)

    self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                              parent.winfo_rooty()+50))

    self.initial_focus.focus_set()
    self.wait_window(self)

  def on_dismiss(self, event=None):

    # put focus back to the parent window
    self.parent.focus_set()
    self.destroy()

class BusyManager:

  def __init__(self, widget):
    self.toplevel = widget.winfo_toplevel()
    self.widgets = {}

  def busy(self, widget=None):

    # attach busy cursor to toplevel, plus all windows
    # that define their own cursor.

    if widget is None:
      w = self.toplevel # myself
    else:
      w = widget

    if not self.widgets.has_key(str(w)):
      try:
          # attach cursor to this widget
          cursor = w.cget("cursor")
          if cursor != "watch":
              self.widgets[str(w)] = (w, cursor)
              w.config(cursor="watch")
              w.update_idletasks()
      except TclError:
          pass

    for w in w.children.values():
      self.busy(w)

  def notbusy(self):

    # restore cursors
    for w, cursor in self.widgets.values():
        try:
            w.config(cursor=cursor)
            w.update_idletasks()
        except TclError:
            pass
    self.widgets = {}

class AnnotatorApp(tkinter.Tk):
  """A wrapper for the annotation application"""
  
  def __init__(self, video, zoom, radius, skip_factor, config, input, 
      output, start, *args, **kwargs):

    tkinter.Tk.__init__(self, *args, **kwargs)
    self.title("annotate")
 
    # holds a pointer to the video object being displayed
    self.video = video
    self.video.on_cache_load(self.on_cache_load, self.on_cache_loaded)
    self.zoom = zoom
    self.radius = radius
    self.shape = (int(round(zoom*video.shape[2])), 
        int(round(zoom*video.shape[1])))
    self.curr_frame = start if start < len(self.video) else (len(self.video)-1)
    self.skip_factor = skip_factor
    self.immediate_keys = '1234567890abcdefg' #max of 17 points
    self.output = output
    self.unsaved = False #if we have data that needs saving
    self.keypoint_config = config
    self.annotations = input
    self.busyman = BusyManager(self)

    if self.zoom != 1:
      # zoom correction
      self.keypoint_config = [(int(round(zoom*x)),int(round(zoom*y)),l) for (x,y,l) in config]
      for k in self.annotations.iterkeys(): 
        self.annotations[k] = [(int(round(zoom*x)),int(round(zoom*y))) for (x,y) in self.annotations[k]]

    # creates the image canvas
    self.canvas = tkinter.Canvas(self, width=self.shape[0], height=self.shape[1])
    self.canvas.pack(side=tkinter.TOP)

    # creates the status bar - bellow the image canvas
    self.bottom_frame = tkinter.Frame(self)
    self.bottom_frame.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH)
    self.text_status = tkinter.StringVar()
    self.label_status = tkinter.Label(self.bottom_frame,
        textvariable=self.text_status)
    self.label_status.pack(side=tkinter.LEFT)

    # place frame 0 on the screen and start the app
    self.curr_image = None
    self.keypoints = None
    self.dragged = [0, 0, None]
    self.curr_focus = None
    self.update_image()
    self.text_status.set('[OK] you can interact with this window. Press ? for help')

    # resize all dialog boxes by default to be 200px wide
    self.option_add("*Dialog.msg.wrapLength", "200p")

    # some keyboard and mouse bindings
    self.add_keyboard_bindings()
    self.add_drag_n_drop()

    # Capture closing the app -> use to save the file
    self.protocol("WM_DELETE_WINDOW", self.on_quit)
    self.bind("Q", self.on_quit)
    self.bind("<Escape>", self.on_quit_no_saving)
    self.bind("S", self.save)
    self.bind("D", self.on_delete_current_frame_annotations)

  def on_cache_load(self):
    """Method called when the video cache is operating"""
    self.label_status.config(background='red', foreground='white')
    self.text_status.set('[cache] reloading...')
    self.label_status.update_idletasks()
    self.busyman.busy()

  def on_cache_loaded(self):
    """Method called when the video cache finished loading"""
    self.label_status.config(background=self.cget('background'), 
        foreground='black')
    self.text_status.set('[cache] reloading finished')
    self.label_status.update_idletasks()
    self.busyman.notbusy()

  def zoom_compensated(self):
    """Returns zoom-compensated annotations"""

    def rounded(x, y, z):
      return (int(round(float(x)/z)), int(round(float(y)/z)))

    import copy

    retval = copy.deepcopy(self.annotations)
    for key, values in retval.iteritems():
      retval[key] = [rounded(x,y,self.zoom) for x,y in values]

    return retval

  def save(self, *args, **kwargs):
    """Action executed when the user explicitly asks us to save the file"""

    from ...io import save as file_save

    if (self.unsaved and self.annotations) or \
        not isinstance(self.output, (str,unicode)):

      header = [l for (x,y,l) in self.keypoint_config]

      if self.output: 
        import time
        curtime = time.strftime('%H:%M:%S')
        sys.stdout.write("Writing annotations to '%s' (%s)..." % (self.output,
          curtime))
        sys.stdout.flush()
        file_save(self.zoom_compensated(), self.output, header=header,
            backup=True)
        sys.stdout.write(" OK\n")
        sys.stdout.flush()
      else: 
        sys.stdout.write('\n')
        sys.stdout.flush()
        file_save(self.zoom_compensated(), sys.stdout, header=header)
        sys.stdout.flush()
      
      self.unsaved = False

    else:

      sys.stdout.write("Saving to '%s' (skipped): unchanged\n" % self.output)
      sys.stdout.flush()
      
  def on_quit_no_saving(self, *args, **kwargs):
    """On quit we either dump the output to screen or to a file."""

    if self.unsaved and self.annotations and \
        isinstance(self.output, (str,unicode)):
      sys.stdout.write("Warning: lost annotations\n")
      sys.stdout.flush()

    self.destroy()

  def on_quit(self, *args, **kwargs):
    """On quit we either dump the output to screen or to a file."""

    self.save(*args, **kwargs)
    self.on_quit_no_saving(*args, **kwargs)

  def on_delete_current_frame_annotations(self, event):
    """Delete current frame annotations and reset the view"""

    if self.annotations.has_key(self.curr_frame):
      del self.annotations[self.curr_frame]
      self.update_image()

  def on_help(self, event):
    """Creates a help dialog box with the currently enabled commands"""

    dialog = HelpDialog(self, __doc__)

  def change_frame(self, event):
    """Advances to the next or rewinds to the previous frame"""

    move = 0

    if event.keysym in ('Right', 'l', 'L') or \
        event.num in (4,): move = self.skip_factor
    if event.keysym in ('Left', 'h', 'H') or \
        event.num in (5,): move = -self.skip_factor
    if event.state & SHIFT: move /= self.skip_factor

    self.curr_frame += move

    if self.curr_frame >= len(self.video):
      self.text_status.set('[warning] cannot go beyond end')
      self.curr_frame = len(self.video) - 1
    elif self.curr_frame < 0:
      self.text_status.set('[warning] cannot go before start')
      self.curr_frame = 0
    
    self.update_image()

  def set_keypoint(self, event):
    """Sets the given keypoint position immediately"""

    # move the object the appropriate amount
    kpindex = self.immediate_keys.index(event.char)
    kpx, kpy, kpitem = self.keypoints[kpindex]
    for obj in [item for sublist in kpitem for item in sublist]: 
      self.canvas.move(obj, event.x - kpx, event.y - kpy)
    self.keypoints[kpindex][0] = event.x
    self.keypoints[kpindex][1] = event.y

    # record the point the marking was dropped in the annotations
    if not self.annotations.has_key(self.curr_frame):
      # if it is the first time, save all points
      self.annotations[self.curr_frame] = \
          [[k[0],k[1]] for k in self.keypoints]

    else:
      # otherwise, just save the one that moved
      self.annotations[self.curr_frame][kpindex] = (event.x, event.y)

    self.unsaved = True
    self.update_status_bar()

  def set_keypoint_focus(self, event):
    """Sets the focus on the first keypoint in the canvas"""

    if self.curr_focus is None:
      self.curr_focus = 0
      for obj in (self.keypoints[self.curr_focus][2][0] + self.keypoints[self.curr_focus][2][2]):
        self.canvas.itemconfig(obj, fill=COLOR_ACTIVE)
      self.text_status.set('[focus] set on keypoint %d' % (self.curr_focus+1,))
    else:
      self.curr_focus += 1
      if self.curr_focus >= len(self.keypoints):
        # reset, focus back to main window
        for obj in (self.keypoints[-1][2][0] + self.keypoints[-1][2][2]):
          self.canvas.itemconfig(obj, fill=COLOR_INACTIVE)
        self.text_status.set('[focus] set back on main window')
        self.curr_focus = None
      else:
        for obj in (self.keypoints[self.curr_focus-1][2][0] + self.keypoints[self.curr_focus-1][2][2]):
          self.canvas.itemconfig(obj, fill=COLOR_INACTIVE)
        for obj in (self.keypoints[self.curr_focus][2][0] + self.keypoints[self.curr_focus][2][2]):
          self.canvas.itemconfig(obj, fill=COLOR_ACTIVE)
        self.text_status.set('[focus] set on keypoint %d' % (self.curr_focus+1,))

  def on_quick_keypoint_fix(self, event):
    """Sets the closest keypoint to the mouse location"""

    def find_closest(x, y):
      """My own implementation to find the closest keypoint to the location
      clicked by the user."""
      dist = [numpy.linalg.norm((x-k[0],y-k[1])) for k in self.keypoints]
      return min(enumerate(dist), key=itemgetter(1))[0]
   
    # move the object the appropriate amount
    kpindex = find_closest(event.x, event.y)
    kpx, kpy, kpitem = self.keypoints[kpindex]
    for obj in [item for sublist in kpitem for item in sublist]: 
      self.canvas.move(obj, event.x - kpx, event.y - kpy)
    self.keypoints[kpindex][0] = event.x
    self.keypoints[kpindex][1] = event.y

    # record the point the marking was dropped in the annotations
    if not self.annotations.has_key(self.curr_frame):
      # if it is the first time, save all points
      self.annotations[self.curr_frame] = \
          [[k[0],k[1]] for k in self.keypoints]

    else:
      # otherwise, just save the one that moved
      self.annotations[self.curr_frame][kpindex] = (event.x, event.y)

    self.unsaved = True
    self.update_status_bar()

  def on_highlight_all(self, event):
    """Highlights all elements at once"""

    for x, y, objects in self.keypoints:
      for o in (objects[0] + objects[2]):
        self.canvas.itemconfig(o, fill=COLOR_ACTIVE)

  def on_unhighlight_all(self, event):
    """Unhighlights all elements at once"""
    
    for x, y, objects in self.keypoints:
      for o in (objects[0] + objects[2]):
        self.canvas.itemconfig(o, fill=COLOR_INACTIVE)

  def on_move_all(self, event):
    """Moves a focused keypoint"""

    # calculates the total motion
    dx, dy = (0, 0)
    if event.keysym in ('Right', 'l', 'L'): dx = self.skip_factor 
    elif event.keysym in ('Left', 'h', 'H'): dx = -self.skip_factor
    elif event.keysym in ('Up', 'k', 'K'): dy = -self.skip_factor
    elif event.keysym in ('Down', 'j', 'J'): dy = self.skip_factor
    
    if event.state & SHIFT: dx /= self.skip_factor; dy /= self.skip_factor

    for i, (kpx, kpy, kpitem) in enumerate(self.keypoints):

      for obj in [item for sublist in kpitem for item in sublist]:
        self.canvas.move(obj, dx, dy)

      self.keypoints[i][0] = kpx + dx
      self.keypoints[i][1] = kpy + dy

      # record the point the marking was dropped in the annotations
      if not self.annotations.has_key(self.curr_frame):
        # if it is the first time, save all points
        self.annotations[self.curr_frame] = \
            [[k[0],k[1]] for k in self.keypoints]

      else:
        # otherwise, just save the one that moved
        self.annotations[self.curr_frame][i] = (kpx + dx, kpy + dy)

    self.unsaved = True
    self.update_status_bar()
    
  def move_focused_keypoint(self, event):
    """Moves a focused keypoint"""

    # move the object the appropriate amount
    kpx, kpy, kpitem = self.keypoints[self.curr_focus]
    dx, dy = (0, 0)
    if event.keysym in ('Right', 'l', 'L'): dx = self.skip_factor 
    elif event.keysym in ('Left', 'h', 'H'): dx = -self.skip_factor
    elif event.keysym in ('Up', 'k', 'K'): dy = -self.skip_factor
    elif event.keysym in ('Down', 'j', 'J'): dy = self.skip_factor
    
    if event.state & SHIFT: dx /= self.skip_factor; dy /= self.skip_factor

    for obj in [item for sublist in kpitem for item in sublist]: 
      self.canvas.move(obj, dx, dy)

    self.keypoints[self.curr_focus][0] = kpx + dx
    self.keypoints[self.curr_focus][1] = kpy + dy

    # record the point the marking was dropped in the annotations
    if not self.annotations.has_key(self.curr_frame):
      # if it is the first time, save all points
      self.annotations[self.curr_frame] = \
          [[k[0],k[1]] for k in self.keypoints]

    else:
      # otherwise, just save the one that moved
      self.annotations[self.curr_frame][self.curr_focus] = (kpx + dx, kpy + dy)

    self.unsaved = True
    self.update_status_bar()

  def on_move(self, event):
    """What happens when one of the arrow keys is pressed"""

    if self.curr_focus is not None and (event.num not in (4,5)): 
      self.move_focused_keypoint(event)
    else: 
      self.change_frame(event)

  def on_show_labels(self, event):
    """Shows labels"""

    for x, y, objects in self.keypoints:
      for o in (objects[2] + objects[3]):
        self.canvas.itemconfig(o, state=tkinter.NORMAL)

  def on_hide_labels(self, event):
    """Hide labels"""

    for x, y, objects in self.keypoints:
      for o in (objects[2] + objects[3]):
        self.canvas.itemconfig(o, state=tkinter.HIDDEN)

  def add_keyboard_bindings(self):
    """Adds mouse bindings to the given widget"""

    # immediate placement using <key>
    for i, k in enumerate(self.keypoints):
      self.bind("%s" % self.immediate_keys[i], self.set_keypoint)

    # focus on a given keypoint (marked in white)
    self.bind("<space>", self.set_keypoint_focus)

    # motion keys - move frame or keypoint depending on keypoint focus
    self.bind("<Right>", self.on_move)
    self.bind("<Shift-Right>", self.on_move)
    self.bind("<Left>", self.on_move)
    self.bind("<Shift-Left>", self.on_move)
    self.bind("<Up>", self.on_move)
    self.bind("<Shift-Up>", self.on_move)
    self.bind("<Down>", self.on_move)
    self.bind("<Shift-Down>", self.on_move)
    self.bind("h", self.on_move)
    self.bind("H", self.on_move)
    self.bind("l", self.on_move)
    self.bind("L", self.on_move)
    self.bind("k", self.on_move)
    self.bind("K", self.on_move)
    self.bind("j", self.on_move)
    self.bind("J", self.on_move)

    # with control down, highlight all points in orange, move all together
    self.bind("<KeyPress-Control_L>", self.on_highlight_all)
    self.bind("<KeyRelease-Control_L>", self.on_unhighlight_all)
    self.bind("<Control-Right>", self.on_move_all)
    self.bind("<Control-Left>", self.on_move_all)
    self.bind("<Control-Up>", self.on_move_all)
    self.bind("<Control-Down>", self.on_move_all)
    self.bind("<Shift-Control-Right>", self.on_move_all)
    self.bind("<Shift-Control-Left>", self.on_move_all)
    self.bind("<Shift-Control-Up>", self.on_move_all)
    self.bind("<Shift-Control-Down>", self.on_move_all)
    self.bind("<Control-h>", self.on_move_all)
    self.bind("<Control-l>", self.on_move_all)
    self.bind("<Control-k>", self.on_move_all)
    self.bind("<Control-j>", self.on_move_all)
    self.bind("<Control-H>", self.on_move_all)
    self.bind("<Control-L>", self.on_move_all)
    self.bind("<Control-K>", self.on_move_all)
    self.bind("<Control-J>", self.on_move_all)

    # show text labels with Alt pressed
    self.bind("<KeyPress-Alt_L>", self.on_show_labels)
    self.bind("<KeyRelease-Alt_L>", self.on_hide_labels)

    self.bind("?", self.on_help)

  def update_image(self):
    """Updates the image displayed on the given widget"""

    # set or replace the current frame image
    self.curr_photo = ImageTk.PhotoImage(self.video[self.curr_frame].resize(self.shape, Image.ANTIALIAS))
    if self.curr_image is None:
      self.curr_image = self.canvas.create_image(self.shape[0], self.shape[1],
          anchor=tkinter.SE, image=self.curr_photo)
    else:
      self.canvas.itemconfig(self.curr_image, image=self.curr_photo)

    # show keypoints
    use_annotation = self.annotations.get(self.curr_frame, None)
    if use_annotation is None:
      # try to get an annotation from any of the previous frames
      use_frame = self.curr_frame - 1
      while use_frame >= 0:
        if self.annotations.has_key(use_frame):
          use_annotation = self.annotations[use_frame]
          break
        use_frame -= 1
    self.show_keypoints(use_annotation)

    self.update_status_bar()

  def update_status_bar(self):

    # updates the status bar
    annotated = '(previous state)'
    if not self.annotations: annotated = '(no annotations)'
    if self.annotations.has_key(self.curr_frame): annotated = ' (annotated)'
    self.text_status.set('[status] frame %03d/%03d %s' % (self.curr_frame+1, 
      len(self.video), annotated))

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
      return min(enumerate(dist), key=itemgetter(1))[0]
   
    index = find_closest(event.x, event.y)

    # self.dragged keeps the *current* event location and an index to the
    # keypoint position in the list of keypoints.
    self.dragged = [event.x, event.y, index]

    for obj in (self.keypoints[index][2][0] + self.keypoints[index][2][2]):
      self.canvas.itemconfig(obj, fill=COLOR_ACTIVE)

  def on_keypoint_button_release(self, event):
    """What happens when the user releases a key point
    
    Re-paint the current keypoint in COLOR_INACTIVE.
    """
    for obj in (self.keypoints[self.dragged[2]][2][0] + self.keypoints[self.dragged[2]][2][2]):
      self.canvas.itemconfig(obj, fill=COLOR_INACTIVE)
    self.dragged = [0, 0, None]

  def on_keypoint_motion(self, event):
    """What happens when the user drags a key point
    
    Finds out how much the user has dragged the keypoint. Move the circle drawn
    on the screen to the new location on the canvas. Update the annotations or
    create new annotations if none existed so far for the current frame.
    """

    # move the object the appropriate amount
    kpindex = self.dragged[2]
    kpx, kpy, kpitem = self.keypoints[kpindex]
    for obj in [item for sublist in kpitem for item in sublist]: 
      self.canvas.move(obj, event.x - self.dragged[0], event.y -
          self.dragged[1])
    self.dragged[0] = self.keypoints[kpindex][0] = event.x
    self.dragged[1] = self.keypoints[kpindex][1] = event.y

    # record the point the marking was dropped in the annotations
    if not self.annotations.has_key(self.curr_frame):
      # if it is the first time, save all points
      self.annotations[self.curr_frame] = \
          [[k[0],k[1]] for k in self.keypoints]

    else:
      # otherwise, just save the one that moved
      self.annotations[self.curr_frame][kpindex] = (event.x, event.y)

    self.unsaved = True
    self.update_status_bar()

  def add_drag_n_drop(self):
    """Add bindings for clicking, dragging and releasing over any object with
    the "keypoint" tag"""

    self.canvas.tag_bind("keypoint", "<ButtonPress-1>", 
        self.on_keypoint_button_press)
    self.canvas.tag_bind("keypoint", "<ButtonRelease-1>",
        self.on_keypoint_button_release)
    self.canvas.tag_bind("keypoint", "<B1-Motion>",
        self.on_keypoint_motion)
    self.canvas.bind("<ButtonPress-1>", self.on_quick_keypoint_fix)
    self.canvas.bind("<4>", self.on_move)
    self.canvas.bind("<5>", self.on_move)

  def create_keypoints(self):
    """Creates the keypoints and draw them to the screen, hiding their
    locations"""

    def cross(canvas, x, y, w, text):
      """Defines a cross + number in terms of a center and a radius"""

      #points = (x, y-r, x, y+r, x, y, x-r, y, x+r, y, x, y)
      w3 = 3*w; 
      points = (
          x-w, y-w3, 
          x+w, y-w3, 
          x+w, y-w, 
          x+w3, y-w, 
          x+w3, y+w,
          x+w, y+w,
          x+w, y+w3,
          x-w, y+w3,
          x-w, y+w,
          x-w3, y+w,
          x-w3, y-w,
          x-w, y-w,
          )

      # text - not modifiable for the color
      t = canvas.create_text((x-w3, y-w3), anchor=tkinter.SE,
          fill='black', tags="keypoint", state=tkinter.NORMAL,
          justify=tkinter.RIGHT, text=text)

      bbox = canvas.bbox(t)
      canvas.itemconfig(t, state=tkinter.HIDDEN)

      # background drop shadow
      s = canvas.create_rectangle(bbox, fill=COLOR_INACTIVE, tags="keypoint",
          state=tkinter.HIDDEN)
      # text on the top of the drop shadow
      canvas.tag_raise(t)

      poly = canvas.create_polygon(points, outline='black',
          fill=COLOR_INACTIVE, tags="keypoint", width=1.0, state=tkinter.HIDDEN)

      # [0]: activate-able (not hidden); 
      # [1]: not activate-able (not hidden);
      # [2]: activate-able (hidden); 
      # [3]: not activate-able (hidden);
      return ((poly,), tuple(), (s,), (t,))

    self.keypoints = []

    for i, (x, y, l) in enumerate(self.keypoint_config):
      self.keypoints.append([x, y, cross(self.canvas, x, y, self.radius, l)])

  def show_keypoints(self, annotations):
    """Shows keypoints acording to existing annotations"""

    if self.keypoints is None: self.create_keypoints()
    if annotations is None: annotations = self.keypoint_config #default
    for i, k in enumerate(self.keypoints):
      for obj in [item for sublist in k[2] for item in sublist]:
        self.canvas.move(obj, annotations[i][0]-k[0], annotations[i][1]-k[1])
      k[0] = annotations[i][0]
      k[1] = annotations[i][1]
    for k in self.keypoints:
      for obj in [item for sublist in k[2][:2] for item in sublist]:
        self.canvas.itemconfig(obj, state=tkinter.NORMAL)
 
def process_arguments():

  import argparse

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  parser.add_argument('video', metavar='VIDEO', type=str,
      help="Video file to load")

  parser.add_argument('config', metavar='FILE', type=str,
      help="Base keypoint/input configuration. You should provide an annotation file with at least one annotation that can be used as the keypoint configuration.")

  parser.add_argument('-c', '--cache', dest='cache', metavar='INT',
      type=int, default=0, help="Number of frames to cache in a video stream (defaults to %(default)s; a value smaller or equal to zero disables the cache)")

  parser.add_argument('-z', '--zoom', dest='zoom', metavar='N',
      type=float, default=1,
      help="Zoom in/out by the given factor (defaults to %(default)s; values between 0 and 1 will zoom-out while values greater then 1 will zoom-in)")

  parser.add_argument('-d', '--annotation-radius', dest='radius',
      metavar='N', type=int, default=2, 
      help="Diameter of visual keypoints while annotating (defaults to %(default)s)")

  parser.add_argument('-s', '--skip-factor', dest='skip_factor',
      metavar='N', type=int, default=5,
      help="Default skip factor for frame and point seeking (if you press SHIFT together with motion keys, we still only move 1 frame/point each time; defaults to %(default)s)")

  parser.add_argument('-S', '--start', dest='start',
      metavar='N', type=int, default=0,
      help="Which frame number to display first (defaults to %(default)s)")

  parser.add_argument('-o', '--output', dest='output',
      metavar='FILE', type=str, default=None,
      help="Output file that will contain the annotations recorded at this session (if not given, dump to stdout; if file exists, a backup is made)")

  from ..version import __version__
  name = os.path.basename(os.path.splitext(sys.argv[0])[0])
  parser.add_argument('-V', '--version', action='version',
      version='Video Keypoint Annotation Tool v%s (%s)' % (__version__, name))
  
  args = parser.parse_args()

  if not os.path.exists(args.video):
    parser.error("Input video file '%s' cannot be read" % args.video)

  if args.zoom <= 0:
    parser.error("This app does not accept zooming out ! Choose a zoom factor that is >= 1.")

  if args.radius <= 0:
    parser.error("Cannot have annotations with a radius <= 0")

  if args.skip_factor <= 0:
    parser.error("Cannot use a skip factor <= 0")

  if not os.path.exists(args.config):
    parser.error("Input configuration file '%s' cannot be read" %
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

def check_config(data, shape):
  """Checks the configuration for inconsistencies w.r.t. the input video
  shape."""

  for x,y,l in data:

    if x >= shape[2]:
      raise RuntimeError, 'Keypoint configuration "%s" has an "x" value (%d) greater or equal the video width (%d)' % (l, x, shape[2])
    if y >= shape[1]:
      raise RuntimeError, 'Keypoint configuration "%s" has an "y" value (%d) greater or equal the video height (%d)' % (l, y, shape[1])

def load_config(filename, shape):
  """Loads the keypoint configuration/input file, checks the input shape for
  problems."""

  from ...io import load, check_input

  data, header = load(filename)

  if not data:
    raise RuntimeError, 'No keypoints found at %s' % filename

  config = [(x,y,l) for ((x,y),l) in zip(data[min(data.keys())], header)]

  check_config(config, shape)
  check_input(data, header, shape)

  return config, data

def main():

  from ..cache import Video

  args = process_arguments()
 
  sys.stdout.write("Loading input video from '%s' (cache=%d)..." % \
      (args.video, args.cache))
  sys.stdout.flush()
  v = Video(args.video, N=args.cache, mid=args.start)

  sys.stdout.write("OK!\nLoading keypoint configuration at '%s'..." % \
      (args.config,))
  sys.stdout.flush()
  config, input = load_config(args.config, v.shape)

  sys.stdout.write(" OK!\nLaunching annotation interface...\n")
  sys.stdout.flush()

  app = AnnotatorApp(v, args.zoom, args.radius, args.skip_factor, config,
      input, args.output, args.start)
  app.mainloop()

if __name__ == '__main__':
  main()
