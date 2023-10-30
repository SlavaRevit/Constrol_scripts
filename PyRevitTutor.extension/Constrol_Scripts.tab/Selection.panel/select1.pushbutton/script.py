# Boilerplate text
import clr
from pyrevit import revit, DB, forms

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference("RevitNodes")

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI import Selection
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.UI import TaskDialog, TaskDialogResult, TextBox, RibbonItem, RibbonPanel

# Current doc/app/ui
doc = revit.doc
uidoc = revit.uidoc


t = Transaction(doc, "Selecting walls")

t.Start()

# Do some action in a Transaction
picked_elements = uidoc.Selection.PickObjects(ObjectType.Element, "Select elements")

element_ids = [el.ElementId for el in picked_elements]
selected_elements = [doc.GetElement(id) for id in element_ids]

t.Commit()
list_of_dtm = []
# dialog = TaskDialog("Enter a value")
# result = dialog.Show()

user_input = forms.ask_for_string()

def geting_param():
    total_result_vol = 0
    for el in selected_elements:
        el_id = el.GetTypeId()
        type_elem = doc.GetElement(el_id)
        dtm = type_elem.LookupParameter("Duplication Type Mark").AsString()
        list_of_dtm.append(dtm)
        if isinstance(el, FamilyInstance):
            if dtm in list_of_dtm and dtm == user_input:
                vol_param = el.LookupParameter("Volume").AsDouble() * 0.02831685
                total_result_vol += vol_param
        else:
            if dtm in list_of_dtm and dtm == user_input:
                vol_param = el.LookupParameter("Volume").AsDouble() * 0.02831685
                total_result_vol += vol_param



    return "Total Volume: {}".format(total_result_vol)


a = geting_param()
print(a)
