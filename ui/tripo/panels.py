from bpy.app.translations import pgettext as _
import bpy
from .lists import *
from ...operators.tripogen import *

class Tripogen_PT_Panel(bpy.types.Panel):
    bl_idname = "BLENDER_ZEALO_TRIPOGEN_PT_Panel"
    bl_label = _('Tripo Generator', '*')
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = _('Tripo', '*')

    @classmethod
    def poll(cls, context):
        gen_props = context.scene.gen_props
        return gen_props.tripo_ready and gen_props.show_tripo
    
    def draw(self, context):
        tripogen_props = context.scene.tripogen_props
        icons_loader = IconsLoader.instance()
        layout = self.layout
        row = layout.row()
        row.label(text=_('Text to 3D Tasks', '*'))
        row = layout.row()
        row.template_list(
            Tripogen_UL_Text23D_Tasks.bl_idname, 
            "", 
            tripogen_props,
            "txt23d_tasks", 
            tripogen_props, 
            "txt23d_task_active_index", 
        )
        row = layout.row()
        row.operator(Tripogen_OT_AddTxt23DTask.bl_idname, text=_('Add', 'Operator'), icon_value=icons_loader.get_icon_id("plus"))
        row.operator(Tripogen_OT_RemoveFailedTxt23DTask.bl_idname, text=_('Remove Failed', '*'), icon_value=icons_loader.get_icon_id("remove"))
        row.operator(Tripogen_OT_RewatchTxt23DTask.bl_idname, text=_('Rewatch', '*'), icon_value=icons_loader.get_icon_id("eye"))
        row.operator(Tripogen_OT_RedownloadOfTxt23DTask.bl_idname, text=_('Redownload', '*'), icon_value=icons_loader.get_icon_id("model"))
        row.operator(Tripogen_OT_ImportModelOfTxt23DTask.bl_idname, text=_('Import', '*'), icon_value=icons_loader.get_icon_id("download"))
        row = layout.row()
        row.label(text=_('Image to 3D Tasks', '*'))
        row = layout.row()
        row.template_list(
            Tripogen_UL_Image23D_Tasks.bl_idname, 
            "", 
            tripogen_props,
            "img23d_tasks", 
            tripogen_props, 
            "img23d_task_active_index", 
        )
        row = layout.row()
        row.operator(Tripogen_OT_AddImg23DTask.bl_idname, text=_('Add', 'Operator'), icon_value=icons_loader.get_icon_id("plus"))
        row.operator(Tripogen_OT_RemoveFailedImg23DTask.bl_idname, text=_('Remove Failed', '*'), icon_value=icons_loader.get_icon_id("remove"))
        row.operator(Tripogen_OT_RewatchImg23DTask.bl_idname, text=_('Rewatch', '*'), icon_value=icons_loader.get_icon_id("eye"))
        row.operator(Tripogen_OT_RedownloadImg23DTask.bl_idname, text=_('Redownload', '*'), icon_value=icons_loader.get_icon_id("model"))
        row.operator(Tripogen_OT_ImportModelOfImg23DTask.bl_idname, text=_('Import', '*'), icon_value=icons_loader.get_icon_id("download"))
        
        