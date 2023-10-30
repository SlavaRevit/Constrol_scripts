from Autodesk.Revit.DB import *
import clr

clr.AddReference("RevitNodes")
import Revit

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
import Autodesk
from Autodesk.Revit.DB import *

doc = __revit__.ActiveUIDocument.Document

stairs_collector = FilteredElementCollector(doc). \
    OfCategory(BuiltInCategory.OST_Stairs). \
    WhereElementIsNotElementType(). \
    ToElements()
runs_collector = FilteredElementCollector(doc). \
    OfCategory(BuiltInCategory.OST_StairsRuns). \
    WhereElementIsNotElementType(). \
    ToElements()
railings = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StairsRailing). \
    WhereElementIsNotElementType().ToElements()


def isRailingAssociatedWithRunCheck(railing_elements, runs_element):
    # Get the bounding box of the run
    run_bb = runs_element.get_BoundingBox(None)
    run_min = run_bb.Min
    run_max = run_bb.Max

    list_railings = []
    for railing_element in railing_elements:
        if "Int" in railing_element.Name:
            continue
        # Get the bounding box of the railing
        railing_bb = railing_element.get_BoundingBox(None)
        railing_min = railing_bb.Min
        railing_max = railing_bb.Max

        # Check if the outlines intersect by comparing the min and max points
        if railing_element.HostId == runs_element.GetStairs().Id and railing_element.Id not in list_railings:
            if (railing_min.X <= run_max.X and railing_max.X > run_min.X and
                    railing_min.Y <= run_max.Y and railing_max.Y > run_min.Y and
                    railing_min.Z <= run_max.Z and railing_max.Z > run_min.Z):
                list_railings.append(railing_element.Id)

    return list_railings


transaction = Transaction(doc, 'Set coating marble values')
transaction.Start()
runs_count = 0

for el in stairs_collector:
    runs = el.GetStairsRuns()
    # getting parameters from stairs
    coatingMarble_param = el.LookupParameter("CoatingMarble")
    LineForBlindPeople_param = el.LookupParameter("LineForBlindPeople")
    PanelStairs_param = el.LookupParameter("PanelStairs")
    actualNumberOfRises = el.LookupParameter("Actual Number of Risers").AsInteger()
    Volume_param = el.LookupParameter("Volume")

    material_ids = el.GetMaterialIds(False)
    total_volume = 0
    for mat_id in material_ids:
        volume_stairs = el.GetMaterialVolume(mat_id)
        total_volume += volume_stairs

    # initial variables
    coatingMarbleResult = 0.0
    blindLineLength = 0
    r_depth = 0
    r_height = 0
    lengthPanel = 0

    for r in runs:
        runs_element = doc.GetElement(r)
        # getting run_width
        runs_width = runs_element.ActualRunWidth * 0.3048
        # params of rises and treads
        runs_actualNumberOfRises = runs_element.LookupParameter("Actual Number of Risers").AsInteger()
        runs_actualNumberOfTreads = runs_element.LookupParameter("Actual Number of Treads").AsInteger()
        # marble for run
        coatingMarbleResult += (runs_width * runs_actualNumberOfTreads)
        # getting run params
        r_depth = runs_element.LookupParameter("Actual Tread Depth").AsDouble() * 0.3048
        r_height = runs_element.LookupParameter("Actual Riser Height").AsDouble() * 0.3048
        # blind line for run
        blindLineLength += (runs_width * 2)
        associated_railings = isRailingAssociatedWithRunCheck(railings, runs_element)
        associated_railings = associated_railings[-2:]

        for railing in associated_railings:
            if railing is not None:
                railing_element = doc.GetElement(railing)
                if "on Wall" in railing_element.Name:
                    lengthPanel += (r_depth * runs_actualNumberOfTreads) + (r_height * runs_actualNumberOfRises)

    coatingMarble_param.Set(coatingMarbleResult / 0.3048)
    PanelStairs_param.Set(lengthPanel / 0.3048)
    LineForBlindPeople_param.Set(blindLineLength / 0.3048)
    Volume_param.Set(total_volume)

transaction.Commit()
