from bpy.app.translations import pgettext as _
import asyncio
import bpy
import threading
from ..icons import IconsLoader
from .general import AsyncOperatorMixin
from ..generators.tripo_generator import TripoGenerator
import os
from ..utils import ADDON_NAME

class Tripo_OT_CHECK_PYTHON_DEPENDENCIES(bpy.types.Operator):
    bl_idname = "blenderai_zealo.tripo_check_python_dependencies"
    bl_label = _("Check Tripo Generator Python Dependencies", '*')

    def execute(self, context):
        tripo_generator = TripoGenerator.instance()
        python_dependencies_installed = tripo_generator.check_python_dependencies()
        gen_props = context.scene.gen_props
        if python_dependencies_installed:
            gen_props.tripo_python_dependencies_installed = True
            gen_props.tripo_python_dependencies_install_status = "not_yet"
            gen_props.tripo_python_dependencies_install_message = ""
        else:
            gen_props.tripo_python_dependencies_installed = False
            gen_props.tripo_python_dependencies_install_status = "not_yet"
            gen_props.tripo_python_dependencies_install_message = ""
        return {"FINISHED"}
    
class Tripo_OT_INSTALL_PYTHON_DEPENDENCIES(AsyncOperatorMixin, bpy.types.Operator):
    bl_idname = "blenderai_zealo.tripo_install_python_dependencies"
    bl_label = _("Install Tripo Generator Python Dependencies", '*')
    

    def execute(self, context):
        gen_props = context.scene.gen_props
        if gen_props.trellis_python_dependencies_install_status == "installing":
            self.report({"ERROR"}, _("Trellis is installing python dependencies currently. Please wait for it and then install for tripo.", '*'))
            return {"CANCELLED"}
        tripo_generator = TripoGenerator.instance()
        python_dependencies_installed = tripo_generator.check_python_dependencies()
        if python_dependencies_installed:
            gen_props.tripo_python_dependencies_install_status = "not_yet"
            gen_props.tripo_python_dependencies_install_message = ""
            gen_props.tripo_python_dependencies_installed = True
            return {"FINISHED"}
        else:
            self.end_token = False
            def tripo_install_python_dependencies_thread():
                tripo_generator.install_python_dependencies(self, gen_props)
            self.async_thread = threading.Thread(target=tripo_install_python_dependencies_thread)
            self.async_thread.start()
            self.timer = context.window_manager.event_timer_add(time_step=1, window=context.window)
            context.window_manager.modal_handler_add(self)
            self.track_self()
            return {'RUNNING_MODAL'}
    
    
class Tripo_OT_CHECK_READY(AsyncOperatorMixin, bpy.types.Operator):
    bl_idname = "blenderai_zealo.tripo_check_ready"
    bl_label = _("Check Wether Tripo Generator is Ready", '*')

    def execute(self, context):
        tripo_generator = TripoGenerator.instance()
        python_dependencies_installed = tripo_generator.check_python_dependencies()
        gen_props = context.scene.gen_props
        if python_dependencies_installed:
            prefs = context.preferences.addons[ADDON_NAME].preferences
            api_key = prefs.tripo_api_key
            self.end_token = False
            def tripo_check_ready_thread():
                tripo_generator.check_ready(self, api_key, gen_props)
            self.async_thread = threading.Thread(target=tripo_check_ready_thread)
            self.async_thread.start()
            self.timer = context.window_manager.event_timer_add(time_step=1, window=context.window)
            context.window_manager.modal_handler_add(self)
            self.track_self()
            return {'RUNNING_MODAL'}
        else:
            gen_props.tripo_ready = False
            gen_props.tripo_check_ready_status = "not_yet"
            gen_props.tripo_check_ready_message = ""
            return {"FINISHED"}
    


class Tripogen_OT_TogglePanel(bpy.types.Operator):
    bl_idname = "blenderai_zealo.tripogen_togglepanel"
    bl_label = _("Toggle Tripo Generator Panel", '*')
    
    def execute(self, context):
        gen_props = context.scene.gen_props
        gen_props.show_tripo = not gen_props.show_tripo
        return {"FINISHED"}
            

class Tripogen_OT_AddTxt23DTask(
    AsyncOperatorMixin, 
    bpy.types.Operator
):
    bl_idname = "blenderai_zealo.tripogen_add_text_to_3d_task"
    bl_label = _("Add Text to 3D Task", '*')

    task_name: bpy.props.StringProperty(
        name=_("Task Name", '*')
    )
    prompt: bpy.props.StringProperty(
        name=_("Prompt", '*')
    )
    model_version: bpy.props.EnumProperty(
        name=_("Model Version", '*'), 
        items=[
            ("v2.0-20240919", _("v2.0", '*'), ""), 
            ("v1.4-20240625", _("v1.4", '*'), ""), 
            ("v1.3-20240522", _("v1.3", '*'), "")
        ], 
    )
    output_type: bpy.props.EnumProperty(
        name=_("Output Type", '*'), 
        items=[
            ("model", _("Model", '*'), ""), 
            ("base_model", _("Base Model", '*'), ""), 
            ("pbr_model", _("PBR Model", '*'), "")
        ], 
        default="pbr_model"
    )

    def invoke(self, context, event=None):
        task_length = len(context.scene.tripogen_props.txt23d_tasks)
        self.task_name = _("Task", '*') + f"{task_length}"
        self.prompt = ""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "task_name")
        layout.prop(self, "prompt")
        layout.prop(self, "model_version")
        layout.prop(self, "output_type")

    def execute(self, context):
        prefs = context.preferences.addons[ADDON_NAME].preferences
        api_key = prefs.tripo_api_key
        self.end_token = False
        tripo_generator = TripoGenerator.instance()
        tripogen_props = context.scene.tripogen_props
        tasks = tripogen_props.txt23d_tasks
        task = tasks.add()
        tripogen_props.txt23d_task_active_index = len(tasks) - 1
        task.name = self.task_name
        task.model_version = self.model_version
        task.prompt = self.prompt
        task.output.type = self.output_type
        task.create_status = "creating"
        self.task = task

        def run_in_thread():
            tripo_generator.text23d(task, api_key, self)
        self.async_thread = threading.Thread(target=run_in_thread)
        self.async_thread.start()
        self.timer = context.window_manager.event_timer_add(time_step=1, window=context.window)
        context.window_manager.modal_handler_add(self)
        self.track_self()
        return {'RUNNING_MODAL'}

class Tripogen_OT_RemoveFailedTxt23DTask(bpy.types.Operator):

    bl_idname = "blenderai_zealo.tripogen_remove_failed_text_to_3d_task"
    bl_label = _("Remove Failed Text to 3D Task", '*')


    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    

    def execute(self, context):
        tripogen_props = context.scene.tripogen_props
        active_index = tripogen_props.txt23d_task_active_index 
        task = tripogen_props.txt23d_tasks[active_index]
        if task.create_status != "creating_failed":
            self.report({"ERROR"}, _("You can only remove a creating failed task", '*'))
            return {"FINISHED"}
        else:
            tripogen_props.txt23d_tasks.remove(active_index)
            return {"FINISHED"}

class Tripogen_OT_RewatchTxt23DTask(AsyncOperatorMixin, bpy.types.Operator):

    bl_idname = "blenderai_zealo.tripogen_rewatch_text_to_3d_task"
    bl_label = _("Rewatch Text to 3D Task", '*')

    def execute(self, context):
        prefs = context.preferences.addons[ADDON_NAME].preferences
        api_key = prefs.tripo_api_key
        tripo_generator = TripoGenerator.instance()
        tripogen_props = context.scene.tripogen_props
        active_index = tripogen_props.txt23d_task_active_index 
        task = tripogen_props.txt23d_tasks[active_index]
        if task.watch_status != "watching_failed":
            self.report({"ERROR"}, _("You can only rewatch a task with status watch_failed", '*'))
            return {"FINISHED"}
        else:
            self.end_token = False
            def run_in_thread():
                tripo_generator.rewatch_txt23d_task(task, api_key, self)
            self.async_thread = threading.Thread(target=run_in_thread)
            self.async_thread.start()
            self.task = task
            self.timer = context.window_manager.event_timer_add(time_step=1.0, window=context.window)
            context.window_manager.modal_handler_add(self)
            self.track_self()
            return {"RUNNING_MODAL"}


class Tripogen_OT_RedownloadOfTxt23DTask(AsyncOperatorMixin, bpy.types.Operator):

    bl_idname = "blenderai_zealo.tripogen_redownload_text_to_3d_task"
    bl_label = _("Redownload Text to 3D Task", '*')


    def execute(self, context):
        prefs = context.preferences.addons[ADDON_NAME].preferences
        api_key = prefs.tripo_api_key
        tripo_generator = TripoGenerator.instance()
        tripogen_props = context.scene.tripogen_props
        active_index = tripogen_props.txt23d_task_active_index 
        task = tripogen_props.txt23d_tasks[active_index]
        self.task = task

        if getattr(task.output, f"{task.output.type}_download_status") != "downloading_failed":
            self.report({"ERROR"}, _("You can only re-download model with status downloading_failed.", '*'))
            return {"FINISHED"}
        else:
            self.end_token = False
            def run_in_thread():
                tripo_generator.redownload_txt23d_task(task, api_key, self)
            self.async_thread = threading.Thread(target=run_in_thread)
            self.async_thread.start()
            self.timer = context.window_manager.event_timer_add(time_step=1.0, window=context.window)
            context.window_manager.modal_handler_add(self)
            self.track_self()
            return {'RUNNING_MODAL'}

    
class Tripogen_OT_ImportModelOfTxt23DTask(bpy.types.Operator):

    bl_idname = "blenderai_zealo.tripogen_import_model_of_text_to_3d_task"
    bl_label = _("Import Model Of Success Txt To 3D Task", '*')

    def execute(self, context):
        tripogen_props = context.scene.tripogen_props
        active_index = tripogen_props.txt23d_task_active_index 
        task = tripogen_props.txt23d_tasks[active_index]
        if getattr(task.output, f"{task.output.type}_download_status") != "downloading_end":
            self.report({"ERROR"}, _("The model hasn't been downloaded yet!", '*'))
            return {"CANCELLED"}
        else:
            local_filepath = getattr(task.output, f"{task.output.type}_local_filepath")
            try:
                bpy.ops.import_scene.gltf(filepath=local_filepath)
            except Exception as e:
                self.report({"ERROR"}, "Try to import glb file from: " + local_filepath + "But get an error: " + str(e) )
                return {"CANCELLED"}
            selected_objects = context.selected_objects
            if not selected_objects:
                self.report({'WARNING'}, _("No objects were imported.", '*'))
                return {'CANCELLED'}
            imported_object = selected_objects[0]
            cursor_position = context.scene.cursor.location
            imported_object.location = cursor_position
            imported_object.name = task.name
            self.report({'INFO'}, _("Imported object: ", '*') + imported_object.name)
            return {'FINISHED'}


class Tripogen_OT_AddImg23DTask(AsyncOperatorMixin, bpy.types.Operator):
    bl_idname = "blenderai_zealo.tripogen_add_image_to_3d_task"
    bl_label = _("Add Image to 3D Task", '*')


    task_name: bpy.props.StringProperty(
        name=_("Task Name", '*'), 
    )

    image_path: bpy.props.StringProperty(
        name=_("Image Path", '*'), 
        subtype="FILE_PATH"
    )

    model_version: bpy.props.EnumProperty(
        name=_("Model Version", '*'), 
        items=[
            ("v2.0-20240919", _("v2.0", '*'), ""), 
            ("v1.4-20240625", _("v1.4", '*'), ""), 
            ("v1.3-20240522", _("v1.3", '*'), "")
        ], 
    )

    output_type: bpy.props.EnumProperty(
        name=_("Output Type", '*'), 
        items=[
            ("model", _("Model", '*'), ""), 
            ("base_model", _("Base Model", '*'), ""), 
            ("pbr_model", _("PBR Model", '*'), "")
        ], 
        default="pbr_model"
    )



    def invoke(self, context, event):
        task_length = len(context.scene.tripogen_props.img23d_tasks)
        self.task_name = _("Task", '*') + f"{task_length}"
        self.image_path = ""
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        icons_loader = IconsLoader.instance()
        layout = self.layout
        layout.prop(self, "task_name")
        layout.label(text=_("Only png and jpeg format.", '*'), icon_value=icons_loader.get_icon_id("image"))
        layout.prop(self, "image_path")
        layout.prop(self, "model_version")
        layout.prop(self, "output_type")
        

    def _check_file_type(self, file_path):
        basename = os.path.basename(file_path)
        extension = basename.split(".")[-1]
        if extension in ["png", "jpeg"]:
            return (True, extension)
        else:
            return (False, extension)

    def execute(self, context):
        file_type_valid, type = self._check_file_type(self.image_path)
        if not file_type_valid:
            self.report({"ERROR"},  _("Now we can only support png and jepg image format. ", '*'))
            return {"FINISHED"}

        prefs = context.preferences.addons[ADDON_NAME].preferences
        api_key = prefs.tripo_api_key
        self.end_token = False
        tripo_generator = TripoGenerator.instance()
        tripogen_props = context.scene.tripogen_props
        tasks = tripogen_props.img23d_tasks
        task = tasks.add()
        tripogen_props.img23d_task_active_index = len(tasks) - 1
        task.name = self.task_name
        task.image.local_filepath = self.image_path
        task.image.type = type
        task.output.type = self.output_type
        self.task = task

        def run_in_thread():
            tripo_generator.image23d(task, api_key, self)
        self.async_thread = threading.Thread(target=run_in_thread)
        self.async_thread.start()
        self.timer = context.window_manager.event_timer_add(time_step=1.0, window=context.window)
        context.window_manager.modal_handler_add(self)
        self.track_self()
        return {'RUNNING_MODAL'}
    
    
class Tripogen_OT_RemoveFailedImg23DTask(bpy.types.Operator):

    bl_idname = "blenderai_zealo.tripogen_remove_failed_image_to_3d_task"
    bl_label = _("Remove Failed Image to 3D Task", '*')

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        tripogen_props = context.scene.tripogen_props
        active_index = tripogen_props.img23d_task_active_index 
        task = tripogen_props.img23d_tasks[active_index]
        if (task.image.upload_status != "uploading_failed" or 
            (task.image.upload_status == "uploading_end" and task.create_status != "creating_failed")
            ):
            self.report({"ERROR"}, _("You can only remove a uploading failed task or creating failed task", '*'))
            return {"FINISHED"}
        else:
            tripogen_props.img23d_tasks.remove(active_index)
            return {"FINISHED"}


class Tripogen_OT_RewatchImg23DTask(AsyncOperatorMixin, bpy.types.Operator):

    bl_idname = "blenderai_zealo.tripogen_rewatch_image_to_3d_task"
    bl_label = _("Rewatch Image to 3D Task", '*')

    def execute(self, context):
        prefs = context.preferences.addons[ADDON_NAME].preferences
        api_key = prefs.tripo_api_key
        tripo_generator = TripoGenerator.instance()
        tripogen_props = context.scene.tripogen_props
        active_index = tripogen_props.img23d_task_active_index 
        task = tripogen_props.img23d_tasks[active_index]
        if task.watch_status != "watching_failed":
            self.report({"ERROR"}, _("You can only re-watch a task with status watch_failed", '*'))
            return {"FINISHED"}
        else:
            self.end_token = False
            def run_in_thread():
                tripo_generator.rewatch_img23d_task(task, api_key, self)
            self.async_thread = threading.Thread(target=run_in_thread)
            self.async_thread.start()
            self.task = task
            self.timer = context.window_manager.event_timer_add(time_step=1.0, window=context.window)
            context.window_manager.modal_handler_add(self)
            self.track_self()
            return {"RUNNING_MODAL"}
    
    
class Tripogen_OT_RedownloadImg23DTask(AsyncOperatorMixin, bpy.types.Operator):

    bl_idname = "blenderai_zealo.tripogen_redownload_image_to_3d_task"
    bl_label = _("Redownload Image to 3D Task", '*')


    def execute(self, context):
        prefs = context.preferences.addons[ADDON_NAME].preferences
        api_key = prefs.tripo_api_key
        tripo_generator = TripoGenerator.instance()
        tripogen_props = context.scene.tripogen_props
        active_index = tripogen_props.img23d_task_active_index 
        task = tripogen_props.img23d_tasks[active_index]
        self.task = task

        if getattr(task.output, f"{task.output.type}_download_status") != "downloading_failed":
            self.report({"ERROR"}, _("You can only re-download model with status downloading_failed", '*'))
            return {"FINISHED"}
        else:
            self.end_token = False
            def run_in_thread():
                tripo_generator.redownload_img23d_task(task, api_key, self)
            self.async_thread = threading.Thread(target=run_in_thread)
            self.async_thread.start()
            self.timer = context.window_manager.event_timer_add(time_step=1.0, window=context.window)
            context.window_manager.modal_handler_add(self)
            self.track_self()
            return {'RUNNING_MODAL'}


class Tripogen_OT_ImportModelOfImg23DTask(bpy.types.Operator):

    bl_idname = "blenderai_zealo.tripogen_import_model_of_image_to_3d_task"
    bl_label = _("Import Model Of Success Image to 3D Task", '*')

    def execute(self, context):
        tripogen_props = context.scene.tripogen_props
        active_index = tripogen_props.img23d_task_active_index 
        task = tripogen_props.img23d_tasks[active_index]
        if getattr(task.output, f"{task.output.type}_download_status") != "downloading_end":
            self.report({"ERROR"}, _("The model hasn't been downloaded yet!", '*'))
            return {"CANCELLED"}
        else:
            local_filepath = getattr(task.output, f"{task.output.type}_local_filepath")
            try:
                bpy.ops.import_scene.gltf(filepath=local_filepath)
            except Exception as e:
                self.report({"ERROR"}, "Try to import glb file from: " + local_filepath + "But get an error: " + str(e))
                return {"CANCELLED"}
            selected_objects = context.selected_objects
            if not selected_objects:
                self.report({'WARNING'}, _("No objects were imported.", '*'))
                return {'CANCELLED'}
            imported_object = selected_objects[0]
            cursor_position = context.scene.cursor.location
            imported_object.location = cursor_position
            imported_object.name = task.name
            self.report({'INFO'}, _("Imported object: ", '*') + imported_object.name)
            return {'FINISHED'}