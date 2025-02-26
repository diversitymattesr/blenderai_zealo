from bpy.app.translations import pgettext as _
import bpy
from .lists import *
from ...icons import IconsLoader
from ...operators.trellis import *

class Trellis_PT_Panel(bpy.types.Panel):
    bl_idname = "BLENDER_ZEALO_TRELLISGEN_PT_Panel"
    bl_label = _("Trellis Generator", '*')
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = _("Trellis", '*')

    @classmethod
    def poll(cls, context):
        gen_props = context.scene.gen_props
        return gen_props.trellis_ready and gen_props.show_trellis
    
    def draw(self, context):
        icons_loader = IconsLoader.instance()
        trellisgen_props = context.scene.trellisgen_props
        layout = self.layout
        layout.label(text=_("Image to 3D Tasks", '*'), icon_value=icons_loader.get_icon_id("image"))
        layout.template_list(
            Trellisgen_UL_Image23D_Tasks.bl_idname, 
            "", 
            trellisgen_props, 
            "img23d_tasks", 
            trellisgen_props, 
            "img23d_tasks_active_index", 
        )
        row = layout.row()
        row.operator(Trellis_OT_AddImg23DTask.bl_idname, text=_("Add", 'Operator'), icon_value=icons_loader.get_icon_id("plus"))
        row.operator(Trellisgen_OT_RemoveFailedImg23DTask.bl_idname, text=_("Remove Failed", '*'), icon_value=icons_loader.get_icon_id("remove"))
        row.operator(Trellisgen_OT_RewatchImg23DTask.bl_idname, text=_("Rewatch", '*'), icon_value=icons_loader.get_icon_id("eye"))
        row.operator(Trellisgen_OT_RedownloadImg23DTask.bl_idname, text=_("Redownload", '*'), icon_value=icons_loader.get_icon_id("download"))
        row.operator(Trellis_OT_ImportModelOfImg23DTask.bl_idname, text=_("Import", '*'), icon_value=icons_loader.get_icon_id("download"))

        
        
        