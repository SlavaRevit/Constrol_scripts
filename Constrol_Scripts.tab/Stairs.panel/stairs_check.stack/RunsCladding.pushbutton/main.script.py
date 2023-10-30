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
from pyrevit.forms import ProgressBar

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

stair_runs = FilteredElementCollector(doc). \
    OfCategory(BuiltInCategory.OST_StairsRuns). \
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



base_point = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ProjectBasePoint).ToElements()
elev_base_point = base_point[0].LookupParameter("Elev").AsDouble()

levels = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Levels).WhereElementIsNotElementType().ToElements()
def get_Level0(levels):
    for level in levels:
        if "Level 0" in level.Name:
            level_elev = level.LookupParameter("Elevation").AsDouble()
            return level_elev


FloorTypes = FilteredElementCollector(doc).OfCategory(
    BuiltInCategory.OST_Floors).WhereElementIsElementType().ToElements()

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


def sort_key(vertex):
    return vertex.Position.X, vertex.Position.Y, vertex.Position.Z

def sort_key_reverse(vertex):
    return vertex.Position.X, -vertex.Position.Y, vertex.Position.Z

def sort_item(item):
    return item[0], item[1], item[2]

def sort_item_reverse(item):
    return item[0], -item[1], item[2]



t = Transaction(doc, "plaster on runs")
t.Start()



for el in stairs_collector:
    floors_to_enable = []
    coordinates_end = []

    floor_heights = []
    floor_params = []
    runs = el.GetStairsRuns()
    stairs_level_id = el.LookupParameter("Base Level").AsElementId()
    stairs_base_offset = el.LookupParameter("Base Offset").AsDouble() * 30.48
    count = 0
    run_coordinates_start = []
    for r in runs:

        profile_ceiling = CurveLoop()
        profile = CurveLoop()
        # Create an empty curve loop to build the profile
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
        # param_to_check = runs_element.LookupParameter("Extend Below Riser Base").AsDouble()
        face = None
        coord_check_start = []
        modified_loop_check = CurveLoop()
        for c in boundaries_of_run:
            start = c.GetEndPoint(0)
            end = c.GetEndPoint(1)
            start = XYZ(start.X , start.Y, start.Z)
            end = XYZ(end.X, end.Y, end.Z)
            modified_start_point = XYZ(start.X, start.Y, 0)
            modified_end_point = XYZ(end.X, end.Y, 0)

            coord_check_start.append((start.X, start.Y, start.Z))
            coord_check_start.append((end.X, end.Y, end.Z))
            try:
                modified_curve_check = Line.CreateBound(modified_start_point, modified_end_point)
                # line_element_id = doc.Create.NewModelCurve(modified_curve_check, SketchPlane.Create(doc,
                #                                                                               Plane.CreateByNormalAndOrigin(
                #                                                                                   XYZ.BasisZ,
                #                                                                                   XYZ(0, 0, 0))))
            except Exception as err:
                print(err)
            modified_loop_check.Append(modified_curve_check)


        for obj in geometry:
            if isinstance(obj, Solid):
                solid = obj
                faces = solid.Faces
                for face in faces:
                    area_of_face = face.Area
                    # surface_area = face.Triangulate().ComputeSurfaceArea()
                    if area_of_face > area_total:
                        area_total = face.Area
                        biggest_face = face
        modified_curves = []
        coordinates_start = []

        try:
            if biggest_face:
                curve_edges_loop = biggest_face.GetEdgesAsCurveLoops()
                normal = biggest_face.FaceNormal
                direction_vector = normal.Normalize()
                edgeArray = face.EdgeLoops

                points = []
                for curve_loop in curve_edges_loop:
                    
                    curve_loop.Flip()
                    curve_iterator = curve_loop.GetCurveLoopIterator()
                    modified_loop = CurveLoop()

                    for curve_iter in curve_iterator:
                        length_curve = curve_iter.Length
                        if length_curve < 2:
                            pass
                        else:
                            start = curve_iter.GetEndPoint(0)
                            end = curve_iter.GetEndPoint(1)
                            start = XYZ(start.X, start.Y, start.Z)
                            end = XYZ(end.X, end.Y, end.Z)

                            # Modify the Z-coordinate to be 0
                            modified_start_point = XYZ(start.X, start.Y, 0)
                            modified_end_point = XYZ(end.X, end.Y, 0)
                        
                            # coordinates_start.append((start.X, start.Y, start.Z))
                            # coordinates_end.append((end.X, end.Y, end.Z))
                            points.append([modified_start_point,modified_end_point])
                            coordinates_start.append([start.X, start.Y, start.Z])
                            coordinates_start.append([end.X, end.Y, end.Z])
                try:
                    modified_curve = Line.CreateBound(points[0][0], points[0][1])
                    # line_element_id = doc.Create.NewModelCurve(modified_curve, SketchPlane.Create(doc,Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ(0, 0, 0))))
                    modified_curve2 = Line.CreateBound(points[0][1], points[1][0])
                    # line_element_id = doc.Create.NewModelCurve(modified_curve2, SketchPlane.Create(doc,Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ(0, 0, 0))))
                    modified_curve3 = Line.CreateBound(points[1][0], points[1][1])
                    # line_element_id = doc.Create.NewModelCurve(modified_curve3, SketchPlane.Create(doc,Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ(0, 0, 0))))
                    modified_curve4 = Line.CreateBound(points[1][1], points[0][0])
                    # line_element_id = doc.Create.NewModelCurve(modified_curve4, SketchPlane.Create(doc,Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ(0, 0, 0))))
                    modified_loop.Append(modified_curve)
                    modified_loop.Append(modified_curve2)
                    modified_loop.Append(modified_curve3)
                    modified_loop.Append(modified_curve4)
                
                except Exception as err:
                    # print(err)
                    pass
                
                modified_curves.append(modified_loop)

        except Exception as err:
            # print(err)
            pass

    
        
        
        try:
            floor_ceiling = Floor.Create(doc, modified_curves, floor_type_id, stairs_level_id)
            floor_ceiling.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(0)
            floors_to_enable.append(floor_ceiling)
            doc.Regenerate()
        except Exception as err:
            pass
            
            

        try:
            new_list = [(item[0], item[1], item[2]) for item in coordinates_start]
            new_sorted_list = sorted(new_list, key=sort_item)
        except Exception as err:
            pass


        try:
            # for floor in floors_to_enable:
            doc.Regenerate()
            slabeditor = floor_ceiling.SlabShapeEditor
            slabeditor.Enable()
            doc.Regenerate()
            creasesArray = slabeditor.SlabShapeCreases
            vertexArray = slabeditor.SlabShapeVertices
            sorted_vertex_array = sorted(vertexArray, key=sort_key)
            # sorted_creases_array = sorted(creasesArray, key=sort_key)
            # print(len(sorted_vertex_array))
            floor_id = floor_ceiling.LevelId
            elevation = doc.GetElement(floor_id).Elevation
            
            # print(round(sorted_vertex_array[0].Position.X,5))
            # print(round(new_sorted_list[0][0],5))
            # print(abs(sorted_vertex_array[0].Position.Y))
            # print(abs(new_sorted_list[0][1]))

            """reverse vertex array"""
            if round(sorted_vertex_array[0].Position.X, 5) == round(new_sorted_list[0][0],5) and round(abs(sorted_vertex_array[0].Position.Y),5) == round(abs(new_sorted_list[0][1]),5):
                # print("Changing it from here")
                sorted_vertex_array = sorted(vertexArray, key=sort_key)
                new_sorted_list = sorted(new_list, key=sort_item)
            elif round(sorted_vertex_array[0].Position.X, 5) == round(new_sorted_list[0][0],5) and round(abs(sorted_vertex_array[0].Position.Y),5) > round(abs(new_sorted_list[0][1]),5):
                # print("position Y > my Y")
                sorted_vertex_array = sorted(vertexArray, key=sort_key_reverse)
                new_sorted_list = sorted(new_list, key=sort_item_reverse)
            elif round(sorted_vertex_array[0].Position.X, 5) == round(new_sorted_list[0][0],5) and round(abs(sorted_vertex_array[0].Position.Y),5) < round(abs(new_sorted_list[0][1]),5):
                # print("position Y < my Y")
                sorted_vertex_array = sorted(vertexArray, key=sort_key_reverse)
                # new_sorted_list = sorted(new_list, key=sort_item_reverse)
                # sorted_vertex_array = sorted(vertexArray, key=sort_key_reverse)
                # new_sorted_list = sorted(new_list, key=sort_item)

            # else:
            #     sorted_vertex_array = sorted(vertexArray, key=sort_key)
            #     new_sorted_list = sorted(new_list, key=sort_item)

            doc.Regenerate()
            level_0_elevation = get_Level0(levels)

            for i, vertex in enumerate(sorted_vertex_array):
                x, y, z = vertex.Position.X, vertex.Position.Y, vertex.Position.Z
                x_new, y_new, z_new = new_sorted_list[i]

                slabeditor.ModifySubElement(vertex, z_new - z)
            # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            # print("End of floor HERE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        
            doc.Regenerate()
        
        
        except Exception as ex:
            pass

#Finished script msg.       
max_value = 100
with ProgressBar() as pb:
    for counter in range(0, max_value):
        pb.update_progress(counter, max_value)  
forms.alert("Script finished.")


t.Commit()
