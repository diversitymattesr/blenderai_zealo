import bpy



class GeneratorProperties(bpy.types.PropertyGroup):

    def redraw(self, context):
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
                    return
                
    windows_long_path_support: bpy.props.BoolProperty(
        default=False
    )

    tripo_python_dependencies_installed: bpy.props.BoolProperty(
        default=False, 
        update=redraw, 
    )

    tripo_python_dependencies_install_status: bpy.props.EnumProperty(
        items=[
            ("not_yet", "", ""), 
            ("installing", "", ""), 
            ("installing_end", "", ""), 
            ("installing_failed", "", "")
        ], 
        default="not_yet", 
        update=redraw, 
    )

    tripo_python_dependencies_install_message: bpy.props.StringProperty(
        update=redraw, 
    )

    tripo_ready: bpy.props.BoolProperty(
        default=False, 
        update=redraw, 
    )

    tripo_check_ready_status: bpy.props.EnumProperty(
        items=[
            ("not_yet", "", ""), 
            ("checking", "", ""), 
            ("checking_end", "", ""), 
            ("checking_failed", "", "")
        ], 
        update=redraw, 
    )

    tripo_check_ready_message: bpy.props.StringProperty(
        update=redraw, 
    )

    show_tripo: bpy.props.BoolProperty(
        default=False
    )

    trellis_manifest_nvidia_driver: bpy.props.BoolProperty(
        default=False
    )

    trellis_python_dependencies_installed: bpy.props.BoolProperty(
        default=False
    )

    trellis_python_dependencies_install_status: bpy.props.EnumProperty(
        items=[
            ("not_yet", "", ""), 
            ("installing", "", ""), 
            ("installing_end", "", ""), 
            ("installing_failed", "", "")
        ], 
        default="not_yet", 
        update=redraw, 
    )

    
    trellis_python_dependencies_install_message: bpy.props.StringProperty(
        update=redraw, 
    )

    trellis_ready: bpy.props.BoolProperty(
        default=False, 
        update=redraw, 
    )

    trellis_make_ready_status: bpy.props.EnumProperty(
        items=[
            ("not_yet", "", ""), 
            ("making_ready", "", ""), 
            ("making_ready_end", "", ""), 
            ("making_ready_failed", "", "")
        ], 
        update=redraw, 
    )
    
    trellis_make_ready_message: bpy.props.StringProperty(
        update=redraw
    )

    show_trellis: bpy.props.BoolProperty(
        default=False
    )