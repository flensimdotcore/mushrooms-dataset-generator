import bpy
import math
import random
import os
from mathutils import Vector
import numpy as np
import os
import glob

class MushroomSceneGenerator:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.scene_data = []
        self.mushroom_classes = ['mushroom']
        self.mushrooms = []
        self.bboxes = []
        self.camera = None
        self.camera_height = 0.97225
        self.displace_texture = None
        self.cap_mushroom_mat_name = ""
        self.stem_mushroom_mat_name = ""
        self.dirt_mat_name = ""

        os.makedirs(os.path.join(output_dir, "train/images"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "train/labels"), exist_ok=True)

        os.makedirs(os.path.join(output_dir, "val/images"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "val/labels"), exist_ok=True)

        os.makedirs(os.path.join(output_dir, "test/images"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "test/labels"), exist_ok=True)

    def clear_scene(self):
        self.mushrooms = []
        self.bboxes = []

        for obj in list(bpy.data.objects):
            if obj.type not in ['CAMERA']:
                bpy.data.objects.remove(obj, do_unlink=True)

        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)

        bpy.context.scene.view_settings.exposure = 0.0
        bpy.context.scene.view_settings.gamma = 1.0
        # bpy.context.scene.view_settings.saturation = 1.0

    def create_shelf(self, material_name, width=2.0, depth=1.0, height=0.05):
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        shelf = bpy.context.active_object
        shelf.name = "Shelf"
        shelf.dimensions = (width, depth, height)

        shelf.location = (0.5, 0.5, -height/2)

        self.apply_material_to_object(shelf.name, material_name)

        return shelf

    def world_to_camera_view(self, camera, world_point):
        camera_matrix = camera.matrix_world.normalized().inverted()

        point_camera = camera_matrix @ Vector(world_point)

        camera_data = camera.data

        if camera_data.type == 'PERSP':
            aspect = 640 / 640 # scene.render.resolution_x / scene.render.resolution_y
            fov = camera_data.angle

            x = point_camera.x / (aspect * 2 * math.tan(fov / 2) * point_camera.z)
            y = point_camera.y / (2 * math.tan(fov / 2) * point_camera.z)

        x_normalized = y + 0.5
        y_normalized = 0.5 - x

        return Vector((x_normalized, y_normalized))

    def create_mushroom(self, cap_material_name, stem_material_name, stem_radius=0.05,
                        stem_height=0.2, cap_radius=0.1, location=(0.5, 0.5, 0), random_scale_factor=1.0, angle_variation=15.0):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16,
            radius=stem_radius,
            depth=stem_height
        )
        stem = bpy.context.active_object
        stem.name = "Mushroom_Stem"
        self.apply_material_to_object(stem.name, stem_material_name)

        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=cap_radius,
            segments=32,
            ring_count=16
        )
        cap = bpy.context.active_object
        cap.name = "Mushroom_Cap"

        cap.scale.z = 0.7

        cap.location.z += 0.04 * random_scale_factor
        bpy.ops.object.shade_smooth()

        bpy.ops.object.modifier_add(type='DISPLACE')
        displace_mod = cap.modifiers["Displace"]

        if not self.displace_texture:
            self.displace_texture = bpy.data.textures.new("MushroomNoise", 'CLOUDS')
            self.displace_texture.noise_scale = 0.2
            self.displace_texture.noise_depth = 3
            self.displace_texture.cloud_type = 'GRAYSCALE'

        displace_mod.texture = self.displace_texture
        displace_mod.strength = 0.02

        self.apply_material_to_object(cap.name, cap_material_name)

        mushroom_group = bpy.data.objects.new(f"Mushroom", None)
        bpy.context.collection.objects.link(mushroom_group)

        stem.parent = mushroom_group
        cap.parent = mushroom_group

        mushroom_group.location = location

        mushroom_group.rotation_euler.z = random.uniform(0, math.pi*2)
        mushroom_group.rotation_euler.x += math.radians(random.uniform(-angle_variation, angle_variation))
        mushroom_group.rotation_euler.y += math.radians(random.uniform(-angle_variation, angle_variation))

        bpy.context.view_layer.update()
        cap_world_location = cap.matrix_world.translation

        center_2d = self.world_to_camera_view(self.camera, cap_world_location)

        bepsilon = 0.01

        if 1.0 < center_2d[0] <= 1.0 + bepsilon:
            center_2d[0] = 1.0
        elif 0.0 - bepsilon <= center_2d[0] < 0.0:
            center_2d[0] = 0.0

        if 1.0 < center_2d[1] <= 1.0 + bepsilon:
            center_2d[1] = 1.0
        elif 0.0 - bepsilon <= center_2d[1] < 0.0:
            center_2d[1] = 0.0

        if (center_2d[0] > 1.0 + bepsilon or 0.0 - bepsilon > center_2d[0]
            or center_2d[1] > 1.0 + bepsilon or 0.0 - bepsilon > center_2d[1]):
            bbox = None
        else:
            bbox = {
                'side_length': cap_radius * 2,
                'center': [center_2d[0], center_2d[1]]
            }

        return mushroom_group, bbox

    def setup_camera(self, height=2.0):
        bpy.ops.object.camera_add(location=(0.5, 0.5, height))
        camera = bpy.context.active_object
        camera.name = "Camera"

        camera.rotation_euler = (math.radians(0), 0, math.radians(90))

        camera.data.type = 'PERSP'
        camera.data.lens = 35

        bpy.context.scene.camera = camera

        return camera

    def setup_lighting(self):
        for obj in bpy.data.objects:
            if obj.type == 'LIGHT':
                bpy.data.objects.remove(obj, do_unlink=True)

        fill_light_location = (random.uniform(-3.0, 3.0), random.uniform(-3.0, 3.0), random.uniform(0.5, 8.0))

        bpy.ops.object.light_add(type='AREA', location=fill_light_location)
        sun = bpy.context.active_object
        sun.data.energy = 200.0
        sun.data.size = 5.0
        sun.rotation_euler = (0, 0, 0)

    def create_simple_material(self, name, rgb_channels=[0.75, 0.0, 0.75]):
        mat_name = f"{name}"

        material = bpy.data.materials.new(name=mat_name)
        if not material.node_tree:
            material.use_nodes = True

        material.node_tree.nodes.clear()

        nodes = material.node_tree.nodes

        bsdf = nodes.new(type='ShaderNodeBsdfDiffuse')
        bsdf.inputs[0].default_value = (rgb_channels[0], rgb_channels[1], rgb_channels[2], 1.0)

        output = nodes.new(type='ShaderNodeOutputMaterial')
        material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        return material

    def create_textured_material(self, name, texture_path, roughness=1.0):
        if not os.path.exists(texture_path):
            return

        mat_name = f"{name}"
        material = bpy.data.materials.new(name=mat_name)
        if not material.node_tree:
            material.use_nodes = True

        material.node_tree.nodes.clear()

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        tex_image = nodes.new(type='ShaderNodeTexImage')
        tex_image.image = bpy.data.images.load(texture_path)

        principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')

        principled_bsdf.inputs['Roughness'].default_value = roughness
        principled_bsdf.inputs['Metallic'].default_value = 0.0

        material_output = nodes.new(type='ShaderNodeOutputMaterial')

        tex_image.location = (-400, 300)
        principled_bsdf.location = (-100, 300)
        material_output.location = (200, 300)

        if tex_image.image:
            links.new(tex_image.outputs['Color'], principled_bsdf.inputs['Base Color'])

        links.new(principled_bsdf.outputs['BSDF'], material_output.inputs['Surface'])

        return material

    def apply_material_to_object(self, obj_name, material_name):
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            return

        material = bpy.data.materials[material_name]
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)

    def apply_mushroom_materials(self, material_name):
        for obj in bpy.data.objects:
            if "Mushroom" in obj.name and obj.type == 'MESH':
                self.apply_texture_to_object(obj.name, material_name)

    def save_bboxes_to_file(self, bboxes, filepath):
        with open(filepath, 'w') as f:
            for bbox in bboxes:
                center_x, center_y = bbox['center']
                side_length = bbox['side_length']

                line = f"0 {center_y:.6f} {center_x:.6f} {side_length:.6f} {side_length:.6f}\n"
                f.write(line)

    def check_collision(self, new_center, new_radius, existing_mushrooms, min_distance_factor=1.0):
        for mushroom_data in existing_mushrooms:
            existing_center = mushroom_data['center']
            existing_radius = mushroom_data['side_length'] / 2

            distance = (Vector(new_center) - Vector(existing_center)).length

            min_distance = (new_radius + existing_radius) * min_distance_factor

            if distance < min_distance:
                return True
        return False

    def render_scene(self, batch_name, scene_id=None, resolution=(640, 640)):
        image_files = glob.glob(os.path.join(self.output_dir, f"{batch_name}", "images", "scene_*.png"))

        if not image_files:
            scene_id = 0
        else:
            existing_ids = []
            for file in image_files:
                try:
                    basename = os.path.basename(file)
                    num_str = basename.replace("scene_", "").replace(".png", "")
                    scene_num = int(num_str)
                    existing_ids.append(scene_num)
                except ValueError:
                    continue

            scene_id = max(existing_ids) + 1

        bpy.context.scene.render.engine = 'BLENDER_EEVEE' # CYCLES
        bpy.context.scene.render.resolution_x = resolution[0]
        bpy.context.scene.render.resolution_y = resolution[1]
        bpy.context.scene.render.image_settings.file_format = 'PNG'

        image_path = os.path.join(self.output_dir, f"{batch_name}", "images", f"scene_{scene_id:04d}.png")

        bpy.context.scene.view_settings.gamma = random.uniform(0.1, 2.0) # min 0.1 max 5.0
        # bpy.context.scene.view_settings.saturation = 1.5

        bpy.context.scene.render.filepath = image_path
        bpy.ops.render.render(write_still=True)

        bboxes = self.bboxes
        label_path = f"{self.output_dir}/{batch_name}/labels/scene_{scene_id:04d}.txt"
        self.save_bboxes_to_file(bboxes, label_path)

    def generate_scene(self, batch_name, scene_id, params, max_attempts_per_mushroom=50):
        self.clear_scene()

        self.create_shelf(
            self.dirt_mat_name,
            width=params['shelf_width'],
            depth=params['shelf_depth'],
            height=params['shelf_height']
        )

        scale = params['mushroom_scale']
        mushroom_size_min = params['mushroom_size_min']
        mushroom_size_max = params['mushroom_size_max']

        for i in range(params['mushroom_count']):
            isValid = False
            attempts = 0
            x = 0
            y = 0
            stem_r = 0
            stem_h = 0
            cap_r = 0

            while not isValid and attempts < max_attempts_per_mushroom:
                attempts += 1

                x = random.uniform(
                    0.0,
                    1.0
                )
                y = random.uniform(
                    0.0,
                    1.0
                )

                random_factor = random.uniform(mushroom_size_min, mushroom_size_max)

                # stem_r = 0.05 * scale * random_factor / (np.log(2*random_factor + 1))
                stem_r = 0.05 * scale * random_factor
                stem_h = 0.2 * scale * random_factor
                cap_r = 0.1 * scale * random_factor

                center = [x, y]
                radius = cap_r

                if not self.check_collision(center, cap_r, self.bboxes):
                    isValid = True

            if not isValid:
                continue

            mushroom, bbox = self.create_mushroom(
                self.cap_mushroom_mat_name,
                self.stem_mushroom_mat_name,
                stem_radius=stem_r,
                stem_height=stem_h,
                cap_radius=cap_r,
                location=(x, y, params['shelf_height']/2),
                random_scale_factor=random_factor
            )

            self.mushrooms.append(mushroom)

            if bbox is not None:
                self.bboxes.append(bbox)

        self.setup_lighting()
        self.render_scene(batch_name, scene_id)

    def setup_environment(self):
        self.camera = self.setup_camera(height=self.camera_height)

        self.cap_mushroom_mat_name = "Material_cap_mushroom"
        self.stem_mushroom_mat_name = "Material_stem_mushroom"
        self.dirt_mat_name = "Material_dirt"
        self.create_textured_material(self.cap_mushroom_mat_name, "./textures/mushroom_v2.png")
        self.create_textured_material(self.stem_mushroom_mat_name, "./textures/mushroom_v2.png")
        self.create_simple_material(self.dirt_mat_name, rgb_channels=[0.01, 0.007, 0.004])

    def generate_dataset(self, num_scenes=1):
        self.setup_environment()

        train_batch_ratio = float(os.environ.get('TRAIN_BATCH_RATIO', 0.7))
        val_batch_ratio = float(os.environ.get('VAL_BATCH_RATIO', 0.15))
        test_batch_ratio = float(os.environ.get('TEST_BATCH_RATIO', 0.15))

        train_num_scenes = int(num_scenes * train_batch_ratio)
        val_num_scenes = int(num_scenes * val_batch_ratio)
        test_num_scenes = int(num_scenes * test_batch_ratio)

        # train batch
        for i in range(train_num_scenes):
            generation_params = {
                'shelf_width': 1.0,
                'shelf_depth': 1.0,
                'shelf_height': 0.05,
                'mushroom_count': random.randint(int(os.environ.get('MUSHROOM_COUNT_MIN', 10)),
                                                 int(os.environ.get('MUSHROOM_COUNT_MAX', 75))),
                'mushroom_scale': 0.5,
                'mushroom_size': float(os.environ.get('MUSHROOM_SIZE', 1.0)),
                'mushroom_size_min': float(os.environ.get('MUSHROOM_SIZE_MIN', 0.4)),
                'mushroom_size_max': float(os.environ.get('MUSHROOM_SIZE_MAX', 1.6))
            }
            self.generate_scene("train", i, generation_params)

        # val batch
        for i in range(val_num_scenes):
            generation_params = {
                'shelf_width': 1.0,
                'shelf_depth': 1.0,
                'shelf_height': 0.05,
                'mushroom_count': random.randint(int(os.environ.get('MUSHROOM_COUNT_MIN', 10)),
                                                 int(os.environ.get('MUSHROOM_COUNT_MAX', 75))),
                'mushroom_scale': 0.5,
                'mushroom_size': float(os.environ.get('MUSHROOM_SIZE', 1.0)),
                'mushroom_size_min': float(os.environ.get('MUSHROOM_SIZE_MIN', 0.4)),
                'mushroom_size_max': float(os.environ.get('MUSHROOM_SIZE_MAX', 1.6))
            }
            self.generate_scene("val", i, generation_params)

        # test batch
        for i in range(test_num_scenes):
            generation_params = {
                'shelf_width': 1.0,
                'shelf_depth': 1.0,
                'shelf_height': 0.05,
                'mushroom_count': random.randint(int(os.environ.get('MUSHROOM_COUNT_MIN', 10)),
                                                 int(os.environ.get('MUSHROOM_COUNT_MAX', 75))),
                'mushroom_scale': 0.5,
                'mushroom_size': float(os.environ.get('MUSHROOM_SIZE', 1.0)),
                'mushroom_size_min': float(os.environ.get('MUSHROOM_SIZE_MIN', 0.4)),
                'mushroom_size_max': float(os.environ.get('MUSHROOM_SIZE_MAX', 1.6))
            }
            self.generate_scene("test", i, generation_params)

if __name__ == "__main__":
    generator = MushroomSceneGenerator(output_dir=os.path.join(os.environ.get('DatasetRoot', os.environ.get('HOME')),
                                                               'mushroom_dataset'))

    generator.generate_dataset(
        num_scenes=int(os.environ.get('NUM_SCENES', 1))
    )
