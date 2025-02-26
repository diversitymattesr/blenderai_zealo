import threading
from bpy.app.translations import pgettext as _
import bpy
from ..updater import BlenderAIUpdater
from ..operators import AsyncOperatorMixin, SubprocessOperatorMixin
from ..icons import IconsLoader

class BlenderAI_Zealo_OT_TOGGLE_UPDATE_PANEL(bpy.types.Operator):
    bl_idname = "blenderai_zealo.toggle_update_panel"
    bl_label = _("Toggle update panel", '*') 

    def execute(self, context):
        updater_props = context.scene.updater_props
        updater_props.show_update_panel = not updater_props.show_update_panel
        return {"FINISHED"}
    
class BlenderAI_Zealo_OT_CHECK_UPDATE(AsyncOperatorMixin, bpy.types.Operator):
    bl_idname = "blenderai_zealo.check_update"
    bl_label = _("Check update", '*') 

    @classmethod
    def poll(cls, context):
        updater_props = context.scene.updater_props
        if updater_props.check_update_status == "checking" or \
            updater_props.download_release_status == "downloading":
            return False
        else:
            return True


    def execute(self, context):
        updater = BlenderAIUpdater.instance()
        updater_props = context.scene.updater_props
        def check_update_thread():
            updater.check_update(self, f"{updater_props.engine}", updater_props)
        self.async_thread = threading.Thread(target=check_update_thread, daemon=True)
        self.async_thread.start()
        self.end_token = False
        self.timer = context.window_manager.event_timer_add(time_step=1, window=context.window)
        context.window_manager.modal_handler_add(self)
        self.track_self()
        return {"RUNNING_MODAL"}
    

class BlenderAI_Zealo_OT_Download_Release(SubprocessOperatorMixin, bpy.types.Operator):
    bl_idname = "blenderai_zealo.download_release"
    bl_label = _("Download Release", '*')

    @classmethod
    def poll(cls, context):
        updater_props = context.scene.updater_props
        if updater_props.check_update_status == "checking" or \
            updater_props.download_release_status == "downloading" or \
            not updater_props.update_to_release_name:
            return False
        else:
            return True
        
    def execute(self, context):
        updater = BlenderAIUpdater.instance()
        updater_props = context.scene.updater_props
        update_to_release_name = f"{updater_props.update_to_release_name}"
        def download_release_thread():
            updater.download_release(self, updater_props.engine, update_to_release_name, updater_props)
        self.async_thread = threading.Thread(target=download_release_thread, daemon=True)
        self.async_thread.start()
        self.end_token = False
        self.timer = context.window_manager.event_timer_add(time_step=1, window=context.window)
        context.window_manager.modal_handler_add(self)
        self.track_self()
        return {"RUNNING_MODAL"}
    
class BlenderAI_Zealo_OT_Update_To_Release(bpy.types.Operator):
    bl_idname = "blenderai_zealo.update_to_release"
    bl_label = _("Update To Release", '*')

    @classmethod
    def poll(cls, context):
        updater_props = context.scene.updater_props
        if updater_props.download_release_status == "downloading_end" and \
            updater_props.downloaded_release_name:
            return True
        else:
            return False
        
    def execute(self, context):
        return {"FINISHED"}
        
    




