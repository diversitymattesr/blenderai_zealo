from bpy.app.translations import pgettext as _
import bpy
from ...updater import BlenderAIUpdater
from ...operators import *


class BlenderAI_Zealo_Updater_PT_Panel(bpy.types.Panel):
    bl_idname = "BLENDERAI_ZEALO_UPDATER_PT_Panel"
    bl_label = _('Updater for AI Generator', '*')
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = _("BlenderAI Updater", "*")

    @classmethod
    def poll(cls, context):
        updater_props = context.scene.updater_props
        if updater_props.show_update_panel:
            return True
        else:
            return False
        
    def draw(self, context):
        icons_loader = IconsLoader.instance()
        updater = BlenderAIUpdater.instance()
        updater_props = context.scene.updater_props
        layout = self.layout
        layout.label(text=_("Update Panel", '*'))
        box = layout.box()
        box.label(text=_("Choose where to get the release", '*'), icon_value=icons_loader.get_icon_id("cloud"))
        box.label(text=_("If you are in China mainland, choose Gitee.", '*'), icon_value=icons_loader.get_icon_id("warning"))
        row = box.row(align=True)
        row.alignment = "LEFT"
        row.label(text=_("Release Source", '*'))
        row.prop(updater_props, "engine",)
        box = layout.box()
        box.label(text=_("Check Update", '*'))
        box.label(text=_("Current version: ", '*') + f"v{'.'.join([str(comp) for comp in updater.CURRENT_VERSION])}")
        box.operator(BlenderAI_Zealo_OT_CHECK_UPDATE.bl_idname, text=_("Check Update", '*'), icon_value=icons_loader.get_icon_id("eye"))
        if updater_props.check_update_message:
            box.label(text=updater_props.check_update_message)
        box.operator(
            BlenderAI_Zealo_OT_Download_Release.bl_idname, 
            text=_("Download Release: ", '*') + f"v{updater_props.update_to_release_name}" if \
                updater_props.update_to_release_name else \
                _("Download Release", '*'), 
            icon_value=icons_loader.get_icon_id("download")
        )
        if updater_props.download_release_message:
            box.label(text=updater_props.download_release_message)
        box.operator(
            BlenderAI_Zealo_OT_Update_To_Release.bl_idname, 
            text=_("Update to Latest Release: ", '*') + updater_props.downloaded_release_name if \
            updater_props.downloaded_release_name else \
            _("Update to Latest Release", '*')
        )