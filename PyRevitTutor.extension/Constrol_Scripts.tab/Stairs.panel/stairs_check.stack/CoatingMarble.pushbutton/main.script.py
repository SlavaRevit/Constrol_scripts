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
from pyrevit.forms import WPFWindow



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


def create_steps_floor(doc,x_cor, y_cor, run_base_height, r_depth, r_height,
                       floor_thickness, steps_number, start_left_point, end_left_point, start_right_point,
                       end_right_point, direction_vector, current_left_start, current_right_start,desired_left_point,
                       desired_right_point,stairs_level_id,base_offset,floor_type_id):

    profile = CurveLoop()

    current_left_start = desired_left_point
    current_right_start = desired_right_point
    desired_left_point = current_left_start + direction_vector * r_depth
    desired_right_point = current_right_start + direction_vector * r_depth


    point1 = current_left_start
    point2 = desired_left_point
    point3 = desired_right_point
    point4 = current_right_start


    line1 = Line.CreateBound(point1, point2)
    line2 = Line.CreateBound(point2, point3)
    line3 = Line.CreateBound(point3, point4)
    line4 = Line.CreateBound(point4, point1)

    profile.Append(line1)
    profile.Append(line2)
    profile.Append(line3)
    profile.Append(line4)

    floor = Floor.Create(doc, [profile], floor_type_id, stairs_level_id)
    floor_thickness = floor.LookupParameter("Thickness").AsDouble()
    floor.get_Parameter(BuiltInParameter.LEVEL_PARAM).Set(stairs_level_id)
    floor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(
        run_base_height + (r_height + (r_height * steps_number)) + floor_thickness + base_offset)

    return current_left_start,current_right_start, desired_left_point,desired_right_point

floors_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType().ToElements()

floor_types = []
for floor in floors_collector:
    floor_name = floor.Name
    if floor_name not in floor_types:
        floor_types.append(floor_name)
    else:
        pass

res = forms.SelectFromList.show(floor_types, button_name="Select item")

for floor in floors_collector:
    if floor.Name == res:
        floor_id = floor.GetTypeId()
        floor_type = doc.GetElement(floor_id)
        floor_type_id = floor_type.Id



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

for el in stairs_collector:
    runs = el.GetStairsRuns()
    stairs_level_id = el.LookupParameter("Base Level").AsElementId()
    stairs_base_offset = el.LookupParameter("Base Offset").AsDouble()


    for r in runs:
        # Create an empty curve loop to build the profile
        profile = CurveLoop()
        profile_ceiling = CurveLoop()

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
        #getting Footprint Boundaries to get all coordinates of X Y Z
        boundaries_of_run = runs_element.GetFootprintBoundary()
        # for each curve element in the boundaries run we are getting points, and adding it to the list
        for curve in boundaries_of_run:
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

        # coordinates to start with
        start_left_point = XYZ(x_cor[1], y_cor[1], z_cor[1])
        # end point need to make direction vector, to save angle of the stair and floor
        end_left_point = XYZ(x_cor[0], y_cor[0], z_cor[0])
        # the same situation for the right point
        start_right_point = XYZ(x_cor[2], y_cor[2], z_cor[2])
        end_right_point = XYZ(x_cor[3], y_cor[3], z_cor[3])

        # saving this points to variable, to work better with it
        current_left_start = XYZ(x_cor[1], y_cor[1], 0)
        current_right_start = XYZ(x_cor[2], y_cor[2], 0)
        # direction_vector to save angle
        direction_vector = (end_left_point - start_left_point).Normalize()

        # Finding desired point according to the start of the X Y Z coordinates
        desired_left_point = current_left_start + direction_vector * r_depth
        desired_right_point = current_right_start + direction_vector * r_depth

        #creating first point to start from it
        def create_point():
            point1 = current_left_start
            point2 = desired_left_point
            point3 = desired_right_point
            point4 = current_right_start

            line1 = Line.CreateBound(point1, point2)
            line2 = Line.CreateBound(point2, point3)
            line3 = Line.CreateBound(point3, point4)
            line4 = Line.CreateBound(point4, point1)

            profile.Append(line1)
            profile.Append(line2)
            profile.Append(line3)
            profile.Append(line4)
        create_point()

        # creating floor according to the profile created from points
        floor = Floor.Create(doc, [profile], floor_type_id, stairs_level_id)
        floor_thickness = floor.LookupParameter("Thickness").AsDouble()
        floor.get_Parameter(BuiltInParameter.LEVEL_PARAM).Set(stairs_level_id)  # Set the level (adjust as needed)
        floor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(
            run_base_height + r_height + floor_thickness+ stairs_base_offset)



        # going through number all runs actual number of treads, to make floor for each step
        for steps_number in range(1, runs_actualNumberOfTreads):
            create_steps_floor(doc,x_cor, y_cor, run_base_height, r_depth, r_height,
                               floor_thickness, steps_number,
                               start_left_point, end_left_point, start_right_point, end_right_point, direction_vector,
                               current_left_start, current_right_start, desired_left_point, desired_right_point,stairs_level_id,stairs_base_offset,floor_type_id)

            # changing current start position to the desired, to start the next floor from it
            current_left_start = desired_left_point
            current_right_start = desired_right_point
            desired_left_point = current_left_start + direction_vector * r_depth
            desired_right_point = current_right_start + direction_vector * r_depth

t.Commit()
# -------------------------------------------------------------------
print('-' * 50)
print("Script is finished")
