bl_info = {
    "name": "Move X Axis",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy

class ObjectMoveX(bpy.types.Operator):
    """My Object Moving Script"""       # Use this as a tooltip for menu items and buttons
    bl_idname = "object.move_x"         # Unique identifier for buttons and menu items to ref
    bl_label = "Move X by One"          # Display name in the interface
    bl_options = {'REGISTER', 'UNDO'}   # Enable undo for the operator

    def execute(self, context):         # execute() is called when running the operator
        # OG script
        scene = bpy.context.scene
        for obj in scene.objects:
            obj.location.x += 1.0
        
        return {'FINISHED'}             # Lets Blender know the operator finished successfully
    
def menu_func(self, context):
    self.layout.operator(ObjectMoveX.bl_idname)

# Only runs when enabling the add-on, meaning the module can be loaded 
# without activating the add-on
def register(): 
    bpy.utils.register_class(ObjectMoveX)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    
# Unload anything setup by register, called whne the add-on is disabled
def unregister():
    bpy.utils.unregister_class(ObjectMoveX)
    
# Allows you to run the script directly from Blender's Text editor 
# to test the addon without having to install it
if __name__ == "__main__":
    register()
    