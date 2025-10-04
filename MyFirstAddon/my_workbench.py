import FreeCAD, FreeCADGui
from PySide import QtGui

class TestCommand:
    def GetResources(self):
        return {
            "MenuText": "Test Command",
            "ToolTip": "Показать сообщение"
        }
    def Activated(self):
        QtGui.QMessageBox.information(None, "Аддон", "Работает!")
    def IsActive(self):
        return True

class MyWorkbench(FreeCADGui.Workbench):
    MenuText = "MyFirstAddon"
    ToolTip = "Мой первый аддон"

    def Initialize(self):
        self.list = ["TestCommand"]
        self.appendToolbar("My Tools", self.list)
        self.appendMenu("MyFirstAddon", self.list)

    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addCommand("TestCommand", TestCommand())