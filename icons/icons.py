import bpy.utils.previews
from ..utils import absolute_path
import os

class IconsLoader:

    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(IconsLoader, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    @classmethod
    def instance(cls):
        return cls()

    def __init__(self):
        if self.initialized:
            return
        self.icons = None
        self.initialized = True

    def get_icon_id(self, name):
        return self.icons[name].icon_id
    
    @classmethod
    def register(cls):
        icons_loader = cls.instance()
        icons_loader.icons = bpy.utils.previews.new()
        for icon_filename in os.listdir(absolute_path("./icons")):
            if icon_filename.endswith(".png"):
                icon_basename = icon_filename.split(".")[0]
                icon_filepath = absolute_path(f"./icons/{icon_filename}")
                icons_loader.icons.load(icon_basename, icon_filepath, "IMAGE")

    @classmethod
    def unregister(cls):
        icons_loader = cls.instance()
        bpy.utils.previews.remove(icons_loader.icons)
        icons_loader.icons = None


