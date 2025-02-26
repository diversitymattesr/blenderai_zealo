from bpy.app.translations import pgettext as _
import bpy


class BlenderAIZealoPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    @staticmethod
    def register():
        pass

    tripo_api_key: bpy.props.StringProperty(
        name=_("Tripo API Key", '*'), 
        default=""
    )

    def draw(self, context):
        layout =self.layout
        layout.prop(self, "tripo_api_key")