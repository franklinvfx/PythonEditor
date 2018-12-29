import sys
import os

PYTHON_EDITOR_MODULES = []

class Finder(object):
    """
    Keep track of pythoneditor modules loaded
    so that they can be reloaded in the same order.
    """
    _can_delete = True
    def find_module(self, name, path=''):
        if 'PythonEditor' not in name:
            return

        global PYTHON_EDITOR_MODULES
        if name in PYTHON_EDITOR_MODULES:
            return
        if path is None:
            return

        filename = name.split('.').pop()+'.py'
        for p in path:
            if filename in os.listdir(p):
                PYTHON_EDITOR_MODULES.append(name)
                return


sys.meta_path = [i for i in sys.meta_path
                 if not hasattr(i, '_can_delete')]
sys.meta_path.append(Finder())


import imp
from PythonEditor.ui.Qt import QtWidgets, QtCore
from PythonEditor.ui import pythoneditor


class IDE(QtWidgets.QWidget):
    """
    Container widget that allows the whole
    package to be reloaded.
    """
    def __init__(self, parent=None):
        super(IDE, self).__init__(parent)
        self.setLayout(QtWidgets.QHBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setObjectName('IDE')
        self.setWindowTitle('Python Editor')
        self.buildUI()

    def buildUI(self):
        print('building UI')
        self.python_editor = pythoneditor.PythonEditor(parent=self)
        self.layout().addWidget(self.python_editor)

    def reload_package(self):
        """
        Reloads the whole package (except for this module),
        in an order that does not cause errors.
        """
        self.python_editor.terminal.stop()
        self.python_editor.deleteLater()
        del self.python_editor

        # not_reloadable = [
        #     # 'PythonEditor.ui.terminal', # reload later
        #     # 'PythonEditor.core.streams', # reload later
        #     'PythonEditor.ui.pythoneditor', # reload later
        #     'PythonEditor.ui.ide',
        #     '__main__'
        #  ]

        # reload modules the order they were loaded in
        for name in PYTHON_EDITOR_MODULES:
            mod = sys.modules.get(name)
            if mod is None:
                continue
            imp.reload(mod)

        # loaded_modules = sys.modules
        # for name, mod in loaded_modules.items():
        #     if (mod and hasattr(mod, '__file__')
        #             and 'PythonEditor' in mod.__file__
        #             and name not in not_reloadable):
        #         # print(name, mod)
                # imp.reload(mod)

        # imp.reload(pythoneditor)
        QtCore.QTimer.singleShot(1, self.buildUI)

    def showEvent(self, event):
        """
        Hack to get rid of margins automatically put in
        place by Nuke Dock Window.
        """
        try:
            parent = self.parent()
            for x in range(6):
                parent.layout().setContentsMargins(0, 0, 0, 0)
                parent = parent.parent()
        except AttributeError:
            pass

        super(IDE, self).showEvent(event)
