import shutil
import subprocess
from bpy.app.translations import pgettext as _
import bpy
import os
from ..utils import absolute_path 

class AsyncOperatorMixin:

    OPERATOR_IN_MODAL = set()

    def track_self(self):
        self.OPERATOR_IN_MODAL.add(self)

    def untrack_self(self):
        if self in self.OPERATOR_IN_MODAL:
            self.OPERATOR_IN_MODAL.remove(self)
    
    def modal(self, context, event):
        if event.type == "TIMER":
            if (getattr(self, "end_token", None) is None) or (getattr(self, "async_thread", None) is None):
                raise Exception("If you want to use the async operator, you have to set the attribute end_token and async_thread on operator instance")
            if self.end_token:
                self.async_thread.join()
                context.window_manager.event_timer_remove(self.timer)
                self.untrack_self()
                return {"FINISHED"}
        return {"PASS_THROUGH"}
    
class SubprocessOperatorMixin(AsyncOperatorMixin):

    subprocess_name = ""

    def terminate_subprocess(self):
        if getattr(self, "subprocess", None) is None:
            print("No subprocess is assigned in this operator yet.")
            return False
        if self.subprocess_name:
            print(f"{self.__class__.__name__} operator is still running a subprocess called {self.subprocess_name}")
        else:
            print(f"{self.__class__.__name__} operator is still running a subprocess")
        print(f"Trying to terminate this subprocess...")
        self.subprocess.terminate()
        self.subprocess.wait()
        return True

        

class Generator_OT_CHECK_WINDOWS_LONG_PATH_SUPPORT(bpy.types.Operator):
    bl_idname = "blenderai_zealo.check_windows_long_path_support"
    bl_label = _("Check Windows Long Path Support", '*') 

    def execute(self, context):
        gen_props = context.scene.gen_props
        long_path_folder = absolute_path(f"{'a' * 255}")
        try:
            subprocess.run(
                f'mkdir "{long_path_folder}"', 
                shell=True,
                check=True
            )
            gen_props.windows_long_path_support = True

            subprocess.run(
                f'rmdir "{long_path_folder}"', 
                shell=True,
                check=True
            )
        except Exception as e:
            print(f"The windows system does not support long file path.")
            gen_props.windows_long_path_support = False
        finally:
            return {"FINISHED"}

class Generator_OT_SELECT_FOLDER_TO_CONTAIN_FILE(bpy.types.Operator):
    bl_idname = "blenderai_zealo.select_folder_to_contain_file"
    bl_label = _("Select Folder to Contain File", '*')

    folder_path: bpy.props.StringProperty(
        name=_("Folder", '*'), 
        subtype="DIR_PATH"
    )

    def invoke(self, context, event):
        desktop_path = os.path.normpath(os.path.join(os.path.expanduser("~"), "desktop"))
        if os.path.exists(desktop_path):
            self.folder_path = desktop_path
        else:
            self.folder_path = ""
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text=_("Select a folder to contain the script", '*'))
        if self.folder_path:
            layout.label(text=(_("Default to: ", '*') + self.folder_path))
        layout.prop(self, "folder_path")


    def execute(self, context):
        language = context.preferences.view.language.split("_")[0]
        configuration_filename = "配置windows支持长路径.bat" if language == "zh" else "configure_windows_support_long_path.bat"
        configuration_filepath = absolute_path(f"scripts/{configuration_filename}")
        try:
            shutil.copy(configuration_filepath, self.folder_path)
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, _("Copy file: ", '*') + configuration_filepath + _(" to: ", '*') + str(self.folder_path) + _(" failed since error: ", '*') + str(e))
            return {"CANCELLED"}
        
