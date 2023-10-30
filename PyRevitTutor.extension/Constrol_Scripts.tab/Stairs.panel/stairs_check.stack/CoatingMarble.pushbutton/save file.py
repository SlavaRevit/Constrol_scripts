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
from System.Collections.Generic import List

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
doc = __revit__.ActiveUIDocument.Document  # type: Document
uidoc = __revit__.ActiveUIDocument  # type: UIDocument
app = __revit__.Application  # type: Application


def getting_parameters_of_element(el):
    # getting all parameters needed for stairs
    coatingMarble_param = el.LookupParameter("CoatingMarble")
    LineForBlindPeople_param = el.LookupParameter("LineForBlindPeople")
    PanelStairs_param = el.LookupParameter("PanelStairs")
    actualNumberOfRises = el.LookupParameter("Actual Number of Risers").AsInteger()
    Volume_param = el.LookupParameter("Volume")

    return actualNumberOfRises, Volume_param


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


def create_steps_floor(point1, point2, point3, point4, x_cor, y_cor, run_base_height, r_depth, r_height,
                       floor_thickness, steps_number, start_left_point, end_left_point):
    profile = CurveLoop()
    point1 = XYZ(x_cor[1], y_cor[1] + (steps_number * r_depth), 0)

    point2 = XYZ(x_cor[1], y_cor[1] + r_depth + (steps_number * r_depth), 0)

    point3 = XYZ(x_cor[1] + runs_width, y_cor[1] + r_depth + (steps_number * r_depth), 0)

    point4 = XYZ(x_cor[1] + runs_width, y_cor[1] + (steps_number * r_depth), 0)

    line1 = Line.CreateBound(point1, point2)
    line2 = Line.CreateBound(point2, point3)
    line3 = Line.CreateBound(point3, point4)
    line4 = Line.CreateBound(point4, point1)

    profile.Append(line1)
    profile.Append(line2)
    profile.Append(line3)
    profile.Append(line4)

    floor = Floor.Create(doc, [profile], ElementId(213369), ElementId(13071))
    floor_thickness = floor.LookupParameter("Thickness").AsDouble()
    floor.get_Parameter(BuiltInParameter.LEVEL_PARAM).Set(ElementId(13071))
    floor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(
        run_base_height + (r_height + (r_height * steps_number)) + floor_thickness)


stairs_collector = FilteredElementCollector(doc). \
    OfCategory(BuiltInCategory.OST_Stairs). \
    WhereElementIsNotElementType(). \
    ToElements()
runs_collector = FilteredElementCollector(doc). \
    OfCategory(BuiltInCategory.OST_StairsRuns). \
    WhereElementIsNotElementType(). \
    ToElements()
t = Transaction(doc, "Add Cladding to Stair Treads")
t.Start()
treads = []
for el in stairs_collector:
    runs = el.GetStairsRuns()

    # profile = CurveLoop()
    for r in runs:
        # Create an empty curve loop to build the profile
        profile = CurveLoop()
        runs_element, \
            runs_width, \
            r_depth, \
            r_height, \
            runs_actualNumberOfRises, \
            runs_actualNumberOfTreads, \
            run_base_height, \
            run_top_height = getting_parameters_for_runs(r)
        x_coordinates = []
        y_coordinates = []
        z_coordinates = []
        x = runs_element.GetFootprintBoundary()
        for curve in x:
            start_point = curve.GetEndPoint(0)
            end_point = curve.GetEndPoint(1)
            x1, y1, z1 = start_point.X, start_point.Y, start_point.Z
            x2, y2, z2 = end_point.X, end_point.Y, end_point.Z
            x_coordinates.extend([x1])
            y_coordinates.extend([y1])
            z_coordinates.extend([z1])

        x_cor = x_coordinates[:]
        y_cor = y_coordinates[:]
        z_cor = z_coordinates[:]
        # print("Printing X coordinates: ", x_cor)
        # print("Printing Y coordinates: ", y_cor)
        # print("Printing Z coordinates: ", z_cor)
        start_left_point = XYZ(x_cor[1], y_cor[1], z_cor[1])
        end_left_point = XYZ(x_cor[0], y_cor[0], z_cor[0])

        start_right_point = XYZ(x_cor[2], y_cor[2], z_cor[2])
        end_right_point = XYZ(x_cor[3], y_cor[3], z_cor[3])

        direction_vector = (end_left_point - start_left_point).Normalize()
        direction_vector_right = (end_right_point - start_right_point).Normalize()

        desired_point = start_left_point + direction_vector * r_depth
        desired_right_point = start_right_point + direction_vector_right * r_depth


        point1 = XYZ(x_cor[1], y_cor[1], 0)  # z = relative base height, x1 = 0, y1 = 0

        point2 = desired_point

        point3 = desired_right_point

        point4 = XYZ(x_cor[2], y_cor[2], 0)

        line1 = Line.CreateBound(XYZ(x_cor[0], y_cor[0], z_cor[0]), XYZ(x_cor[1], y_cor[1], z_cor[1]))
        line2 = Line.CreateBound(XYZ(x_cor[1], y_cor[1], z_cor[1]), XYZ(x_cor[2], y_cor[2], z_cor[2]))
        line3 = Line.CreateBound(XYZ(x_cor[2], y_cor[2], z_cor[2]), XYZ(x_cor[3], y_cor[3], z_cor[3]))
        line4 = Line.CreateBound(XYZ(x_cor[3], y_cor[3], z_cor[3]), XYZ(x_cor[0], y_cor[0], z_cor[0]))

        # this is ok for the straight line, not for stairs with the angle
        line_test_1 = Line.CreateBound(point1, point2)
        line_element_id = doc.Create.NewModelCurve(line_test_1, SketchPlane.Create(doc, Plane.CreateByNormalAndOrigin(
            XYZ.BasisZ, XYZ(0, 0, 0))))
        # this is also works ok only for points where we don't have the angle
        line_test_2 = Line.CreateBound(point3, point4)
        line_element_id_2 = doc.Create.NewModelCurve(line_test_2, SketchPlane.Create(doc, Plane.CreateByNormalAndOrigin(
            XYZ.BasisZ, XYZ(0, 0, 0))))

        line1 = Line.CreateBound(point1, point2)
        line2 = Line.CreateBound(point2, point3)
        line3 = Line.CreateBound(point3, point4)
        line4 = Line.CreateBound(point4, point1)

        profile.Append(line1)
        profile.Append(line2)
        profile.Append(line3)
        profile.Append(line4)
        #
        floor = Floor.Create(doc, [profile], ElementId(213369), ElementId(13071))
        floor_thickness = floor.LookupParameter("Thickness").AsDouble()
        floor.get_Parameter(BuiltInParameter.LEVEL_PARAM).Set(ElementId(13071))  # Set the level (adjust as needed)
        floor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(
            run_base_height + r_height + floor_thickness)

        # for steps_number in range(1, runs_actualNumberOfTreads):
        #     create_steps_floor(point1, point2, point3, point4,x_cor,y_cor,run_base_height,r_depth,r_height,floor_thickness, steps_number)

t.Commit()
# -------------------------------------------------------------------
print('-' * 50)
print("Script is finished")
