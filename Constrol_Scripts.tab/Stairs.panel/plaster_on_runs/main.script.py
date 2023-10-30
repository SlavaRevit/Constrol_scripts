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

#
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


def sort_item(item):
    return item[1], item[0], item[2]


t = Transaction(doc, "plaster on runs")
t.Start()

floor_heights = []
floors_to_enable = []
floor_params = []
doc.Regenerate()
for el in stairs_collector:
    runs = el.GetStairsRuns()
    stairs_level_id = el.LookupParameter("Base Level").AsElementId()
    stairs_base_offset = el.LookupParameter("Base Offset").AsDouble() * 30.48
    doc.Regenerate()
    for r in runs:
        # Create an empty curve loop to build the profile
        profile_ceiling = CurveLoop()

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
        coordinates_start = []
        modified_loop = CurveLoop()
        for c in boundaries_of_run:
            start = c.GetEndPoint(0)
            end = c.GetEndPoint(1)
            start = XYZ(start.X, start.Y, start.Z)
            end = XYZ(end.X, end.Y, end.Z)
            modified_start_point = XYZ(start.X, start.Y, 0)
            modified_end_point = XYZ(end.X, end.Y, 0)

            coordinates_start.append((start.X, start.Y, start.Z))
            try:
                modified_curve = Line.CreateBound(modified_start_point, modified_end_point)
                line_element_id = doc.Create.NewModelCurve(modified_curve, SketchPlane.Create(doc,
                                                                                              Plane.CreateByNormalAndOrigin(
                                                                                                  XYZ.BasisZ,
                                                                                                  XYZ(0, 0, 0))))
            except Exception as err:
                print(err)
            modified_loop.Append(modified_curve)

        print("END OF THE RUN")

        # Creating floors
        try:
            floor_ceiling = Floor.Create(doc, [modified_loop], floor_type_id, stairs_level_id)
            floor_ceiling.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(0)
            floors_to_enable.append(floor_ceiling)
        except Exception as ex:
            print(ex)

        try:
            new_list = [(round(item[0], 10), item[1], item[2]) for item in coordinates_start]
            new_sorted_list = sorted(new_list, key=sort_item)
        except Exception as err:
            print(err)

        try:
            # for floor in floors_to_enable:
            doc.Regenerate()
            slabeditor = floor_ceiling.SlabShapeEditor
            slabeditor.Enable()

            doc.Regenerate()
            creasesArray = slabeditor.SlabShapeCreases
            vertexArray = slabeditor.SlabShapeVertices

            sorted_vertex_array = sorted(vertexArray, key=sort_key)
            # print(len(sorted_vertex_array))
            floor_id = floor_ceiling.LevelId
            elevation = doc.GetElement(floor_id).Elevation

            doc.Regenerate()
            # level_0_elevation = get_Level0(levels)
            for i, vertex in enumerate(sorted_vertex_array):
                x, y, z = vertex.Position.X, vertex.Position.Y, vertex.Position.Z
                x_new, y_new, z_new = new_sorted_list[i]
                print(x, y, z, ":::::::::", x_new, y_new, z_new)

                slabeditor.ModifySubElement(vertex, z_new - elevation)
            # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            # print("End of floor HERE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

            doc.Regenerate()


        except Exception as ex:
            print(ex)

t.Commit()
