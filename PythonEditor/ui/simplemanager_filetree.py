import os
import sys
import io

def cd_up(path, level=1):
    for d in range(level):
        path = os.path.dirname(path)
    return path

package_dir = cd_up(__file__, level=3)
sys.path.insert(0, package_dir)

from PythonEditor.ui.Qt import QtWidgets, QtCore, QtGui
from PythonEditor.ui import editor
from PythonEditor.ui import filetree as browser
from PythonEditor.ui import menubar
from PythonEditor.utils.constants import NUKE_DIR


def get_parent(widget, level=1):
    """
    Return a widget's nth parent widget.
    """
    parent = widget
    for p in range(level):
        parent = parent.parentWidget()
    return parent


class Manager(QtWidgets.QWidget):
    """
    Manager with only one file connected at a time.
    """
    def __init__(self):
        super(Manager, self).__init__()
        self.currently_viewed_file = None
        self.blocking = True
        self.build_layout()

    def build_layout(self):
        """
        Create the layout.
        """
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.menubar = menubar.MenuBar(self)

        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter = splitter

        self.xpanded = False
        self.setLayout(layout)
        self.tool_button = QtWidgets.QToolButton()
        self.tool_button.setText('<')
        self.tool_button.clicked.connect(self.xpand)
        self.tool_button.setMaximumWidth(20)

        layout.addWidget(splitter)

        browse = browser.FileTree()
        self.browser = browse
        left_layout.addWidget(self.browser)
        self.browser.no_selection_signal.connect(self.read_temp)
        self.browser.name_edit_signal.connect(self.update_file_path)

        self.editor = editor.Editor(handle_shortcuts=True)
        self.read_temp()

        widgets = [left_widget,
                   self.tool_button,
                   self.editor]

        for w in widgets:
            splitter.addWidget(w)

        splitter.setSizes([200, 10, 800])
        self.browser.path_signal.connect(self.read)
        self.editor.textChanged.connect(self.write)

    def update_file_path(self, file_path):
        self.editor.path = file_path
        print 'updated to ' + file_path

    def read_temp(self):
        path = os.path.join(os.path.expanduser('~'), '.nuke')
        if os.path.isdir(path):
            path = os.path.join(path, 'PythonEditorHistory.py')
            if not os.path.isfile(path):
                with open(path, 'w') as f:
                    f.write('')
            self.editor.path = path
            self.temp_path = path
            self.read(path)

    def xpand(self):
        """
        Expand or contract the QSplitter
        to show or hide the file browser.
        """
        if self.xpanded:
            symbol = '<'
            sizes = [200, 10, 800]  # should be current sizes
        else:
            symbol = '>'
            sizes = [0, 10, 800]  # should be current sizes

        self.tool_button.setText(symbol)
        self.splitter.setSizes(sizes)
        self.xpanded = not self.xpanded

    def unblock_on_timer(self):
        self.blocking = False

    def start_timer(self):
        self._timer = QtCore.QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self.unblock_on_timer)
        self._timer.start()

    @QtCore.Slot(str)
    def read(self, path):
        """
        Read from text file.
        """
        if not os.path.isfile(path):
            return

        self.blocking = True
        self.start_timer()

        self.editor.path = path
        with io.open(path, 'rt', encoding='utf8', errors='ignore') as f:
            text = f.read()
            self.editor.setPlainText(text)

    @QtCore.Slot()
    def write(self):
        """
        Write to text file.
        """
        if self.blocking:
            return

        path = self.editor.path

        try:
            with io.open(path, 'wt', encoding='utf8', errors='ignore') as f:
                f.write(self.editor.toPlainText())
        except IOError as e:
            print 'Cannot write.', e

    def showEvent(self, event):
        """
        Hack to get rid of margins automatically put in
        place by Nuke Dock Window.
        """
        try:
            for i in 2, 4:
                parent = get_parent(self, level=i)
                parent.layout().setContentsMargins(0, 0, 0, 0)
        except Exception:
            pass

        super(Manager, self).showEvent(event)


if __name__ == '__main__':
    from PythonEditor.ui.features import nukepalette

    app = QtWidgets.QApplication(sys.argv)
    app.setPalette(nukepalette.getNukePalette())
    m = Manager()
    m.show()
    plastique = QtWidgets.QStyleFactory.create('Plastique')
    QtWidgets.QApplication.setStyle(plastique)
    # app.setFont(QtGui.QFont('Consolas'))
    app.exec_()
