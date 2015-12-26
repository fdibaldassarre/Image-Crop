#!/usr/bin/env python3

import os
import configparser

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from PIL import Image

path = os.path.abspath(__file__)
MAIN_FOLDER = os.path.dirname(path)

BORDER_SIZE = 4
BORDER_SIZE_POINTER = 8

RESIZE_CORRECTION = 4

WIN_WIDTH = 800
WIN_HEIGHT = 600

RESIZE_NONE = 0
RESIZE_RIGHT = 1
RESIZE_LEFT = 2
RESIZE_TOP = 4
RESIZE_BOTTOM = 8

RESIZE_TOP_RIGHT = RESIZE_TOP + RESIZE_RIGHT
RESIZE_TOP_LEFT = RESIZE_TOP + RESIZE_LEFT
RESIZE_BOTTOM_RIGHT = RESIZE_BOTTOM + RESIZE_RIGHT
RESIZE_BOTTOM_LEFT = RESIZE_BOTTOM + RESIZE_LEFT

MIN_WIDTH = 20

SELECTOR_COLOUR = (0.533, 0.03, 0.576)

CONFIG_SECTION = 'Image-Crop'
CONFIG_DEFAULT = {'RatioWidth' : '16',
                  'RatioHeight' : '9',
                  'FixRatio' : 'True',
                  'SelectorR' : '0.533',
                  'SelectorG' : '0.03',
                  'SelectorB' : '0.576'
                 }

## SELECTOR
class Selector():
  
  def __init__(self, interface):
    self.interface = interface
    # selector data
    self.x = 0
    self.y = 0
    self.width = MIN_WIDTH
    self.height = MIN_WIDTH
    self.min_size = MIN_WIDTH
    self.max_width = 10
    self.max_height = 10
    self.ratio_width = 16
    self.ratio_height = 9
    self.fix_ratio = True
    self.colour = SELECTOR_COLOUR
    # selector
    self.selector = self.interface.builder.get_object('Selector')
    self.setWidth(self.width)
    self.selector.connect('draw', self.draw)
  
  def draw(self, widget, cr):
    r, g, b = self.colour
    r_i = min(r + 0.2, 1)
    g_i = min(g + 0.2, 1)
    b_i = min(b + 0.2, 1)
    # border
    cr.set_source_rgba(r, g, b, 1)
    # border - top
    cr.rectangle(0, 0, self.width, BORDER_SIZE)
    cr.fill()
    # border - right
    cr.rectangle(self.width-BORDER_SIZE, 0, BORDER_SIZE, self.height)
    cr.fill()
    # border - bottom
    cr.rectangle(0, self.height-BORDER_SIZE, self.width, BORDER_SIZE)
    cr.fill()
    # border - left
    cr.rectangle(0, 0, BORDER_SIZE, self.height)
    cr.fill()
    # inside
    cr.set_source_rgba(r_i, g_i, b_i, 0.3)
    cr.rectangle(BORDER_SIZE, BORDER_SIZE, self.width-2*BORDER_SIZE, self.height-2*BORDER_SIZE)
    cr.fill()
    return False
  
  # GET
  def getPosition(self):
    return self.x, self.y
  
  def getSize(self):
    return self.width, self.height
  
  def getColour(self):
    return self.colour
  
  def getRatio(self):
    return self.ratio_width, self.ratio_height
  
  def getFixRatio(self):
    return self.fix_ratio
  
  def getValidWidth(self, width):
    if width <= 0:
      width = 1
    elif self.x + width > self.max_width:
      width = self.max_width - self.x
    return width
  
  def getValidHeight(self, height):
    if height <= 0:
      height = 1
    elif self.y + height > self.max_height:
      height = self.max_height - self.y
    return height
  
  def getValidPosition(self, x, y):
    if x < 0:
      x = 0
    elif x + self.width > self.max_width:
      x = self.max_width - self.width
    if y < 0:
      y = 0
    elif y + self.height > self.max_height:
      y = self.max_height - self.height
    return x, y
  
  def getResizeType(self, x, y):
    width, height = self.width, self.height
    frame_x, frame_y = self.x, self.y
    # check if inside/left/right/top/bottom
    inside = x >= frame_x and x <= frame_x + width and \
             y >= frame_y and y <= frame_y + height
    left = x >= frame_x and x <= frame_x + BORDER_SIZE_POINTER
    right = x >= frame_x + width - BORDER_SIZE_POINTER and x <= frame_x + width
    top = y >= frame_y and y <= frame_y + BORDER_SIZE_POINTER
    bottom = y >= frame_y + height - BORDER_SIZE_POINTER and y <= frame_y + height
    # confront results
    if not inside:
      resize = RESIZE_NONE
    else:
      if top and left:
        resize = RESIZE_TOP_LEFT
      elif top and right:
        resize = RESIZE_TOP_RIGHT
      elif bottom and left:
        resize = RESIZE_BOTTOM_LEFT
      elif bottom and right:
        resize = RESIZE_BOTTOM_RIGHT
      elif left:
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
  
  # CHECK
  def checkRatio(self):
    # TODO: better
    self.setWidth(self.width)
    self.setHeight(self.height)
  
  def isValidPosition(self, x, y):
    return x >= 0 and x + self.width <= self.max_width and \
           y >= 0 and y + self.height <= self.max_height
  
  def isPositionInternal(self, x, y):
    return x >= self.x and x <= self.x + self.width and \
           y >= self.y and y <= self.y + self.height
  
     
  # SET
  def setSizeMin(self, size):
    self.min_size = size
  
  def setSizeMax(self, width, height):
    self.max_width = width
    self.max_height = height
  
  def setRatio(self, ratio_width, ratio_height):
    self.ratio_width = ratio_width
    self.ratio_height = ratio_height
  
  def fixRatio(self, fix=True):
    self.fix_ratio = fix
  
  def setColour(self, colour):
    self.colour = colour
  
  def set(self, x, y, width, height):
    self.moveTo(x, y)
    self.setSize(width, height)
  
  def setWidth(self, width):
    width = self.getValidWidth(width)
    if self.fix_ratio:
      height = width * self.ratio_height / self.ratio_width
    else:
      height = self.height
    if width >= self.min_size and height >= self.min_size and \
       self.x + width <= self.max_width and self.y + height <= self.max_height:
      self.setSize(width, height)
  
  def setHeight(self, height):
    height = self.getValidHeight(height)
    if self.fix_ratio:
      width = height * self.ratio_width / self.ratio_height
    else:
      width = self.width
    if width >= self.min_size and height >= self.min_size and \
       self.x + width <= self.max_width and self.y + height <= self.max_height:
      self.setSize(width, height)
  
  def setSize(self, width, height):
    self.width = width
    self.height = height
    self.selector.set_size_request(self.width, self.height)
  
  # MOVE
  def move(self, x, y):
    x, y = self.getValidPosition(x, y)
    self.moveTo(x, y)
  
  def moveTo(self, x, y):
    self.x = x
    self.y = y
    self.interface.overlay.move(self.selector, x, y)
    
  # RESIZE
  def resizeBottom(self, x, y):
    y = y + RESIZE_CORRECTION
    y_s = self.y
    y_e = min(max(y, y_s + self.min_size), self.max_height)
    height = y_e - y_s
    width = int(height * self.ratio_width / self.ratio_height)
    # fit width in image
    x_s, width = self.fitWidth(width)
    if self.fix_ratio:
      height = int(width * self.ratio_height / self.ratio_width)
    # set
    start_x = x_s
    start_y = y_s
    self.set(start_x, start_y, width, height)
  
  def resizeTop(self, x, y):
    y = y - RESIZE_CORRECTION
    y_e = self.y + self.height
    y_s = min(max(y, 0), y_e - self.min_size)
    height = y_e - y_s
    width = int(height * self.ratio_width / self.ratio_height)
    # fit width in image
    x_s, width = self.fitWidth(width)
    if self.fix_ratio:
      height = int(width * self.ratio_height / self.ratio_width)
    y_s = y_e - height
    # set
    start_x = x_s
    start_y = y_s
    self.set(start_x, start_y, width, height)
  
  def resizeRight(self, x, y):
    x = x + RESIZE_CORRECTION
    x_s = self.x
    x_e = min(max(x, x_s + self.min_size), self.max_width)
    width = x_e - x_s
    height = int(width * self.ratio_height / self.ratio_width)
    # fit width in image
    y_s, height = self.fitHeight(height)
    if self.fix_ratio:
      width = int(height * self.ratio_width / self.ratio_height)
    # set
    start_x = x_s
    start_y = y_s
    self.set(start_x, start_y, width, height)
  
  def resizeLeft(self, x, y):
    x = x - RESIZE_CORRECTION
    x_e = self.x + self.width
    x_s = min(max(x, 0), x_e - self.min_size)
    width = x_e - x_s
    height = int(width * self.ratio_height / self.ratio_width)
    # fit width in image
    y_s, height = self.fitHeight(height)
    if self.fix_ratio:
      width = int(height * self.ratio_width / self.ratio_height)
    x_s = x_e - width
    # set
    start_x = x_s
    start_y = y_s
    self.set(start_x, start_y, width, height)
  
  def resizeTopLeft(self, x, y):
    x_e = self.x + self.width
    y_e = self.y + self.height
    x_s = min(max(x, 0), x_e - self.min_size)
    y_s = min(max(y, 0), y_e - self.min_size)
    # Fit selection
    area_width = x_e - x_s
    area_height = y_e - y_s
    width, height = self.fitToArea(area_width, area_height)
    # Set starting point
    start_x = x_e - width
    start_y = y_e - height
    self.set(start_x, start_y, width, height)
  
  def resizeTopRight(self, x, y):
    x_s = self.x
    y_e = self.y + self.height
    x_e = min(max(x, x_s + self.min_size), self.max_width)
    y_s = min(max(y, 0), y_e - self.min_size)
    # Fit selection
    area_width = x_e - x_s
    area_height = y_e - y_s
    width, height = self.fitToArea(area_width, area_height)
    # Set starting point
    start_x = x_s
    start_y = y_e - height
    self.set(start_x, start_y, width, height)
  
  def resizeBottomLeft(self, x, y):
    x_e = self.x + self.width
    y_s = self.y
    x_s = min(max(x, 0), x_e - self.min_size)
    y_e = min(max(y, y_s + self.min_size), self.max_height)
    # Fit selection
    area_width = x_e - x_s
    area_height = y_e - y_s
    width, height = self.fitToArea(area_width, area_height)
    # Set starting point
    start_x = x_e - width
    start_y = y_s
    self.set(start_x, start_y, width, height)
  
  def resizeBottomRight(self, x, y):
    x_s = self.x
    y_s = self.y
    x_e = min(max(x, x_s + self.min_size), self.max_width)
    y_e = min(max(y, y_s + self.min_size), self.max_height)
    # Fit selection
    area_width = x_e - x_s
    area_height = y_e - y_s
    width, height = self.fitToArea(area_width, area_height)
    # Set starting point
    start_x = x_s
    start_y = y_s
    self.set(start_x, start_y, width, height)
  
  # FITTING
  def fitToArea(self, area_width, area_height):
    if self.fix_ratio:
      factor_w = area_width / self.ratio_width
      factor_h = area_height / self.ratio_height
      if factor_h < factor_w:
        # fit height
        height = area_height
        width = int(height * self.ratio_width / self.ratio_height)
      else:
        # fit width
        width = area_width
        height = int(width * self.ratio_height / self.ratio_width)
    else:
      height = area_height
      width = area_width
    return width, height
  
  def fitWidth(self, width):
    if not self.fix_ratio:
      return self.x, self.width
    if width > self.max_width:
      width = self.max_width
      x_s = 0
      x_e = self.max_width
      return x_s, width
    lim = int((width - self.width)/2)
    x_s = self.x - lim
    x_e = x_s + width
    if x_s < 0:
      x_s = 0
      x_e = width
    elif x_e > self.max_width:
      x_e = self.max_width
      x_s = self.max_width - width
    return x_s, width
  
  def fitHeight(self, height):
    if not self.fix_ratio:
      return self.y, self.height
    if height > self.max_height:
      height = self.max_height
      y_s = 0
      y_e = self.max_height
      return y_s, height
    lim = int((height - self.height)/2)
    y_s = self.y - lim
    y_e = self.y + self.height + lim
    if y_s < 0:
      y_s = 0
      y_e = height
    elif y_e > self.max_height:
      y_e = self.max_height
      y_s = self.max_height - height
    return y_s, height
  
## INTERFACE
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
    # load settings
    self.loadSettings()
    # load events and accels
    self.loadEvents()
    self.loadAccels()
    # variables
    self.drag = False
    self.resize = RESIZE_NONE
    self.resize_start = False
    # load Selector
    self.loadSelector()
    # setup
    self.setupRatioSelector()
    self.setupFixRatio()
    self.setupSaveButton()
    self.setupColourChooser()
  
  
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
      max_width, max_height = allocation.width, allocation.height
      self.selector.setSizeMax(max_width, max_height)
      # set selector to 1/2 image width
      self.selector.setWidth(max_width / 2)
      self.selector.setHeight(max_height / 2)
  
  def start(self):
    self.show()
    Gtk.main()
  
  def close(self, *args):
    self.saveSettings()
    Gtk.main_quit()
  
  
  ## SETTINGS LOAD/SAVE
  def loadSettings(self):
    self.config = configparser.SafeConfigParser(CONFIG_DEFAULT)
    config_folder = os.path.join(os.environ['HOME'], ".config/imc-image-crop/")
    if not os.path.exists(config_folder):
      os.mkdir(config_folder)
    self.config_file = os.path.join(config_folder, 'config.txt')
    self.config.read(self.config_file)
    if not CONFIG_SECTION in self.config.sections():
      self.config[CONFIG_SECTION] = {}
  
  def getConfig(self, param):
    return self.config.get(CONFIG_SECTION, param)
  
  def getConfigBool(self, param):
    if self.config.get(CONFIG_SECTION, param).lower() == 'true':
      return True
    else:
      return False
  
  def setConfig(self, param, value):
    self.config[CONFIG_SECTION][param] = str(value)
  
  def saveSettings(self):
    # read current settings
    self.setConfigRatio()
    self.setConfigFixRatio()
    self.setConfigSelectorColour()
    # save
    self.config.write(open(self.config_file, 'w'))
  
  # GET CONFIG
  def getConfigRatio(self):
    ratio_width = int(self.getConfig('RatioWidth'))
    ratio_height = int(self.getConfig('RatioHeight'))
    return ratio_width, ratio_height
  
  def getConfigFixRatio(self):
    return self.getConfigBool('FixRatio')
  
  def getConfigSelectorColour(self):
    r = float(self.getConfig('SelectorR'))
    g = float(self.getConfig('SelectorG'))
    b = float(self.getConfig('SelectorB'))
    return r, g, b
  
  # SET CONFIG
  def setConfigRatio(self):
    ratio_width, ratio_height = self.selector.getRatio()
    self.setConfig('RatioWidth', ratio_width)
    self.setConfig('RatioHeight', ratio_height)
    
  def setConfigFixRatio(self):
    fix = self.selector.getFixRatio()
    self.setConfig('FixRatio', fix)
  
  def setConfigSelectorColour(self):
    r, g, b = self.selector.getColour()
    self.setConfig('SelectorR', r)
    self.setConfig('SelectorG', g)
    self.setConfig('SelectorB', b)
  
  ## INTERFACE SETUP
  def loadAccels(self):
    accels = Gtk.AccelGroup()
    accelerator = '<control>s'
    key, mod = Gtk.accelerator_parse(accelerator)
    accels.connect(key, mod, Gtk.AccelFlags.LOCKED, self.saveResized)
    accelerator = '<control>q'
    key, mod = Gtk.accelerator_parse(accelerator)
    accels.connect(key, mod, Gtk.AccelFlags.LOCKED, self.close)
    self.main_window.add_accel_group(accels)
  
  def setupRatioSelector(self): 
    ratio_entry = self.builder.get_object('RatioEntry')
    ratio_width, ratio_height = self.selector.getRatio()
    ratio_txt = str(ratio_width) + ':' + str(ratio_height)
    ratio_entry.set_active_id(ratio_txt)
    ratio_entry.connect('changed', self.onRatioChanged)
  
  def onRatioChanged(self, widget):
    model = widget.get_model()
    index = widget.get_active()
    el = model[index][0]
    ratio_txt = model[index][1]
    width, height = ratio_txt.split(':')
    width = int(width)
    height = int(height)
    self.selector.setRatio(width, height)
    # check selector ratio
    self.selector.checkRatio()
  
  def setupFixRatio(self):
    fix_button = self.builder.get_object('FixRatio')
    fix_button.set_active(self.selector.getFixRatio())
    fix_button.connect('toggled', self.onFixRatioChanged)
  
  def onFixRatioChanged(self, widget):
    if widget.get_active():
      self.selector.fixRatio()
      self.selector.checkRatio()
    else:
      self.selector.fixRatio(False)
  
  def setupSaveButton(self):
    btn = self.builder.get_object('SaveButton')
    btn.connect('clicked', self.saveResized)
  
  def setupColourChooser(self):
    btn = self.builder.get_object('ChooseColourButton')
    colour = self.selector.getColour()
    btn.set_rgba(Gdk.RGBA(*colour))
    btn.connect('color-set', self.changeSelectorColour)
  
  def changeSelectorColour(self, widget):
    r, g, b, a = widget.get_rgba()
    self.selector.setColour((r,g,b))
  
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
    self.selector = Selector(self)
    ratio_w, ratio_h = self.getConfigRatio()
    self.selector.setRatio(ratio_w, ratio_h)
    fix = self.getConfigFixRatio()
    self.selector.fixRatio(fix)
    colour = self.getConfigSelectorColour()
    self.selector.setColour(colour)
  
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
    elif self.selector.isPositionInternal(x, y):
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
        resize_type = self.selector.getResizeType(x, y)
        self.resize = resize_type
        self.setPointerResize(resize_type)
      elif self.drag:
        # drag selector
        position = x, y
        self.moveSelectorTo(position)
      elif self.resize_start:
        # resize selector
        position = x, y
        self.resizeSelectorTo(position)
    
  def moveSelectorTo(self, end_pos):
    # calculate new position
    x_s, y_s = self.drag_start_position
    x_e, y_e = end_pos
    # delta
    delta_x = x_e - x_s
    delta_y = y_e - y_s
    # new position
    x, y = self.selector.getPosition()
    new_x = x + delta_x
    new_y = y + delta_y
    self.selector.move(new_x, new_y)
    # set new starting position
    self.drag_start_position = end_pos
  
  def resizeSelectorTo(self, end_pos):
    # starting position
    x_s, y_s = self.resize_start_point
    x_e, y_e = end_pos
    # delta
    delta_x = x_e - x_s
    delta_y = y_e - y_s
    # end size depends on resize type
    if self.resize == RESIZE_BOTTOM:
      self.selector.resizeBottom(x_e, y_e)
    elif self.resize == RESIZE_RIGHT:
      self.selector.resizeRight(x_e, y_e)
    elif self.resize == RESIZE_TOP:
      self.selector.resizeTop(x_e, y_e)
    elif self.resize == RESIZE_LEFT:
      self.selector.resizeLeft(x_e, y_e)
    elif self.resize == RESIZE_TOP_LEFT:
      self.selector.resizeTopLeft(x_e, y_e)
    elif self.resize == RESIZE_TOP_RIGHT:
      self.selector.resizeTopRight(x_e, y_e)
    elif self.resize == RESIZE_BOTTOM_LEFT:
      self.selector.resizeBottomLeft(x_e, y_e)
    elif self.resize == RESIZE_BOTTOM_RIGHT:
      self.selector.resizeBottomRight(x_e, y_e)
    # set new start position
    self.resize_start_point = end_pos
  
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
    elif border_type == RESIZE_TOP_LEFT:
      self.changeCursorType(Gdk.CursorType.TOP_LEFT_CORNER)
    elif border_type == RESIZE_TOP_RIGHT:
      self.changeCursorType(Gdk.CursorType.TOP_RIGHT_CORNER)
    elif border_type == RESIZE_BOTTOM_LEFT:
      self.changeCursorType(Gdk.CursorType.BOTTOM_LEFT_CORNER)
    elif border_type == RESIZE_BOTTOM_RIGHT:
      self.changeCursorType(Gdk.CursorType.BOTTOM_RIGHT_CORNER)
    else:
      self.changeCursorType(Gdk.CursorType.LEFT_PTR)
  
  def resetCursor(self):
    self.changeCursorType(Gdk.CursorType.LEFT_PTR)
  
  def changeCursorType(self, cursor_type):
    window = self.main_window.get_window()
    display = Gdk.Display.get_default()
    cursor = Gdk.Cursor.new_for_display(display, cursor_type)
    window.set_cursor(cursor)
  
  def saveResized(self, *args):
    selector_width, selector_height = self.selector.getSize()
    width, height = selector_width / self.scale_factor, selector_height / self.scale_factor
    selector_x, selector_y = self.selector.getPosition()
    x, y = selector_x / self.scale_factor, selector_y / self.scale_factor
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
    
