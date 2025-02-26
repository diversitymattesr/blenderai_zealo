# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import time
from .property_groups import *
from .operators import *
from .ui import *
from .icons import *
from .utils import initial_properties, absolute_path, translations_dict
from .preferences import *

# TODO 1. Refactor the dependencies check machanism of each ai generator: unify all check operation into one; use dynamic python package import;
# TODO 2. Add update feature for this addon: monitor running state of all async operator; use git to update


bl_info = {
    "name": "Blenderai_zealo",
    "author": "zealo",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "description": "This is a extension focused on the AI Mesh Generation",
    "doc_url": "https://github.com/diversitymattesr/blenderai_zealo",
    "category": "3D View",
    "license": "GPL-2.0-or-later",
}

classes = (
    BlenderAIZealoPreferences, 
    TripoGenTaskOutputProperties, 
    TripoGenTextTo3DTaskProperties,
    TripoGenImageTo3DTaskImageProperties, 
    TripoGenImageTo3DTaskProperties, 
    TrellisGenImageTo3DTaskImageProperties, 
    TrellisGenTaskOutputProperties, 
    TrellisGenImageTo3DTaskProperties, 
    TrellisGenProps, 
    TripoGenProperties,
    GeneratorProperties, 
    UpdaterProperties, 
    Tripogen_OT_TogglePanel, 
    Generator_PT_Panel, 
    Tripogen_PT_Panel,
    Tripogen_UL_Text23D_Tasks, 
    Tripogen_UL_Image23D_Tasks, 
    Tripo_OT_CHECK_PYTHON_DEPENDENCIES, 
    Tripo_OT_INSTALL_PYTHON_DEPENDENCIES, 
    Tripo_OT_CHECK_READY, 
    Tripogen_OT_AddTxt23DTask, 
    Tripogen_OT_RemoveFailedTxt23DTask, 
    Tripogen_OT_RewatchTxt23DTask, 
    Tripogen_OT_RedownloadOfTxt23DTask, 
    Tripogen_OT_ImportModelOfTxt23DTask, 
    Tripogen_OT_AddImg23DTask,
    Tripogen_OT_RemoveFailedImg23DTask, 
    Tripogen_OT_RewatchImg23DTask, 
    Tripogen_OT_RedownloadImg23DTask, 
    Tripogen_OT_ImportModelOfImg23DTask, 
    Trellis_OT_CHECK_MANIFEST_NVIDIA_DRIVER, 
    Trellis_OT_CHECK_PYTHON_DEPENDENCIES, 
    Trellis_OT_INSTALL_PYTHON_DEPENDENCIES, 
    Trellis_OT_CHECK_READY, 
    Trellis_OT_MakeReady, 
    Trellis_OT_TogglePanel, 
    Trellisgen_UL_Image23D_Tasks, 
    Trellis_PT_Panel, 
    Trellis_OT_AddImg23DTask, 
    Trellis_OT_ImportModelOfImg23DTask, 
    Trellisgen_OT_RemoveFailedImg23DTask, 
    Trellisgen_OT_RewatchImg23DTask, 
    Trellisgen_OT_RedownloadImg23DTask, 
    Generator_OT_CHECK_WINDOWS_LONG_PATH_SUPPORT, 
    Generator_OT_SELECT_FOLDER_TO_CONTAIN_FILE, 
    Trellis_OT_Manually_Close_Trellis_Process, 
    BlenderAI_Zealo_OT_TOGGLE_UPDATE_PANEL,
    BlenderAI_Zealo_OT_CHECK_UPDATE,  
    BlenderAI_Zealo_Updater_PT_Panel, 
    BlenderAI_Zealo_OT_Download_Release, 
    BlenderAI_Zealo_OT_Update_To_Release, 
)




def register():
    print("================Register BlenderAI Zealo=====================")
    bpy.app.translations.register(__name__, translations_dict)
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gen_props = bpy.props.PointerProperty(type=GeneratorProperties)
    bpy.types.Scene.tripogen_props = bpy.props.PointerProperty(type=TripoGenProperties)
    bpy.types.Scene.trellisgen_props = bpy.props.PointerProperty(type=TrellisGenProps)
    bpy.types.Scene.updater_props = bpy.props.PointerProperty(type=UpdaterProperties)
    IconsLoader.register()
    bpy.app.handlers.load_post.append(initial_properties)


def unregister():
    print("================Unregister BlenderAI Zealo=====================")
    if AsyncOperatorMixin.OPERATOR_IN_MODAL:
        running_operators = set(AsyncOperatorMixin.OPERATOR_IN_MODAL)
        running_operators_message = ""
        for op in running_operators:
            running_operators_message += f"{op.__class__.__name__}\n"
        raise RuntimeError(f"There is still operators related to blenderai_zealo addon running\n{running_operators_message}" )
    del bpy.types.Scene.gen_props
    del bpy.types.Scene.tripogen_props
    del bpy.types.Scene.trellisgen_props
    del bpy.types.Scene.updater_props
    IconsLoader.unregister()
    bpy.app.handlers.load_post.remove(initial_properties)
    bpy.app.translations.unregister(__name__)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    
    
