import bpy



class UpdaterProperties(bpy.types.PropertyGroup):

    def redraw(self, context):
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
                    return

    show_update_panel: bpy.props.BoolProperty(
        default=False
    )

    engine: bpy.props.EnumProperty(
        items=[
            ("github", "Github", ""),
            ("gitee", "Gitee", ""), 
        ], 
        default="github"
    )

    check_update_status: bpy.props.EnumProperty(
        items=[
            ("not_yet", "", ""), 
            ("checking", "", ""), 
            ("checking_failed", "", ""), 
            ("checking_end", "", ""), 
        ], 
        default="not_yet", 
        update=redraw, 
    )

    check_update_message: bpy.props.StringProperty(
        default="", 
        update=redraw, 
    )

    update_to_release_name: bpy.props.StringProperty(
        default="", 
        update=redraw, 
    )

    download_release_status: bpy.props.EnumProperty(
        items=[
            ("not_yet", "", ""), 
            ("downloading", "", ""), 
            ("downloading_failed", "", ""), 
            ("downloading_end", "", ""), 
        ], 
        update=redraw, 
    )

    download_release_message: bpy.props.StringProperty(
        default="", 
        update=redraw, 
    )

    downloaded_release_name: bpy.props.StringProperty(
        default=""
    )