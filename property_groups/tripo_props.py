import bpy
import json
from ..utils import absolute_path

class TripoGenTaskOutputProperties(bpy.types.PropertyGroup):

    def redraw(self, context):
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
                    return
    
    type: bpy.props.EnumProperty(items=[
        ("model", "", ""), 
        ("base_model", "", ""), 
        ("pbr_model", "", "")
    ])
    model_url: bpy.props.StringProperty()
    model_local_filepath: bpy.props.StringProperty()
    model_download_status: bpy.props.EnumProperty(
        items=[
            ('not_yet', "", ""), 
            ('downloading', "", ""),
            ('downloading_end', "", ""),
            ('downloading_failed', "", ""),
        ], 
        update=redraw
    )
    model_download_progress: bpy.props.StringProperty(
        default="0.0%", 
        update=redraw, 
    )
    base_model_url: bpy.props.StringProperty()
    base_model_local_filepath: bpy.props.StringProperty()
    base_model_download_status: bpy.props.EnumProperty(
        items=[
            ('not_yet', "", ""), 
            ('downloading', "", ""),
            ('downloading_end', "", ""),
            ('downloading_failed', "", ""),
        ], 
        default="not_yet", 
        update=redraw
    )
    base_model_download_progress: bpy.props.StringProperty(
        default="0.0%", 
        update=redraw, 
    )
    pbr_model_url: bpy.props.StringProperty()
    pbr_model_local_filepath: bpy.props.StringProperty()
    pbr_model_download_status: bpy.props.EnumProperty(
        items=[
            ('not_yet', "", ""), 
            ('downloading', "", ""),
            ('downloading_end', "", ""),
            ('downloading_failed', "", ""),
        ], 
        default="not_yet", 
        update=redraw
    )
    pbr_model_download_progress: bpy.props.StringProperty(
        default="0.0%", 
        update=redraw, 
    )
    rendered_image_url: bpy.props.StringProperty()
    rendered_image_local_filepath: bpy.props.StringProperty()
    rendered_image_download_status: bpy.props.EnumProperty(
        items=[
            ('not_yet', "", ""), 
            ('downloading', "", ""),
            ('downloading_end', "", ""),
            ('downloading_failed', "", ""),
        ], 
        default="not_yet", 
        update=redraw
    )
    rendered_image_download_progress: bpy.props.StringProperty(
        default="0.0%", 
        update=redraw, 
    )


class TripoGenTextTo3DTaskProperties(bpy.types.PropertyGroup):

    def redraw(self, context):
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
                    return


    name: bpy.props.StringProperty()
    prompt: bpy.props.StringProperty()
    model_version: bpy.props.EnumProperty(
        items=[
            ("v2.0-20240919", "", ""), 
            ("v1.4-20240625", "", ""), 
            ("v1.3-20240522", "", "")
        ],
    )
    create_status: bpy.props.EnumProperty(
        items=[
            ("not_yet", "", ""), 
            ("creating", "", ""), 
            ("creating_end", "", ""), 
            ("creating_failed", "", ""), 
        ], 
        update=redraw, 
    )
    id: bpy.props.StringProperty()  
    watch_status: bpy.props.EnumProperty(
        items=[
            ('not_yet', "", ""), 
            ('watching', "", ""),
            ('watching_end', "", ""),
            ('watching_failed', "", ""),
        ], 
        default="not_yet", 
        update=redraw
    )
    watch_progress: bpy.props.StringProperty(
        default="queued: 0.0%", 
        update=redraw, 
    )
    output: bpy.props.PointerProperty(type=TripoGenTaskOutputProperties)



class TripoGenImageTo3DTaskImageProperties(bpy.types.PropertyGroup):

    def redraw(self, context):
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
                    return

    local_filepath: bpy.props.StringProperty()
    upload_status: bpy.props.EnumProperty(
        items=[
            ("not_yet", "", ""), 
            ("uploading", "", ""), 
            ("uploading_end", "", ""), 
            ("uploading_failed", "", ""), 
        ], 
        default="not_yet", 
        update=redraw
    )
    type: bpy.props.StringProperty()
    token: bpy.props.StringProperty()


class TripoGenImageTo3DTaskProperties(bpy.types.PropertyGroup):

    def redraw(self, context):
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
                    return

    
    name: bpy.props.StringProperty()
    model_version: bpy.props.EnumProperty(
        items=[
            ("v2.0-20240919", "", ""), 
            ("v1.4-20240625", "", ""), 
            ("v1.3-20240522", "", "")
        ]
    )

    image: bpy.props.PointerProperty(type=TripoGenImageTo3DTaskImageProperties)

    create_status: bpy.props.EnumProperty(
        items=[
            ("not_yet", "", ""), 
            ("creating", "", ""), 
            ("creating_end", "", ""), 
            ("creating_failed", "", ""), 
        ], 
        default="not_yet", 
        update=redraw, 
    )
    
    id: bpy.props.StringProperty() 

    watch_status: bpy.props.EnumProperty(
        items=[
            ('not_yet', "", ""), 
            ('watching', "", ""),
            ('watching_end', "", ""),
            ('watching_failed', "", ""),
        ], 
        default="not_yet", 
        update=redraw
    )

    watch_progress: bpy.props.StringProperty(
        default="queued: 0.0%", 
        update=redraw, 
    )

    output: bpy.props.PointerProperty(type=TripoGenTaskOutputProperties)

class TripoGenProperties(bpy.types.PropertyGroup):

    txt23d_tasks: bpy.props.CollectionProperty(type=TripoGenTextTo3DTaskProperties) 
    txt23d_task_active_index: bpy.props.IntProperty(
        min=1, 
    )
    img23d_tasks: bpy.props.CollectionProperty(type=TripoGenImageTo3DTaskProperties) 
    img23d_task_active_index: bpy.props.IntProperty(
        min=1, 
    )