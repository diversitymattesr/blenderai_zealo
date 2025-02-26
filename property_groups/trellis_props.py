import bpy


class TrellisGenImageTo3DTaskImageProperties(bpy.types.PropertyGroup):

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
    preprocess_image: bpy.props.BoolProperty(
        default=True
    )


class TrellisGenTaskOutputProperties(bpy.types.PropertyGroup):

    def redraw(self, context):
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
                    return
                
    type: bpy.props.EnumProperty(
        items=[
            ("base_model", "", ""), 
            ("model", "", ""), 
        ],
        default="base_model"
    )

    download_status: bpy.props.EnumProperty(
        items=[
            ("not_yet", "", ""), 
            ("downloading", "", ""), 
            ("downloading_end", "", ""), 
            ("downloading_failed", "", "")
        ], 
        default="not_yet", 
        update=redraw
    )

    download_progress: bpy.props.StringProperty(
        default="0.0%", 
        update=redraw
    )

    url: bpy.props.StringProperty()

    local_filepath: bpy.props.StringProperty()


class TrellisGenImageTo3DTaskProperties(bpy.types.PropertyGroup):

    def redraw(self, context):
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
                    return

    name: bpy.props.StringProperty()

    image: bpy.props.PointerProperty(type=TrellisGenImageTo3DTaskImageProperties)

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
        name="Task Watch Status", 
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

    output: bpy.props.PointerProperty(type=TrellisGenTaskOutputProperties)



class TrellisGenProps(bpy.types.PropertyGroup):

    img23d_tasks: bpy.props.CollectionProperty(type=TrellisGenImageTo3DTaskProperties)

    img23d_tasks_active_index: bpy.props.IntProperty(
        min=1, 
    )