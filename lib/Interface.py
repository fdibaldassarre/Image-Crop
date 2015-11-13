#!/usr/bin/env python3

import os
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from PIL import Image

path = os.path.abspath(__file__)
MAIN_FOLDER = os.path.dirname(path)

BORDER_SIZE = 3
BORDER_SIZE_POINTER = 8

WIN_WIDTH = 800
WIN_HEIGHT = 600

RESIZE_NONE = 0
RESIZE_RIGHT = 1
RESIZE_LEFT = 2
RESIZE_TOP = 4
RESIZE_BOTTOM = 8

MIN_WIDTH = 20

class Interface():

  def __init__(self, imagepath):
    self.imagepath = imagepath
    self.builder = Gtk.Builder.new()
    ui_file = os.path.join(MAIN_FOLDER, 'ui/Main.glade')
    self.builder.add_from_file(ui_file)
    #self.loadCss()
    self.main_window = self.builder.get_object('MainWindow')
    self.main_window.connect('destroy', self.close)
    self.overlay = self.builder.get_object('Overlay')
    if self.loadImage():
      self.load_error = False
      self.setupAll()
    else:
      self.load_error = True
  
  def setupAll(self):
    image_name = os.path.basename(self.imagepath)
    self.main_window.set_title(image_name)
    # load events and accels
    self.loadEvents()
    self.loadAccels()
    # variables
    self.drag = False
    self.resize = RESIZE_NONE
    self.resize_start = False
    self.selector_x = 0
    self.selector_y = 0
    self.selector_width = 10
    self.selector_height = 10
    self.max_width = 20
    self.max_height = 20
    self.min_size = MIN_WIDTH
    self.ratio_height = 9
    self.ratio_width = 16
    self.fix_ratio = True
    # setup
    self.setupRatioSelector()
    self.setupFixRatio()
    self.setupSaveButton()
    # load Selector
    self.loadSelector()
  
  
  def show(self):
    self.main_window.show_all()
    self.hideInfoBar()
    if self.load_error:
      controls = self.builder.get_object('ControlsGrid')
      controls.hide()
      self.main_window.set_title('Error loading image')
      self.main_window.set_size_request(20, 20)
    else:
      overlay = self.builder.get_object('Overlay')
      allocation = overlay.get_allocation()
      self.max_width, self.max_height = allocation.width, allocation.height
      # set selector to 1/2 image width
      self.setSelectorWidth(self.max_width / 2)
  
  def start(self):
    self.show()
    Gtk.main()
  
  def close(self, widget=None):
    Gtk.main_quit()
  
  '''
  def loadCss(self):
    display = Gdk.Display.get_default()
    screen = Gdk.Display.get_default_screen(display)
    provider = Gtk.CssProvider()
    Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    css_file = os.path.join(MAIN_FOLDER, 'css/style.css')
    provider.load_from_path(css_file)
  '''
  ## INTERFACE SETUP
  
  def loadAccels(self):
    accels = Gtk.AccelGroup()
    accelerator = '<control>s'
    key, mod = Gtk.accelerator_parse(accelerator)
    accels.connect(key, mod, Gtk.AccelFlags.LOCKED, self.saveResized)
    self.main_window.add_accel_group(accels)
  
  def setupRatioSelector(self): 
    ratio_entry = self.builder.get_object('RatioEntry')
    ratio_entry.set_active(0)
    ratio_entry.connect('changed', self.onRatioChanged)
  
  def onRatioChanged(self, widget):
    model = widget.get_model()
    index = widget.get_active()
    el = model[index][0]
    if el == 0:
      # ratio 16:9
      self.ratio_width = 16
      self.ratio_height = 9
    elif el == 1:
      # ratio 4:3
      self.ratio_width = 4
      self.ratio_height = 3
    elif el == 2:
      # ratio 1:1
      self.ratio_width = 1
      self.ratio_height = 1
    # trigger selector redraw
    self.setSelectorWidth(self.selector_width)
    self.setSelectorHeight(self.selector_height)
  
  def setupFixRatio(self):
    fix_button = self.builder.get_object('FixRatio')
    fix_button.connect('toggled', self.onFixRatioChanged)
  
  def onFixRatioChanged(self, widget):
    self.fix_ratio = widget.get_active()
    if self.fix_ratio:
      self.setSelectorWidth(self.selector_width)
      self.setSelectorHeight(self.selector_height)
  
  def setupSaveButton(self):
    btn = self.builder.get_object('SaveButton')
    btn.connect('clicked', self.saveResized)
  
  ## INTERFACE - INFO LABEL
  def showInfoMessage(self, message, duration=3000):
    label = self.builder.get_object('InfoBarLabel')
    label.set_text(message)
    self.showInfoBar()
    if duration is not None:
      GObject.timeout_add(duration, self.hideInfoBar)
  
  def showInfoBar(self, *args):
    bar = self.builder.get_object('InfoBar')
    bar.show_all()
    return False
  
  def hideInfoBar(self, *args):
    bar = self.builder.get_object('InfoBar')
    bar.hide()
    return False
    
    
  ## IMAGE OPERATIONS
  
  def loadImage(self):
    try:
      image = self.builder.get_object('Image')
      pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.imagepath)
      pixbuf = self.resizeImage(pixbuf)
      image.set_from_pixbuf(pixbuf)
      return True
    except Exception:
      return False
  
  def resizeImage(self, pixbuf):
    width = pixbuf.get_width()
    height = pixbuf.get_height()
    factor_w = WIN_WIDTH / width
    factor_h = WIN_HEIGHT / height
    factor = min(factor_w, factor_h, 1.0)
    self.scale_factor = factor
    new_width = width * self.scale_factor
    new_height = height * self.scale_factor
    return pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)
  
  def loadSelector(self):
    self.selector = self.builder.get_object('Selector')
    self.setSelectorWidth(self.selector_width)
    self.selector.connect('draw', self.drawSelector)
  
  def drawSelector(self, widget, cr):
    width, height = self.selector_width, self.selector_height
    # border
    cr.set_source_rgba(0.533, 0.03, 0.576, 1)
    # border - top
    cr.rectangle(0, 0, width, BORDER_SIZE)
    cr.fill()
    # border - right
    cr.rectangle(width-BORDER_SIZE, 0, BORDER_SIZE, height)
    cr.fill()
    # border - bottom
    cr.rectangle(0, height-BORDER_SIZE, width, BORDER_SIZE)
    cr.fill()
    # border - left
    cr.rectangle(0, 0, BORDER_SIZE, height)
    cr.fill()
    # inside
    cr.set_source_rgba(0.768, 0.03, 0.835, 0.3)
    cr.rectangle(BORDER_SIZE, BORDER_SIZE, width-2*BORDER_SIZE, height-2*BORDER_SIZE)
    cr.fill()
    return False
  
  def setSelectorWidth(self, width):
    width = self.getSelectorValidWidth(width)
    if self.fix_ratio:
      height = width * self.ratio_height / self.ratio_width
    else:
      height = self.selector_height
    if width >= self.min_size and height >= self.min_size:
      self.setSelectorSize(width, height)
  
  def setSelectorHeight(self, height):
    height = self.getSelectorValidHeight(height)
    if self.fix_ratio:
      width = height * self.ratio_width / self.ratio_height
    else:
      width = self.selector_width
    if width >= self.min_size and height >= self.min_size:
      self.setSelectorSize(width, height)
    
  def setSelectorSize(self, width, height):
    if self.validSelectorSizes(width, height):
      self.selector_width = width
      self.selector_height = height
      self.selector.set_size_request(self.selector_width, self.selector_height)

  def getSelectorValidWidth(self, width):
    if width <= 0:
      width = 1
    elif self.selector_x + width > self.max_width:
      width = self.max_width - self.selector_x
    return width
  
  def getSelectorValidHeight(self, height):
    if height <= 0:
      height = 1
    elif self.selector_y + height > self.max_height:
      height = self.max_height - self.selector_y
    return height
  
  def moveSelector(self, x, y):
    x, y = self.getValidSelectorPositions(x, y)
    self.selector_x = x
    self.selector_y = y
    self.overlay.move(self.selector, x, y)
      
  def validSelectorSizes(self, width, height):
    return width >= 0 and self.selector_x + width <= self.max_width and \
           height >= 0 and self.selector_y + height <= self.max_height
  
  def getValidSelectorPositions(self, x, y):
    if x < 0:
      x = 0
    elif x + self.selector_width > self.max_width:
      x = self.max_width - self.selector_width
    if y < 0:
      y = 0
    elif y + self.selector_height > self.max_height:
      y = self.max_height - self.selector_height
    return x, y
    
  def validSelectorPosition(self, x, y):
    return x >= 0 and x + self.selector_width <= self.max_width and \
           y >= 0 and y + self.selector_height <= self.max_height
  
  def positionInSelector(self, x, y):
    return x >= self.selector_x and x <= self.selector_x + self.selector_width and \
           y >= self.selector_y and y <= self.selector_y + self.selector_height
  
  def loadEvents(self):
    self.main_window.connect("motion-notify-event", self.onMouseMovement)
    eventbox = self.builder.get_object('OverlayEventBox')
    eventbox.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
    #eventbox.connect("motion-notify-event", self.onMouseMovement)
    eventbox.connect("button-press-event", self.startDrag)
    eventbox.connect("button-release-event", self.stopDrag)
    
  
  def getOverlayRelativeCoordinates(self, x, y):
    overlay = self.builder.get_object('Overlay')
    alloc = overlay.get_allocation()
    return x, y - alloc.y
  
  
  def startDrag(self, widget, event):
    x, y = self.getOverlayRelativeCoordinates(event.x, event.y)
    if self.resize != RESIZE_NONE:
      self.resize_start = True
      self.resize_start_point = x, y
    elif self.positionInSelector(x, y):
      self.drag = True
      self.drag_start_position = x, y
      self.setPointerDrag(True)
  
  def stopDrag(self, widget, event):
    self.drag = False
    self.resize_start = False
    self.setPointerDrag(False)
  
  def onMouseMovement(self, widget, event):
    overlay = self.builder.get_object('Overlay')
    alloc = overlay.get_allocation()
    if event.y <= alloc.y:
      self.resetCursor()
    else:
      x, y = self.getOverlayRelativeCoordinates(event.x, event.y)
      if not self.drag and not self.resize_start:
        # check resize
        resize_type = self.pointerOnSelectorBorder(x, y)
        self.resize = resize_type
        self.setPointerResize(resize_type)
      elif self.drag:
        # drag selector
        position = x, y
        self.moveOverlayTo(position)
      elif self.resize_start:
        # resize selector
        position = x, y
        self.resizeOverlayTo(position)
    
  def moveOverlayTo(self, end_pos):
    # calculate new position
    x_s, y_s = self.drag_start_position
    x_e, y_e = end_pos
    # delta
    delta_x = x_e - x_s
    delta_y = y_e - y_s
    # new position
    new_x = self.selector_x + delta_x
    new_y = self.selector_y + delta_y
    self.moveSelector(new_x, new_y)
    # set new starting position
    self.drag_start_position = end_pos
  
  def resizeOverlayTo(self, end_pos):
    # starting position
    x_s, y_s = self.resize_start_point
    x_e, y_e = end_pos
    # delta
    delta_x = x_e - x_s
    delta_y = y_e - y_s
    # end size depends on resize type
    if self.resize == RESIZE_BOTTOM:
      new_height = self.selector_height + delta_y
      self.setSelectorHeight(new_height)
    elif self.resize == RESIZE_RIGHT:
      new_width = self.selector_width + delta_x
      self.setSelectorWidth(new_width)
    elif self.resize == RESIZE_TOP:
      self.resizeTop(delta_x, delta_y)
    elif self.resize == RESIZE_LEFT:
      self.resizeLeft(delta_x, delta_y)
    # set new start position
    self.resize_start_point = end_pos
  
  def resizeLeft(self, delta_x, delta_y):
    new_x = self.selector_x + delta_x
    new_width = self.selector_width - delta_x
    if delta_x < 0:
      # move and resize
      self.moveSelector(new_x, self.selector_y)
      if new_x == self.selector_x:
        self.setSelectorWidth(new_width)
    else:
      # resize and move
      self.setSelectorWidth(new_width)
      if self.selector_width == new_width:
        self.moveSelector(new_x, self.selector_y)
  
  def resizeTop(self, delta_x, delta_y):
    new_y = self.selector_y + delta_y
    new_height = self.selector_height - delta_y
    if delta_y > 0:
      # resize and move
      self.setSelectorHeight(new_height)
      if new_height == self.selector_height:
        self.moveSelector(self.selector_x, new_y)
    else:
      # move and resize
      self.moveSelector(self.selector_x, new_y)
      if new_y == self.selector_y:
        self.setSelectorHeight(new_height)
      
  def setPointerDrag(self, set_drag):
    if set_drag:
      self.changeCursorType(Gdk.CursorType.FLEUR)
    else:
      self.changeCursorType(Gdk.CursorType.LEFT_PTR)
  
  def setPointerResize(self, border_type):
    if border_type == RESIZE_NONE:
      self.changeCursorType(Gdk.CursorType.LEFT_PTR)
    elif border_type == RESIZE_TOP:
      self.changeCursorType(Gdk.CursorType.TOP_SIDE)
    elif border_type == RESIZE_BOTTOM:
      self.changeCursorType(Gdk.CursorType.BOTTOM_SIDE)
    elif border_type == RESIZE_RIGHT:
      self.changeCursorType(Gdk.CursorType.RIGHT_SIDE)
    elif border_type == RESIZE_LEFT:
      self.changeCursorType(Gdk.CursorType.LEFT_SIDE)
    else:
      self.changeCursorType(Gdk.CursorType.LEFT_PTR)
  
  def resetCursor(self):
    self.changeCursorType(Gdk.CursorType.LEFT_PTR)
  
  def changeCursorType(self, cursor_type):
    window = self.main_window.get_window()
    display = Gdk.Display.get_default()
    cursor = Gdk.Cursor.new_for_display(display, cursor_type)
    window.set_cursor(cursor)
  
  def getValidOverlayPosition(self, x0, y0, width, height):
    x1 = x0 + width
    y1 = y0 + height
    if x0 < 0:
      x0 = 0
    elif x0 + width > self.max_width:
      x0 = self.max_width - width
    if y0 < 0:
      y0 = 0
    elif y0 + height > self.max_height:
      y0 = self.max_height - height
    return x0, y0
  
  def getValidOverlaySize(self, x0, y0, width, height):
    x1 = x0 + width
    y1 = y0 + height
    if width <= 0:
      width = 1
    elif x0 + width > self.max_width:
      width = self.max_width - x0
    if height <= 0:
      height = 1
    elif y0 + height > self.max_height:
      height = self.max_height - y0
    height = width * self.ratio_height / self.ratio_width
    return width, height
  
  def pointerOnSelectorBorder(self, x, y):
    width, height = self.selector_width, self.selector_height
    frame_x, frame_y = self.selector_x, self.selector_y
    
    inside = x >= frame_x and x <= frame_x + width and \
             y >= frame_y and y <= frame_y + height
    
    left = x >= frame_x and x <= frame_x + BORDER_SIZE_POINTER
    right = x >= frame_x + width - BORDER_SIZE_POINTER and x <= frame_x + width
    
    top = y >= frame_y and y <= frame_y + BORDER_SIZE_POINTER
    bottom = y >= frame_y + height - BORDER_SIZE_POINTER and y <= frame_y + height
    
    if not inside:
      resize = RESIZE_NONE
    else:
      if left:
        resize = RESIZE_LEFT
      elif right:
        resize = RESIZE_RIGHT
      elif top:
        resize = RESIZE_TOP
      elif bottom:
        resize = RESIZE_BOTTOM
      else:
        resize = RESIZE_NONE
    
    return resize

  def saveResized(self, *args):
    width, height = self.selector_width / self.scale_factor, self.selector_height / self.scale_factor
    x, y = self.selector_x / self.scale_factor, self.selector_y / self.scale_factor
    base_img = Image.open(self.imagepath)
    base_img.load()
    new_img = base_img.crop((int(x), int(y), int(x+width), int(y+height)))
    image_folder = os.path.dirname(self.imagepath)
    image_name = os.path.basename(self.imagepath)
    basename, extension = os.path.splitext(image_name)
    # NOTE: force output extension to png
    extension = '.png'
    savename = basename + '.resized' + extension
    savepath = os.path.join(image_folder, savename)
    keep = True
    i = 1
    while keep:
      if os.path.exists(savepath):
        savename = basename + '.resized-' + str(i) + extension
        savepath = os.path.join(image_folder, savename)
      else:
        keep = False
      i += 1
    #print('Saving: ' + savepath)
    new_img.save(savepath)
    self.showInfoMessage('Image saved as ' + savename)
    
