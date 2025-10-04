import FreeCAD, FreeCADGui
from PySide import QtGui

class HelloWorldCommand:
    def GetResources(self):
        return {"MenuText": "Say Hello", "ToolTip": "Show a greeting"}
    def Activated(self):
        QtGui.QMessageBox.information(None, "FreeCAD Addon", "Привет, мир!\nТы только что запустил свой первый аддон!")
    def IsActive(self):
        return True

class HelloWorldWorkbench(FreeCADGui.Workbench):
    MenuText = "Hello World"
    def Initialize(self):
        self.appendToolbar("Hello Tools", ["HelloWorldCommand"])
        self.appendMenu("Hello World", ["HelloWorldCommand"])
    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addCommand("HelloWorldCommand", HelloWorldCommand())