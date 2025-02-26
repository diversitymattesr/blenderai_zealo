from bpy.app.translations import pgettext as _
import bpy
from ..operators import *


class Generator_PT_Panel(bpy.types.Panel):
    bl_idname = "BLENDER_ZEALO_GENERATOR_PT_Panel"
    bl_label = _('AI Generator Status', '*')
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = _("AI Generator", "*")

    @classmethod
    def poll(cls, context):
        return True
    
    def draw(self, context):
        layout = self.layout
        icons_loader = IconsLoader.instance()
        gen_props = context.scene.gen_props
        language = context.preferences.view.language.split("_")[0]
        if gen_props.windows_long_path_support:
            tripo_box = layout.box()
            tripo_box.label(text=_('Tripo Generator', '*'), icon_value=icons_loader.get_icon_id("model"))
            col = tripo_box.column(align=True)
            if gen_props.tripo_python_dependencies_installed:
                if gen_props.tripo_ready:
                    if gen_props.show_tripo:
                        col.operator(Tripogen_OT_TogglePanel.bl_idname, text=_('Close Tripo Generator', '*'))
                    else:
                        col.operator(Tripogen_OT_TogglePanel.bl_idname, text=_('Open Tripo Generator', '*'))
                else:
                    col.label(text=_('The tripo api key is not correct', '*'), icon_value=icons_loader.get_icon_id("warning"))
                    col.label(text=_('Please go to addon preferences to modify it.', '*'))
                    col.operator(Tripo_OT_CHECK_READY.bl_idname, text=_('Check API Key', '*'))
                    if gen_props.tripo_check_ready_status in ["checking_failed", "checking"]:
                        col.label(text=f"{gen_props.tripo_check_ready_message}", icon_value=icons_loader.get_icon_id("warning"))
            else:
                if gen_props.tripo_python_dependencies_install_status == "installing":
                    col.label(text=_('Installing Progress', '*'), icon_value=icons_loader.get_icon_id("progress"))
                    col.label(text=f"{gen_props.tripo_python_dependencies_install_message}")
                else:
                    col.operator(Tripo_OT_INSTALL_PYTHON_DEPENDENCIES.bl_idname, text=_('Install Python Dependencies', '*'))
                    if gen_props.tripo_python_dependencies_install_status == "installing_failed":
                        col.label(text=f"{gen_props.tripo_python_dependencies_install_message}", icon_value=icons_loader.get_icon_id("warning"))

            layout.separator(type="LINE")
            trellis_box = layout.box()
            trellis_box.label(text=_('Trellis Generator', '*'), icon_value=icons_loader.get_icon_id("model"))
            col = trellis_box.column()
            if gen_props.trellis_manifest_nvidia_driver:
                if gen_props.trellis_python_dependencies_installed:
                    if gen_props.trellis_ready:
                        if gen_props.show_trellis:
                            col.operator(Trellis_OT_TogglePanel.bl_idname, text=_('Close Trellis Generator', '*'))
                        else:
                            col.operator(Trellis_OT_TogglePanel.bl_idname, text=_('Open Trellis Generator', '*'))
                        col.operator(Trellis_OT_Manually_Close_Trellis_Process.bl_idname, text=_("Manually close Trellis process", '*'))
                    else:
                        if gen_props.trellis_make_ready_status == "making_ready":
                            col.label(text=_('Making Ready Progress', '*'), icon_value=icons_loader.get_icon_id("progress"))
                            col.label(text=f"{gen_props.trellis_make_ready_message}")
                        else:
                            col.operator(Trellis_OT_MakeReady.bl_idname, text=_('Get Trellis Generator Ready', '*'))
                            if gen_props.trellis_make_ready_status == "making_ready_failed":
                                col.label(text=f"{gen_props.trellis_make_ready_message}", icon_value=icons_loader.get_icon_id("warning"))
                else:
                    if gen_props.trellis_python_dependencies_install_status == "installing":
                        col.label(text=_('Installing Progress', '*'), icon_value=icons_loader.get_icon_id("progress"))
                        col.label(text=f"{gen_props.trellis_python_dependencies_install_message}")
                    else:
                        col.operator(Trellis_OT_INSTALL_PYTHON_DEPENDENCIES.bl_idname, text=_('Install Python Dependencies', '*'))
                        if gen_props.trellis_python_dependencies_install_status == "installing_failed":
                            col.label(text=f"{gen_props.trellis_python_dependencies_install_message}", icon_value=icons_loader.get_icon_id("warning"))
            else:
                col.label(text=_("The version of your Nvidia driver should be at least 527.41. Please update your driver.", '*'), icon_value=icons_loader.get_icon_id("warning"))
                col.operator(Trellis_OT_CHECK_MANIFEST_NVIDIA_DRIVER.bl_idname, text=_("Check Nvidia Driver", '*'), icon_value=icons_loader.get_icon_id("nvidia"))
                box_method_a = col.box()
                box_method_a.label(text=_("Method A (If you have Geforce Experience installed in your computer)", '*'))
                col_box_method_a = box_method_a.column(align=True)
                col_box_method_a.label(text=_("Step1: Open Geforce Experience", '*'))
                col_box_method_a.label(text=_("Step2: Click Driver tab on top", '*'))
                col_box_method_a.label(text=_("Step3: In available driver section, click download to get latest driver", '*'))

                box_method_b = col.box()
                box_method_b.label(text=_("Method B (If you don't have Geforce Experience installed in your computer)", '*'))
                col_box_method_b = box_method_b.column(align=True)
                row = col_box_method_b.row(align=True)
                row.alignment = "LEFT"
                row.label(text=_("Step1: ", '*'))
                driver_open_url = f"https://nvidia.{'cn' if language == 'zh' else 'com'}/drivers"
                row.operator("wm.url_open", text=_("Get Programme to Update Nvidia Driver", '*'), icon_value=icons_loader.get_icon_id("link")).url = driver_open_url
                col_box_method_b.label(text=_("Step2: In Manual Driver Search Area, Select Appropriate Type of Your Driver", '*'))
                col_box_method_b.label(text=_("Step3: In the Results, Choose any one between Studio Driver and Game Ready Driver", '*'))
                col_box_method_b.label(text=_("Step4: After Downloaded, Follow Guided to Update Your Driver", '*'))
        else:
            layout.operator(Generator_OT_CHECK_WINDOWS_LONG_PATH_SUPPORT.bl_idname, text=_("Check if windows support long path", '*'), icon="FILE")
            layout.label(text=_("Your windows does not support long path.", '*'), icon_value=icons_loader.get_icon_id("warning"))
            layout.label(text=_("Try to configure your windows using following methods", '*'))
            box_method_a = layout.box()
            box_method_a.label(text=_("Method A: Manually", '*'))
            col = box_method_a.column()
            col.label(text=_("Step1: Open Start Menu -> Search Registry Editor -> Open it in administration mode", '*'))
            col.label(text=(_("Step2: Navigate to: ", '*') + "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\FileSystem"))
            col.label(text=_("Step3: Find Key: LongPathsEnabled and set the value of it to 1", '*'))
            col.label(text=_("Step4: Click the button above to check if windows now support long path", '*'))

            box_method_b = layout.box()
            box_method_b.label(text=_("Method B: Automatically", '*'))
            col = box_method_b.column()
            row = col.row(align=True)
            row.alignment = "LEFT"
            row.label(text=_("Step1: ", '*'))
            row.operator(Generator_OT_SELECT_FOLDER_TO_CONTAIN_FILE.bl_idname, text=_("Select a folder to contain the automatic script", '*'))
            script_filename = "配置windows支持长路径.bat" if language == "zh" else "configure_windows_support_long_path.bat"
            col.label(text=(_("Step2: Run the script in administration mode named ", '*') + script_filename))
            col.label(text=_("Step3: Click the button above to check if windows now support long path", '*'))
        layout.separator(type="LINE")
        box = layout.box()
        col = box.column()
        col.label(text=_("The blender extension is in public test phrase.", '*'), icon_value=icons_loader.get_icon_id("notification"))
        col.label(text=_("If you encounter some issue, open blender console to check or bring the error to admin.", '*'))
        col.operator("wm.console_toggle", text=_("Toggle blender console", '*'), icon="CONSOLE")
        layout.separator(type="LINE")
        box = layout.box()
        col = box.column()
        col.label(text=_("The blender addon is in hot update phrase.", '*'), icon_value=icons_loader.get_icon_id("notification"))
        col.operator(BlenderAI_Zealo_OT_TOGGLE_UPDATE_PANEL.bl_idname, text=_("Show Update Panel", '*'))