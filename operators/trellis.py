from bpy.app.translations import pgettext as _
import os
import threading
import bpy
from .general import AsyncOperatorMixin, SubprocessOperatorMixin
from ..icons import IconsLoader
from ..generators.trellis_generator import TrellisGenerator
from ..utils import absolute_path, open_console


class Trellis_OT_CHECK_MANIFEST_NVIDIA_DRIVER(bpy.types.Operator):
    bl_idname = "blenderai_zealo.trellis_check_manifest_nvidia_driver"
    bl_label = _("Check Nvidia Driver Version if Manifest Min Version", '*') 

    def execute(self, context):
        trellis_generator = TrellisGenerator.instance()
        gen_props = context.scene.gen_props
        nvidia_driver_manifest = trellis_generator.check_nvidia_driver_manifest()
        if nvidia_driver_manifest:
            gen_props.trellis_manifest_nvidia_driver = True
        else:
            gen_props.trellis_manifest_nvidia_driver = False
        return {"FINISHED"}
    

class Trellis_OT_CHECK_PYTHON_DEPENDENCIES(bpy.types.Operator):
    bl_idname = "blenderai_zealo.trellis_check_python_dependencies"
    bl_label = _("Check Trellis Generator Python Dependencies", '*')

    def execute(self, context):
        trellis_generator = TrellisGenerator.instance()
        python_dependencies_installed = trellis_generator.check_python_dependencies()
        gen_props = context.scene.gen_props
        if python_dependencies_installed:
            gen_props.trellis_python_dependencies_installed = True
            gen_props.trellis_python_dependencies_install_status = "not_yet"
            gen_props.trellis_python_dependencies_install_message = ""
        else:
            gen_props.trellis_python_dependencies_installed = False
            gen_props.trellis_python_dependencies_install_status = "not_yet"
            gen_props.trellis_python_dependencies_install_message = ""
        return {"FINISHED"}

class Trellis_OT_INSTALL_PYTHON_DEPENDENCIES(AsyncOperatorMixin, bpy.types.Operator):
    bl_idname = "blenderai_zealo.trellis_install_python_dependencies"
    bl_label = _("Install Trellis Generator Python Dependencies", '*')
    

    def execute(self, context):
        gen_props = context.scene.gen_props
        if gen_props.tripo_python_dependencies_install_status == "installing":
            self.report({"ERROR"}, _("Tripo is installing python dependencies currently. Please wait for it and then install for trellis.", '*'))
            return {"CANCELLED"}
        trellis_generator = TrellisGenerator.instance()
        python_dependencies_installed = trellis_generator.check_python_dependencies()
        if python_dependencies_installed:
            gen_props.trellis_python_dependencies_installed = True
            gen_props.trellis_python_dependencies_install_status = "not_yet"
            gen_props.trellis_python_dependencies_install_message = ""
            return {"FINISHED"}
        else:
            self.end_token = False
            def run_in_thread():
                trellis_generator.install_python_dependencies(self, gen_props)
            self.async_thread = threading.Thread(target=run_in_thread)
            self.async_thread.start()
            self.timer = context.window_manager.event_timer_add(time_step=1, window=context.window)
            context.window_manager.modal_handler_add(self)
            self.track_self()
            return {'RUNNING_MODAL'}
    

class Trellis_OT_CHECK_READY(bpy.types.Operator):
    bl_idname = "blenderai_zealo.trellis_check_ready"
    bl_label = _("Check Wether Trellis Generator is Ready", '*')

    def execute(self, context):
        trellis_generator = TrellisGenerator.instance()
        python_dependencies_installed = trellis_generator.check_python_dependencies()
        gen_props = context.scene.gen_props
        if python_dependencies_installed:
            ready = trellis_generator.check_ready()
            if ready:
                gen_props.trellis_ready = True
                gen_props.trellis_make_ready_status = "not_yet"
                gen_props.trellis_make_ready_message = ""
            else:
                gen_props.trellis_ready = False
                gen_props.trellis_make_ready_status = "not_yet"
                gen_props.trellis_make_ready_message = ""
        else:
            gen_props.trellis_ready = False
            gen_props.trellis_make_ready_status = "not_yet"
            gen_props.trellis_make_ready_message = ""
        return {"FINISHED"}



class Trellis_OT_MakeReady(SubprocessOperatorMixin, bpy.types.Operator):
    bl_idname = "blenderai_zealo.trellis_make_ready"
    bl_label = _("Make Trellis Generator Ready", '*')
    subprocess_name = "Trellis Generator Subprocess"

    process_on_8000_on_none_self_process: bpy.props.BoolProperty(default=False)

    terminate_process_on_8000_on_non_self_process: bpy.props.BoolProperty(
        name=_("Terminate: ", '*'), 
        default=False
    )

    precision: bpy.props.EnumProperty(
        name=_("Precision", '*'), 
        items=[
            ("float16", _("float16", '*'), ""), 
            ("float32", _("float32", '*'), "")
        ], 
        default="float16"
    )

    device_mode: bpy.props.EnumProperty(
        name=_("Device Mode", '*'), 
        items=[
            ("dynamic", _("dynamic", '*'), ""), 
            ("cuda", _("cuda", '*'), ""), 
        ]
    )

    
    def invoke(self, context, event):
        self.terminate_process_on_8000_on_non_self_process = False
        trellis_generator = TrellisGenerator.instance()
        self.process_on_8000_on_none_self_process = trellis_generator.check_process_on_8000_is_on_none_self_process()
        return context.window_manager.invoke_props_dialog(
            self, 
            width=600, 
            title=_("Make Trellis Generator Ready", '*')
        )


    def draw(self, context):
        icons_loader = IconsLoader.instance()
        layout = self.layout
        if self.process_on_8000_on_none_self_process:
            layout.label(text=_("There is a process taking over port 8000 which not belongs to current process", '*'), icon_value=icons_loader.get_icon_id("warning"))
            layout.prop(self, "terminate_process_on_8000_on_non_self_process")
            layout.label(text=_("If you choose not to terminate, then you can not run trellis on current process.", '*'))
        layout.label(text=_("Default configuration of precision and device mode required least VRAM. Any changes would require more VRAM.", '*'))
        layout.prop(self, "precision")
        layout.prop(self, "device_mode")


    def execute(self, context):
        if self.process_on_8000_on_none_self_process and (not self.terminate_process_on_8000_on_non_self_process):
            return {"FINISHED"}
        else:
            self.end_token = False
            self.trellis_start_parameters = {
                "precision": f"{self.precision}", 
                "device_mode": f"{self.device_mode}", 
            }
            gen_props = context.scene.gen_props
            trellis_generator = TrellisGenerator.instance()
            def trellis_generator_make_ready_thread():
                trellis_generator.make_ready(self, gen_props)
            self.async_thread = threading.Thread(target=trellis_generator_make_ready_thread, daemon=True)
            self.async_thread.start()
            self.timer = context.window_manager.event_timer_add(time_step=5, window=context.window)
            context.window_manager.modal_handler_add(self)
            self.track_self()
            return {'RUNNING_MODAL'}
        
    
class Trellis_OT_Manually_Close_Trellis_Process(bpy.types.Operator):
    bl_idname = "blenderai_zealo.trellis_manually_close_trellis_process"
    bl_label = _("Manually Close Trellis Process", '*') 

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(
            self, event, 
            title=_("Manually close trellis process", '*'), 
            message=_("Are you sure you want to terminate the process running Trellis?", '*'), 
        )

    def execute(self, context):
        trellis_generator = TrellisGenerator.instance()
        terminated = trellis_generator.terminate_ready_trellis_process(self)
        if terminated:
            return {"FINISHED"}
        else:
            return {"CANCELLED"}
        


class Trellis_OT_TogglePanel(bpy.types.Operator):
    bl_idname = "blenderai_zealo.trellis_toggle_panel"
    bl_label = _("Toggle Trellis Generator Panel", '*')
    
    def execute(self, context):
        gen_props = context.scene.gen_props
        gen_props.show_trellis = not gen_props.show_trellis
        return {"FINISHED"}
    
class Trellis_OT_AddImg23DTask(
    AsyncOperatorMixin, 
    bpy.types.Operator
):
    bl_idname = "blenderai_zealo.trellis_add_image_to_3d_task"
    bl_label = _("Add Image to 3D Task in Trellis Generator", '*')


    task_name: bpy.props.StringProperty(
        name=_("Task Name", '*'), 
    )

    image_path: bpy.props.StringProperty(
        name=_("Image Path", '*'), 
        subtype="FILE_PATH", 
    )

    preprocess_image: bpy.props.BoolProperty(
        name=_("Preprocess Image", '*'), 
        default=True, 
    )

    output_type: bpy.props.EnumProperty(
        name=_("Output Type", '*'), 
        items=[
            ("model", _("Model", '*'), ""), 
            ("base_model", _("Base Model", '*'), ""), 
        ], 
        default="model"
    )



    def invoke(self, context, event):
        self.image_path = ""
        task_length = len(context.scene.trellisgen_props.img23d_tasks)
        self.task_name = _("Task", '*') + f"{task_length}"
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        icons_loader = IconsLoader.instance()
        layout = self.layout
        layout.prop(self, "task_name")
        layout.label(text=_("Only png and jpeg format.", '*'), icon_value=icons_loader.get_icon_id("image"))
        layout.prop(self, "image_path")
        layout.prop(self,"preprocess_image")
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
            self.report({"ERROR"}, _("Now we can only support png and jepg image format.", '*'))
            return {"FINISHED"}

        self.end_token = False
        trellis_generator = TrellisGenerator.instance()
        trellisgen_props = context.scene.trellisgen_props
        tasks = trellisgen_props.img23d_tasks
        task = tasks.add()
        trellisgen_props.img23d_tasks_active_index = len(tasks) - 1
        task.name = self.task_name
        task.image.local_filepath = self.image_path
        task.image.type = type
        task.image.preprocess_image = self.preprocess_image
        task.output.type = self.output_type
        self.task = task

        def add_img23d_task_trellis_thread():
            trellis_generator.image23d(self, task)
        self.async_thread = threading.Thread(target=add_img23d_task_trellis_thread)
        self.async_thread.start()
        self.timer = context.window_manager.event_timer_add(time_step=1.0, window=context.window)
        context.window_manager.modal_handler_add(self)
        self.track_self()
        return {'RUNNING_MODAL'}
    

class Trellisgen_OT_RemoveFailedImg23DTask(bpy.types.Operator):

    bl_idname = "blenderai_zealo.trellisgen_remove_failed_image_to_3d_task"
    bl_label = _("Remove Failed Image to 3D Task", '*')

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        trellisgen_props = context.scene.trellisgen_props
        active_index = trellisgen_props.img23d_tasks_active_index 
        task = trellisgen_props.img23d_tasks[active_index]
        if (task.image.upload_status != "uploading_failed" or 
            (task.image.upload_status == "uploading_end" and task.create_status != "creating_failed")
            ):
            self.report({"ERROR"}, _("You can only remove a uploading failed task or creating failed task", '*'))
            return {"FINISHED"}
        else:
            trellisgen_props.img23d_tasks.remove(active_index)
            return {"FINISHED"}


class Trellisgen_OT_RewatchImg23DTask(AsyncOperatorMixin, bpy.types.Operator):

    bl_idname = "blenderai_zealo.trellisgen_rewatch_image_to_3d_task"
    bl_label = _("Rewatch Image to 3D Task", '*')

    def execute(self, context):
        trellis_generator = TrellisGenerator.instance()
        trellisgen_props = context.scene.trellisgen_props
        active_index = trellisgen_props.img23d_tasks_active_index 
        task = trellisgen_props.img23d_tasks[active_index]
        if task.watch_status != "watching_failed":
            self.report({"ERROR"}, _("You can only re-watch a task with status watch_failed", '*'))
            return {"FINISHED"}
        else:
            self.end_token = False
            def rewatch_img23d_task_trellis_thread():
                trellis_generator.rewatch_img23d_task(self, task)
            self.async_thread = threading.Thread(target=rewatch_img23d_task_trellis_thread)
            self.async_thread.start()
            self.timer = context.window_manager.event_timer_add(time_step=1.0, window=context.window)
            context.window_manager.modal_handler_add(self)
            self.track_self()
            return {"RUNNING_MODAL"}
    

class Trellisgen_OT_RedownloadImg23DTask(AsyncOperatorMixin, bpy.types.Operator):

    bl_idname = "blenderai_zealo.trellisgen_redownload_image_to_3d_task"
    bl_label = _("Redownload Image to 3D Task", '*')


    def execute(self, context):
        trellis_generator = TrellisGenerator.instance()
        trellisgen_props = context.scene.trellisgen_props
        active_index = trellisgen_props.img23d_tasks_active_index 
        task = trellisgen_props.img23d_tasks[active_index]

        if task.output.download_status!= "downloading_failed":
            self.report({"ERROR"}, _("You can only re-download model with status downloading_failed", '*'))
            return {"FINISHED"}
        else:
            self.end_token = False
            def redownload_model_trellis_thread():
                trellis_generator.redownload_img23d_task(self, task)
            self.async_thread = threading.Thread(target=redownload_model_trellis_thread)
            self.async_thread.start()
            self.timer = context.window_manager.event_timer_add(time_step=1.0, window=context.window)
            context.window_manager.modal_handler_add(self)
            self.track_self()
            return {'RUNNING_MODAL'}


class Trellis_OT_ImportModelOfImg23DTask(bpy.types.Operator):

    bl_idname = "blenderai_zealo.trellisgen_import_model_of_image_to_3d_task"
    bl_label = _("Trellis: Import Model Of Success Image 2 3D Task", '*')

    def execute(self, context):
        trellisgen_props = context.scene.trellisgen_props
        active_index = trellisgen_props.img23d_tasks_active_index 
        task = trellisgen_props.img23d_tasks[active_index]
        if task.output.download_status != "downloading_end":
            self.report({"ERROR"}, _("The model hasn't been downloaded yet!", '*'))
            return {"CANCELLED"}
        else:
            local_filepath = task.output.local_filepath
            try:
                bpy.ops.import_scene.gltf(filepath=local_filepath)
            except Exception as e:
                self.report({"ERROR"}, _("Try to import glb file from: ", '*') + local_filepath + _("But get an error: ", '*') + str(e))
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