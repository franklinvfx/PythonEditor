from PythonEditor.ui.nukefeatures import nukedock
from PythonEditor.utils import constants
from PythonEditor.utils.Qt import QtWidgets, QtCore

PANEL_NAME = 'i.d.e.Python_Editor'

RELOAD_CMD = """
for m in sys.modules.keys():
    if 'PythonEditor' in m:
        del sys.modules[m]
import PythonEditor
reload(PythonEditor)
from PythonEditor.ui.nukefeatures import nukedock
reload(nukedock)
nukedock.setup_dock()
nukescripts.panels.__panels["i.d.e.Python_Editor"]()
"""

ICON_PATH = constants.NUKE_DIR + '/icons/PythonEditor.png'


def menu_setup():
    import nuke

    panelMenu = nuke.menu('Nuke').addMenu('Panels')
    panelMenu.addCommand('Python Editor',
                         RELOAD_CMD,
                         icon=ICON_PATH)

    import_cmd = '__import__("PythonEditor")'\
        '.ui.nukefeatures.nukeinit.add_to_pane()'
    nuke.menu('Nodes').addCommand('Python Editor',
                                  import_cmd,
                                  '\\',
                                  icon=ICON_PATH)


def add_to_pane():
    """
    Locates a panel and adds it to one
    of the main dock windows in order
    of preference.
    """
    panel = None
    for widget in QtWidgets.QApplication.instance().allWidgets():
        if isinstance(widget, QtWidgets.QStackedWidget):
            for child in widget.children():
                if child.objectName() == PANEL_NAME:
                    panel = child
                    pane = widget
                    break

    if bool(panel):

        pane.setCurrentWidget(panel)
        panel.setFocus(QtCore.Qt.ActiveWindowFocusReason)
        panel.activateWindow()

    else:
        import nuke
        from nukescripts import panels
        found = False
        panel = panels.__panels.get(PANEL_NAME).__call__()
        for dock in ['Properties.1',
                     'Viewer.1',
                     'DAG.1']:
            pane = nuke.getPaneFor(dock)
            if pane:
                panel.addToPane(pane)
                found = True
                break
        if not found:
            panels.__panels[PANEL_NAME]()


def setup():
    menu_setup()
    nukedock.setup_dock()
