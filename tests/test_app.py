# put python shebang here for linux testing
""" For testing independently. """
import sys
import imp
import package_paths
import PythonEditor

package_paths  # to satisfy linter
imp.reload(PythonEditor)

if __name__ == '__main__':
    """
    For testing outside of nuke.
    """
    from PythonEditor.utils.Qt import QtWidgets
    from PythonEditor.ui.features import nukepalette

    app = QtWidgets.QApplication(sys.argv)
    ide = PythonEditor.ide.IDE()
    app.setPalette(nukepalette.getNukePalette())
    ide.show()
    ide.setStyleSheet('font-family:Consolas;font-size:8pt;')
    ide.resize(500, 500)
    plastique = QtWidgets.QStyleFactory.create('Plastique')
    QtWidgets.QApplication.setStyle(plastique)
    sys.exit(app.exec_())
