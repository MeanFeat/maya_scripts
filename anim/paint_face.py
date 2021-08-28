from maya import cmds
from maya.api import OpenMaya
from maya.api.OpenMaya import MSpace, MGlobal, MColor, MVector, MPoint

from core.basis import get_matrix_translation
from tools.paint_system import PaintSystem, PaintPoint
from ui.ui_draw_manager import UIDrawPoint


class PaintableSceneObject:
    def __init__(self, scene_name, dag_path):
        self.scene_name = scene_name
        self.dag_path = dag_path
        self.transform_func = OpenMaya.MFnTransform(dag_path)


class PaintFace(PaintSystem):

    draw_points = []

    drag_strength = 0.5

    def __init__(self, context='paint_trajectory_ctx'):
        super(PaintFace, self).__init__()
        self.context = context
        self.paint_set = cmds.select('paintable')
        self.paintable_scene_objects = []
        self.paintable_points = []

        selection_list = MGlobal.getActiveSelectionList()

        for i in range(0, selection_list.length()):
            scene_name = selection_list.getSelectionStrings()[i]
            dag_path = selection_list.getDagPath(i)
            t = get_matrix_translation(dag_path.inclusiveMatrix())
            point = PaintPoint(t)
            paintable = PaintableSceneObject(scene_name, dag_path)
            self.paintable_scene_objects.append(paintable)
            self.paintable_points.append(point)

        for p in self.paintable_scene_objects:
            cmds.hide(p.scene_name)

    def drag_points(self, drag_point):
        for p in self.paintable_points:
            if p.feathering > 0 and not p.is_locked:
                p.set_world_point((p.world_point + (drag_point - self.brush.last_drag_point.world_point) * p.feathering))
                #scene_object = self.paintable_scene_objects[i]
                #origin = MVector(get_matrix_translation(scene_object.dag_path.exclusiveMatrix()))
                #local = t - origin
                #x_limit = cmds.transformLimits(scene_object.scene_name, query=True, translationX=True)
                #y_limit = cmds.transformLimits(scene_object.scene_name, query=True, translationY=True)
                #z_limit = cmds.transformLimits(scene_object.scene_name, query=True, translationZ=True)
                #min_vec = MVector(x_limit[0], y_limit[0], z_limit[0])
                #max_vec = MVector(x_limit[1], y_limit[1], z_limit[1])
                #local.x = min(max(min_vec.x, local.x), max_vec.x)
                #local.y = min(max(min_vec.y, local.y), max_vec.y)
                #local.z = min(max(min_vec.z, local.z), max_vec.z)
                #p.set_world_point(MPoint(origin + local))

    def build_draw_shapes(self):
        super(PaintFace, self).build_draw_shapes()
        for p in self.paintable_points:
            pos = p.world_point
            point = UIDrawPoint()
            point.set(pos, 3, (0.5, 0.5, 1, 0.5), True)
            self.draw_points.append(point)

    def draw_paint_points(self):
        for i, draw_point in enumerate(self.draw_points):
            point = self.paintable_points[i]
            if point.is_locked:
                draw_point.set(self.paintable_points[i].world_point, 3, (1, 1, 1, 1), True)
            else:
                draw_point.set(self.paintable_points[i].world_point, 3, (0.5, 0.5, 1, 1), True)

    def update_driven_objects(self):
        for i, p in enumerate(self.paintable_scene_objects):

            p.transform_func.setTranslation(MVector(self.paintable_points[i].world_point), MSpace.kWorld)

    def update_view_points(self):
        for i, p in enumerate(self.paintable_scene_objects):
            t = get_matrix_translation(p.dag_path.inclusiveMatrix())
            self.paintable_points[i].set_world_point(MPoint(t))

    def key_driven_objects(self):
        for i, scene_object in enumerate(self.paintable_scene_objects):
            point = self.paintable_points[i]
            if not point.is_locked:
                cmds.setKeyframe(scene_object.scene_name)

    def relax_points(self):
        for i, scene_object in enumerate(self.paintable_scene_objects):
            point = self.paintable_points[i]
            if not point.is_locked:
                scene_object.transform_func.setTranslation(scene_object.transform_func.translation(MSpace.kObject) * (1.0 - (0.1 * point.feathering)), MSpace.kObject)
                cmds.setKeyframe(scene_object.scene_name)

    def lock_points(self):
        for p in self.paintable_points:
            if p.feathering > 0.9:
                p.is_locked = not p.is_locked
