from bpy.app.translations import pgettext as _
import os
import bpy
from ...icons import IconsLoader

class Trellisgen_UL_Image23D_Tasks(bpy.types.UIList):

    bl_idname = "BLENDER_ZEALO_TRELLISGEN_UL_IMAGE23D_TASKS"


    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icons_loader = IconsLoader.instance()
        task = item
        row = layout.row()
        if index == 0:
            row.label(text=_("Name", '*'), icon_value=icons_loader.get_icon_id("task"))
            row.label(text=_("Image", '*'), icon_value=icons_loader.get_icon_id("image"))
            row.label(text=_("Output", '*'), icon_value=icons_loader.get_icon_id("model"))
            row.label(text=_("Create", '*'), icon_value=icons_loader.get_icon_id("plus"))
            row.label(text=_("Watch", 'taskHeader'), icon_value=icons_loader.get_icon_id("eye"))
            row.label(text=_("Download", '*'), icon_value=icons_loader.get_icon_id("download"))
        else:
            row.label(text=f"{task.name}")
            image_base_name = os.path.basename(task.image.local_filepath)
            image_upload_status_info = (
                (_("Not Yet", '*'), "ellipsis")if task.image.upload_status == "not_yet" else
                (_("Uploading", '*'), "progress")if task.image.upload_status == "uploading" else
                (image_base_name, "check_mark") if task.image.upload_status == "uploading_end" else
                (_("Failed", '*'), "cross_mark")
            )
            row.label(text=image_upload_status_info[0], icon_value=icons_loader.get_icon_id(image_upload_status_info[1]))
            output_type_info = (
                (_("Model", '*'), "shine_model") if task.output.type == "model" else
                (_("Base Model", '*'), "shine_base_model")
            )
            row.label(text=output_type_info[0], icon_value=icons_loader.get_icon_id(output_type_info[1]))
            create_status_info = (
                (_("Not Yet", '*'), "ellipsis") if task.create_status == "not_yet" else
                (_("Creating", '*'), "progress")if task.create_status == "creating" else
                (_("Created", '*'), "check_mark") if task.create_status == "creating_end" else
                (_("Failed", '*'), "cross_mark")
            )
            row.label(text=create_status_info[0], icon_value=icons_loader.get_icon_id(create_status_info[1]))
            watch_status_info = (
                (_("Not Yet", '*'), "ellipsis") if task.watch_status == "not_yet" else
                (task.watch_progress, "progress") if task.watch_status == "watching" else
                (_("Success", '*'), "check_mark") if task.watch_status == "watching_end" else
                (_("Failed", '*'), "cross_mark") 
            )
            row.label(text=watch_status_info[0], icon_value=icons_loader.get_icon_id(watch_status_info[1]))
            model_download_info = (
                (_("Not Yet", '*'), "ellipsis") if task.output.download_status == "not_yet" else
                (task.output.download_progress, "progress") if task.output.download_status == "downloading" else
                (_("Success", '*'), "check_mark") if task.output.download_status == "downloading_end" else
                (_("Failed", '*'), "cross_mark") 
            )
            row.label(text=model_download_info[0], icon_value=icons_loader.get_icon_id(model_download_info[1]))
        
