import os
import sys
import io
import json

def cd_up(path, level=1):
    for d in range(level):
        path = os.path.dirname(path)
    return path

package_dir = cd_up(__file__, level=3)
sys.path.insert(0, package_dir)

from PythonEditor.ui.Qt import QtWidgets, QtCore, QtGui
from PythonEditor.ui import edittabs
from PythonEditor.ui import filetree as browser
from PythonEditor.ui import menubar
from PythonEditor.ui.features import shortcuts
from PythonEditor.utils.constants import CONFIG_DIR, TEMP_DIR

CONFIG_FILE = os.path.join(CONFIG_DIR, 'PythonEditorState.json')
print CONFIG_FILE


def get_parent(widget, level=1):
    """
    Return a widget's nth parent widget.
    """
    parent = widget
    for p in range(level):
        parent = parent.parentWidget()
    return parent


def read(file_path):
    """Reads text from a file"""
    with io.open(file_path, 'rt', encoding='utf8', errors='ignore') as f:
        text = f.read()
    return text


def write(file_path, contents):
    """Writes text to a file"""
    if isinstance(contents, str):
        contents = unicode(contents)
    with io.open(file_path, 'wt', encoding='utf8', errors='ignore') as f:
        f.write(contents)


def read_json(json_path):
    """
    Read a json file, load its contents.
    """
    data = read(json_path)
    json_dict = json.loads(data)
    return json_dict


def write_json(json_path, json_dict):
    """
    Write a dictionary to a json file.
    """
    assert isinstance(json_dict, dict)
    data = json.dumps(json_dict, indent=4)
    json_dir = cd_up(json_path)
    if os.path.isdir(json_dir):
        write(json_path, data)


class File(object):
    def __init__(self, editor):
        self.editor = editor
        self.editor.file = self
        self.path = editor.path

        name = editor.name
        if '.' not in name:
            name = name + '.py'

        self.temp = os.path.join(TEMP_DIR, name)

        # connect signals
        self.editor.textChanged.connect(self.autosave)

        if os.path.isfile(self.path):
            self.read(self.path)

    def read(self, path):
        """
        Read from text file and set current editor text.
        """
        self.editor.path = path
        text = read(path)
        self.editor.setPlainText(text)

    def autosave(self):
        """
        Write to autosave file.
        """
        temp_dir = os.path.dirname(self.temp)
        if not os.path.isdir(temp_dir):
            os.makedirs(temp_dir)

        write(self.temp, self.editor.toPlainText())

    def save(self):
        """
        Save text to desired file.
        """
        write(self.path, self.editor.toPlainText())


class Manager(QtWidgets.QWidget):
    """
    Manager connecting files and editor tabs.
    """
    def __init__(self):
        super(Manager, self).__init__()
        self.build_ui()
        self.file_dict = {}
        self._path = ''

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.browser = browser.FileTree()
        self.tabs = edittabs.EditTabs()
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        layout.addWidget(self.splitter)

        self.splitter.addWidget(self.browser)
        self.splitter.addWidget(self.tabs)
        self.splitter.setSizes([200, 800])

        # connect signals
        self.browser.path_signal.connect(self.path_signal_handler)
        shortcuts.ShortcutHandler(self.tabs)
        self.tabs.new_editor_signal.connect(self.new_editor_handler)
        self.tabs.closed_tab_signal.connect(self.closed_editor_handler)
        self.tabs.tab_rename_signal.connect(self.tab_rename_handler)

    @property
    def editor(self):
        self._editor = self.tabs.currentWidget()
        return self._editor

    @editor.setter
    def editor(self, editor):
        self._editor = editor

    @QtCore.Slot(str)
    def path_signal_handler(self, path):
        if not os.path.isfile(path):
            return
        file_name = os.path.basename(path)

        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if editor.objectName() != 'Editor':
                continue
            if not hasattr(editor, 'path'):
                continue
            if editor.path == path:
                self.tabs.setCurrentIndex(i)
                break
        else:
            self._path = path
            self.tabs.new_tab(tab_name=file_name)

    @QtCore.Slot(object)
    def new_editor_handler(self, editor):
        """
        Create a file object for the new editor.
        """
        editor.path = self._path
        file = File(editor)
        self.file_dict[file] = editor
        self._path = ''

    @QtCore.Slot(object)
    def closed_editor_handler(self, editor):
        """
        Cleanup file_dict,
        Ask if user wants to save
        """
        file_path = editor.path
        file_exists = os.path.isfile(file_path)
        contents = editor.toPlainText()

        if file_exists:
            text = read(file_path)
            if text != editor.toPlainText():
                # ask user if they want to save
                # in either case (let's not make temp files
                # sticky/too persistent):
                remove_temp = True

        # delete temp file and json entry
        temp_path = editor.file.temp
        # extra safety checks about the temp file being in the right directory
        if TEMP_DIR in temp_path:
            print 'dir in path! deleting empty file!'
        del self.file_dict[editor.file]

        json_dict = read_json(CONFIG_FILE)
        open_tabs = {editor.uid:{'path':file.path,
                                 'temp':file.temp}
                     for file, editor in self.file_dict.items()}
        json_dict['open_tabs'] = open_tabs
        print json_dict
        write_json(CONFIG_FILE, json_dict)

    @QtCore.Slot(str, str)
    def tab_rename_handler(self, old_name, new_name):
        print old_name, new_name

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
