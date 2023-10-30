# -*- coding: utf-8 -*-

__title__ = ""  # Name of the button displayed in Revit UI
__doc__ = ""  # Description of the button displayed in Revit UI
__autor__ = 'Slava Filimonenko'  # Script's autor

import math
# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
import os, sys, datetime
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.DB.Analysis import *
from Autodesk.Revit.DB.Architecture import *
# pyrevit
from pyrevit import forms, revit, script

# .NET Imports
import clr

clr.AddReference('System')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from System.Collections.Generic import List
from pyrevit.forms import WPFWindow

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
doc = __revit__.ActiveUIDocument.Document  # type: Document
uidoc = __revit__.ActiveUIDocument  # type: UIDocument
app = __revit__.Application  # type: Application

stairs_collector = FilteredElementCollector(doc). \
    OfCategory(BuiltInCategory.OST_Stairs). \
    WhereElementIsNotElementType(). \
    ToElements()
runs_collector = FilteredElementCollector(doc). \
    OfCategory(BuiltInCategory.OST_StairsRuns). \
    WhereElementIsNotElementType(). \
    ToElements()

floors_collector = FilteredElementCollector(doc). \
    OfCategory(BuiltInCategory.OST_Floors). \
    WhereElementIsNotElementType(). \
    ToElements()


FloorTypes = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsElementType().ToElements()

floor_to_show = [floor.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() for floor in FloorTypes]
res = forms.SelectFromList.show(floor_to_show, button_name="Select item")

for floor in FloorTypes:
    if floor.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() == res:
        floor_type_id = floor.Id


def getting_parameters_for_runs(el):
    # runs element from element id
    runs_element = doc.GetElement(r)
    # getting actual width of  run_width
    runs_width = runs_element.ActualRunWidth
    # params of rises and treads
    runs_actualNumberOfRises = runs_element.LookupParameter("Actual Number of Risers").AsInteger()
    runs_actualNumberOfTreads = runs_element.LookupParameter("Actual Number of Treads").AsInteger()
    run_base_height = runs_element.LookupParameter("Relative Base Height").AsDouble()
    run_top_height = runs_element.LookupParameter("Relative Top Height").AsDouble()
    # getting run params
    r_depth = runs_element.LookupParameter("Actual Tread Depth").AsDouble()
    r_height = runs_element.LookupParameter("Actual Riser Height").AsDouble()
    return runs_element, runs_width, r_depth, r_height, runs_actualNumberOfRises, runs_actualNumberOfTreads, run_base_height, run_top_height


def is_face_planar(face, tolerance=0.001):
    normal = face.ComputeNormal(XYZ.BasisZ)
    return normal.GetLength() < tolerance


def create_point(count, profile, start_point_left, end_point_left, end_point_right, start_point_right, param_to_check=0):
    doc.Regenerate()
    if param_to_check < 0:

        point1 = start_point_left
        point2 = end_point_left
        point3 = end_point_right
        point4 = start_point_right

        line1 = Line.CreateBound(point1, point2)
        line2 = Line.CreateBound(point2, point4)
        line3 = Line.CreateBound(point4, point3)
        line4 = Line.CreateBound(point3, point1)

        profile.Append(line1)
        profile.Append(line2)
        profile.Append(line3)
        profile.Append(line4)

        return profile

    if param_to_check >= 0:
        point1 = start_point_left
        point2 = end_point_left
        point3 = end_point_right
        point4 = start_point_right

        line1 = Line.CreateBound(point1, point2)
        line2 = Line.CreateBound(point2, point3)
        line3 = Line.CreateBound(point3, point4)
        line4 = Line.CreateBound(point4, point1)

        profile.Append(line1)
        profile.Append(line2)
        profile.Append(line3)
        profile.Append(line4)

        return profile
    else:
        point1 = start_point_left
        point2 = end_point_left
        point3 = end_point_right
        point4 = start_point_right
        line1 = Line.CreateBound(point1, point2)
        line2 = Line.CreateBound(point2, point4)
        line3 = Line.CreateBound(point4, point3)
        line4 = Line.CreateBound(point3, point1)

        profile.Append(line1)
        profile.Append(line2)
        profile.Append(line3)
        profile.Append(line4)

        return profile


def create_point_param_less_0(count, profile, start_point_left, end_point_left, end_point_right, start_point_right, param_to_check=0):
    doc.Regenerate()
    point1 = start_point_left
    point2 = end_point_left
    point3 = end_point_right
    point4 = start_point_right

    line1 = Line.CreateBound(point1, point2)
    line2 = Line.CreateBound(point2, point4)
    line3 = Line.CreateBound(point4, point3)
    line4 = Line.CreateBound(point3, point1)

    profile.Append(line1)
    profile.Append(line2)
    profile.Append(line3)
    profile.Append(line4)

    return profile
def create_point_param_equal0(count, profile, start_point_left, end_point_left, end_point_right, start_point_right, param_to_check=0):
    doc.Regenerate()
    point1 = start_point_left
    point2 = end_point_left
    point3 = end_point_right
    point4 = start_point_right

    line1 = Line.CreateBound(point1, point2)
    line2 = Line.CreateBound(point2, point3)
    line3 = Line.CreateBound(point3, point4)
    line4 = Line.CreateBound(point4, point1)

    profile.Append(line1)
    profile.Append(line2)
    profile.Append(line3)
    profile.Append(line4)

    return profile

t = Transaction(doc, "plaster on runs")
t.Start()

floor_heights = []
floors_to_enable = []
floor_params = []
for el in stairs_collector:
    runs = el.GetStairsRuns()
    stairs_level_id = el.LookupParameter("Base Level").AsElementId()
    stairs_base_offset = el.LookupParameter("Base Offset").AsDouble() * 30.48

    count = 0
    for r in runs:
        # Create an empty curve loop to build the profile
        profile_ceiling = CurveLoop()
        profile = CurveLoop()

        runs_element, \
            runs_width, \
            r_depth, \
            r_height, \
            runs_actualNumberOfRises, \
            runs_actualNumberOfTreads, \
            run_base_height, \
            run_top_height = getting_parameters_for_runs(r)

        geometry = runs_element.get_Geometry(Options())
        # getting Footprint Boundaries to get all coordinates of X Y Z
        boundaries_of_run = runs_element.GetFootprintBoundary()
        # for each curve element in the boundaries run we are getting points, and adding it to the list
        biggest_face = None
        area_total = 0
        cat1Id = ElementId(BuiltInCategory.OST_GenericModel)
        for obj in geometry:
            if isinstance(obj, Solid):
                solid = obj
                faces = solid.Faces
                for face in faces:
                    area_of_face = face.Area
                    surface_area = face.Triangulate().ComputeSurfaceArea()
                    if area_of_face > area_total:
                        area_total = face.Area
                        biggest_face = face
        x_coordinates = []
        y_coordinates = []
        z_coordinates = []
        if biggest_face:
            curve_edges_loop = biggest_face.GetEdgesAsCurveLoops()
            # print(face_evaluate)
            # curve_edges_loop = biggest_face.GetSurface()
            normal = biggest_face.FaceNormal
            direction_vector = normal.Normalize()
            # Define a reference point
            # # working creating floor
            for curve_loop in curve_edges_loop:
                curve_iterator = curve_loop.GetCurveLoopIterator()
                for curve_iter in curve_iterator:
                    start = curve_iter.GetEndPoint(0)
                    end = curve_iter.GetEndPoint(1)
                    start = XYZ(start.X, start.Y, start.Z)
                    end = XYZ(end.X, end.Y, end.Z)
                    x1, y1, z1 = start.X, start.Y, start.Z
                    x2, y2, z2 = end.X, end.Y, end.Z
                    x_coordinates.extend([x1])
                    y_coordinates.extend([y1])
                    z_coordinates.extend([z1])

        # print("X Coordinates:", x_coordinates)
        # print("Y Coordinates:", y_coordinates)
        # print("Z Coordinates:", z_coordinates)

        if count == 0:
            param_to_check = runs_element.LookupParameter("Extend Below Riser Base").AsDouble()
            if param_to_check < 0:
                start_point_left = XYZ(x_coordinates[0], y_coordinates[0], 0)
                end_point_left = XYZ(x_coordinates[runs_actualNumberOfTreads], y_coordinates[runs_actualNumberOfTreads],0)
                start_point_right = XYZ(x_coordinates[runs_actualNumberOfTreads+1], y_coordinates[runs_actualNumberOfTreads+1], 0)
                end_point_right = XYZ(x_coordinates[-1],
                                      y_coordinates[-1], 0)
                print("Creating it if count == 0 and param < 0")
                create_point_param_less_0(count, profile, start_point_left, end_point_left, end_point_right, start_point_right, param_to_check=-20)

                check_left = XYZ(x_coordinates[runs_actualNumberOfTreads], y_coordinates[runs_actualNumberOfTreads],
                                 z_coordinates[runs_actualNumberOfTreads])
                # print(check_left)
                check_right = XYZ(x_coordinates[runs_actualNumberOfTreads + 1],
                                  y_coordinates[runs_actualNumberOfTreads + 1],
                                  z_coordinates[runs_actualNumberOfTreads] + 1)
                check_left_base = XYZ(x_coordinates[0], y_coordinates[0], z_coordinates[0])

                floor_params.append({'top_z': check_left,
                                     'bottom_z': check_left_base,
                                     'param': True})

            else:
                start_point_left = XYZ(x_coordinates[1], y_coordinates[1], 0)
                end_point_left = XYZ(x_coordinates[runs_actualNumberOfTreads], y_coordinates[runs_actualNumberOfTreads], 0)
                start_point_right = XYZ(x_coordinates[0], y_coordinates[0], 0)
                end_point_right = XYZ(x_coordinates[runs_actualNumberOfTreads + 1],
                                      y_coordinates[runs_actualNumberOfTreads + 1 ], 0)

                check_left = XYZ(x_coordinates[runs_actualNumberOfTreads], y_coordinates[runs_actualNumberOfTreads],
                                 z_coordinates[runs_actualNumberOfTreads])

                check_left_base = XYZ(x_coordinates[1], y_coordinates[1], z_coordinates[1])

                check_right = XYZ(x_coordinates[runs_actualNumberOfTreads + 1],
                                  y_coordinates[runs_actualNumberOfTreads + 1],
                                  z_coordinates[runs_actualNumberOfTreads] + 1)
                if check_left:
                    floor_params.append({'top_z': check_left,
                                         'bottom_z': check_left_base,
                                         'param': False})
                print("Creating it if count == 0 and param > 0")
                create_point_param_equal0(count, profile, start_point_left, end_point_left, end_point_right, start_point_right)

        elif count >= 1:

            try:
                start_point_left = XYZ(x_coordinates[0], y_coordinates[0], 0)
                end_point_left = XYZ(x_coordinates[runs_actualNumberOfTreads], y_coordinates[runs_actualNumberOfTreads],
                                     0)
                start_point_right = XYZ(x_coordinates[runs_actualNumberOfTreads + 1],
                                        y_coordinates[runs_actualNumberOfTreads + 1], 0)
                end_point_right = XYZ(x_coordinates[-1], y_coordinates[-1], 0)

                # line_test_1 = Line.CreateBound(start_point_left, end_point_left)
                # line_test_2 = Line.CreateBound(end_point_left, start_point_right)
                # line_test3 = Line.CreateBound(start_point_right, end_point_right)
                # line_test4 = Line.CreateBound(end_point_right, start_point_left)
                # line_element_id = doc.Create.NewModelCurve(line_test_1, SketchPlane.Create(doc,Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ(0, 0, 0))))
                # line_element_id = doc.Create.NewModelCurve(line_test_2, SketchPlane.Create(doc,Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ(0, 0, 0))))
                # line_element_id = doc.Create.NewModelCurve(line_test3, SketchPlane.Create(doc,Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ(0, 0, 0))))
                # line_element_id = doc.Create.NewModelCurve(line_test4, SketchPlane.Create(doc,Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ(0, 0, 0))))

                print("creating this if cound >= 1 ")
                create_point_param_less_0(count, profile, start_point_left, end_point_left, end_point_right, start_point_right,param_to_check=0)

                check_left = XYZ(x_coordinates[runs_actualNumberOfTreads], y_coordinates[runs_actualNumberOfTreads],
                                 z_coordinates[runs_actualNumberOfTreads])

                check_right = XYZ(x_coordinates[-1], y_coordinates[-1], z_coordinates[-1])
                check_left_base = XYZ(x_coordinates[0], y_coordinates[0], z_coordinates[0])
                if check_left:
                    floor_params.append({
                        'top_z': check_left,
                        'bottom_z': check_left_base,
                        'param': False
                    })

            except Exception as err:
                print(err)

        try:
            floor_ceiling = Floor.Create(doc, [profile], floor_type_id, stairs_level_id)
            floor_ceiling.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(0)
            floors_to_enable.append(floor_ceiling)
        except Exception as ex:
            print(ex)
        count += 1


try:
    doc.Regenerate()
    # print(floor_params)

    for i, floor in enumerate(floors_to_enable):
        slabeditor = floor.SlabShapeEditor
        # Get the slab's vertex array
        vertexArray = slabeditor.SlabShapeVertices
        slabeditor.Enable()
        doc.Regenerate()
        creasesArray = floor.SlabShapeEditor.SlabShapeCreases
        #floor elevation
        floor_id = floor.LevelId
        elevation = doc.GetElement(floor_id).Elevation


        if i < len(floor_params):
            floor_param = floor_params[i] # accses parameters for the current floor
            top_z = floor_param.get('top_z', None)
            bottom_z = floor_param.get('bottom_z', None)
            param_value = floor_param.get('param', None)
            # print(top_z, bottom_z, param_value)
            if top_z is not None:
                slabeditor.ModifySubElement(creasesArray[3], top_z.Z - elevation)
            if param_value is True:
                if bottom_z is not None:
                    slabeditor.ModifySubElement(creasesArray[0], bottom_z.Z - elevation)
            else:
                if bottom_z is not None:
                    # Adjust the Z coordinate for the base
                    slabeditor.ModifySubElement(creasesArray[0], bottom_z.Z - elevation)


        doc.Regenerate()


except Exception as ex:
    print(ex)

t.Commit()
