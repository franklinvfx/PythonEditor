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
    ide.setStyleSheet('font-family:Consolas;font-size:9pt;')
    ide.resize(500, 500)
    style = QtWidgets.QStyleFactory.create('Cleanlooks')
    # style = QtWidgets.QStyleFactory.create('Plastique')
    QtWidgets.QApplication.setStyle(style)
    sys.exit(app.exec_())
