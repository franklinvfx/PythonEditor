import os
import sys
import json


def cd_up(path, level=1):
    for d in range(level):
        path = os.path.dirname(path)
    return path


package_dir = cd_up(__file__, level=2)
sys.path.insert(0, package_dir)

from PythonEditor.utils.Qt import QtWidgets, QtCore, QtGui
from PythonEditor.utils.constants import CONFIG_DIR



class FileItem(QtGui.QStandardItem):
    path = None

    def setData(self, value, role):
        if role == QtCore.Qt.UserRole:
            self.path = value
        if role == QtCore.Qt.EditRole:
            self.edit_name(value)
        super(FileItem, self).setData(value, role)

    def edit_name(self, value):
        if self.path is None:
            raise Exception('No path for item')
        if not (os.path.isfile(self.path)
                or os.path.isdir(self.path)):
            raise Exception(self.path + ' does not exist')
        folder = os.path.dirname(self.path)
        new_path = os.path.join(folder, value)
        os.rename(self.path, new_path)
        self.path = new_path
        super(FileItem, self).setData(new_path,
                                      QtCore.Qt.UserRole)


class FileTree(QtWidgets.QTreeView):
    path_signal = QtCore.Signal(str)
    no_selection_signal = QtCore.Signal()
    name_edit_signal = QtCore.Signal(str)

    def __init__(self):
        super(FileTree, self).__init__()
        self.setAcceptDrops(True)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        mode = QtWidgets.QAbstractItemView.ContiguousSelection
        self.setSelectionMode(mode)
        self.header().hide()

        self._model = QtGui.QStandardItemModel()
        self.setModel(self._model)
        self._model.itemChanged.connect(self.item_changed_handler)
        self.root = self._model.invisibleRootItem()
        self.load_state()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            super(FileTree, self).dragMoveEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            super(FileTree, self).dragMoveEvent(e)

    def dropEvent(self, e):
        print e.mimeData().formats()
        # add ability to drag file paths in here
        if not e.mimeData().hasUrls:
            return
        for url in e.mimeData().urls():
            path = url.toLocalFile()
            self.load_path(path)

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.RightButton:
            print 'right'
            return
        if e.button() == QtCore.Qt.LeftButton:
            self.clearSelection()
            super(FileTree, self).mousePressEvent(e)
            selection = self.selectedIndexes()
            if not selection:
                self.no_selection_signal.emit()

    def keyReleaseEvent(self, e):
        if e.key() == QtCore.Qt.Key_Delete:
            self.remove_selected()
        super(FileTree, self).keyReleaseEvent(e)

    def selectionChanged(self, selected, deselected):
        for index in selected.indexes():
            item = self._model.itemFromIndex(index)
            path = item.data(QtCore.Qt.UserRole)
            self.path_signal.emit(path)
        super(FileTree, self).selectionChanged(selected, deselected)

    def remove_selected(self):
        selection = self.selectedIndexes()
        r = self.root
        top_level_items = [r.child(i, 0) for i in range(r.rowCount())]
        if selection:
            self.setUpdatesEnabled(False)
            to_remove = []
            for index in selection:
                item = self._model.itemFromIndex(index)
                if item in set(top_level_items):
                    to_remove.append(item)
            while len(to_remove) > 0:
                item = to_remove.pop()
                self._model.removeRow(item.row())
            self.setUpdatesEnabled(True)
            self.save_state()

    def load_path(self, path):
        if os.path.isdir(path):
            self.display_folder(path)
        elif os.path.isfile(path):
            self.open_file(path)

    @property
    def temp(self):
        if os.path.isdir(CONFIG_DIR):
            path = os.path.join(CONFIG_DIR, 'PythonEditorState.json')
            if not os.path.isfile(path):
                with open(path, 'w') as f:
                    f.write('')
        self._temp = path
        return path

    def save_state(self):
        """
        Save loaded files to a json file
        TODO: save QSettings.ini expanded state
        https://stackoverflow.com/questions/3253301/howto-restore-qtreeview-last-expanded-state
        """
        root = self._model.invisibleRootItem()
        paths = list()
        for i in reversed(range(root.rowCount())):
            path = root.child(i, 0).path
            if path not in paths:
                paths.append(path)

        json_dict = {}
        json_dict['tree_paths'] = paths
        data = json.dumps(json_dict, indent=4)
        with open(self.temp, 'w') as f:
            f.write(data)

    def load_state(self):
        """
        Load file paths from json file
        TODO: restore expanded state
        """
        with open(self.temp, 'r') as f:
            data = f.read()

        if not data.strip():
            return
        json_dict = json.loads(data)
        paths = json_dict.get('tree_paths')
        if paths is None:
            return
        for path in paths:
            self.load_path(path)

    @QtCore.Slot(QtGui.QStandardItem)
    def item_changed_handler(self, item):
        self.name_edit_signal.emit(item.path)

    def new_file_item(self, file_name, file_path):
        item = FileItem(file_name)
        item.setData(file_path, QtCore.Qt.UserRole)
        return item

    def display_folder(self, path):
        name = os.path.basename(path)
        item = self.new_file_item(name, path)
        self.root.appendRow([item])

        def recurse_path(path, parent_item):
            directory = os.listdir(path)
            for file_name in directory:
                if (file_name.endswith('.pyc')
                        or file_name.startswith('.')):
                    continue
                file_path = path + '/' + file_name
                new_item = self.new_file_item(file_name, file_path)
                parent_item.appendRow(new_item)
                if os.path.isdir(file_path):
                    recurse_path(file_path, new_item)

        recurse_path(path, item)
        self.save_state()

    def open_file(self, path):
        name = os.path.basename(path)
        item = self.new_file_item(name, path)
        self.root.insertRow(0, [item])
        self.save_state()

if __name__ == '__main__':
    from PythonEditor.ui.features import nukepalette

    app = QtWidgets.QApplication(sys.argv)
    app.setPalette(nukepalette.getNukePalette())
    tree = FileTree()
    tree.show()
    plastique = QtWidgets.QStyleFactory.create('Plastique')
    QtWidgets.QApplication.setStyle(plastique)
    app.exec_()
