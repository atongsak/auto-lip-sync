# Make it an addon
bl_info = {
    "name": "My Custom Panel",
    "author": "Annette Tongsak",
    "version": (0, 0, 1),
    "blender": (5, 0, 1),
    "location": "3D Viewport > Sidebar > My Custom Panel category",
    "description": "My custom operator buttons",
    "category": "Development",
}

# https://youtu.be/Qyy_6N3JV3k?si=JVEwFaSNXYJqNJKK
# Give Python access to Blender's Python API
import bpy

# Class naming convention for a panel 'CATEGORY_TYPE_name'
class VIEW3D_PT_my_custom_panel(bpy.types.Panel):
    pass

    # Where to add the panel in the UI
    bl_space_type = "VIEW_3D" # 3D viewport area https://docs.blender.org/api/current/bpy_types_enum_items/space_type_items.html#rna-enum-space-type-items
    bl_region_type = "UI" # Sidebar region https://docs.blender.org/api/current/bpy_types_enum_items/region_type_items.html#rna-enum-region-type-items
    
    # Add labels
    bl_category = "My Custom Panel category"
    bl_label = "My Custom Panel label" # Found at top of the panel

    
    def draw(self, context):
        """Define the layout of the panel"""
        # https://docs.blender.org/api/current/bpy.ops.mesh.html
        
        row = self.layout.row()
        row.operator("mesh.primitive_cube_add", text="Add Cube")
        
        row1 = self.layout.row()
        row1.operator("mesh.primitive_ico_sphere_add", text="Add Ico Sphere")
        
        row2 = self.layout.row()
        row2.operator("object.shade_smooth", text="Shade Smooth")
        

# Register the panel with Blender

def register():
    bpy.utils.register_class(VIEW3D_PT_my_custom_panel)


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_my_custom_panel)


if __name__ == "__main__":
    register()