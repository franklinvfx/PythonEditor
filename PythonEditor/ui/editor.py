import uuid
from PythonEditor.utils.Qt import QtWidgets, QtGui, QtCore

from PythonEditor.ui.dialogs import shortcuteditor
from PythonEditor.ui.features import (shortcuts,
                                      linenumberarea,
                                      syntaxhighlighter,
                                      autocompletion,
                                      contextmenu)

CTRL_ALT = QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier

# themes = {
#     'Monokai': 'background:#272822;color:#EEE;',
#     'Monokai Smooth': 'background:rgb(45,42,46);color:rgb(252,252,250);',
# }


class Editor(QtWidgets.QPlainTextEdit):
    """
    Code Editor widget.
    """
    wrap_types = ['\'', '"',
                  '[', ']',
                  '(', ')',
                  '{', '}',
                  '<', '>']

    tab_signal = QtCore.Signal()
    return_signal = QtCore.Signal(QtGui.QKeyEvent)
    wrap_signal = QtCore.Signal(str)
    focus_in_signal = QtCore.Signal(QtGui.QFocusEvent)
    key_pressed_signal = QtCore.Signal(QtGui.QKeyEvent)
    post_key_pressed_signal = QtCore.Signal(QtGui.QKeyEvent)
    wheel_signal = QtCore.Signal(QtGui.QWheelEvent)
    context_menu_signal = QtCore.Signal(QtWidgets.QMenu)
    home_key_signal = QtCore.Signal()
    home_key_ctrl_alt_signal = QtCore.Signal()
    end_key_ctrl_alt_signal = QtCore.Signal()
    ctrl_x_signal = QtCore.Signal()
    ctrl_n_signal = QtCore.Signal()
    ctrl_w_signal = QtCore.Signal()
    ctrl_enter_signal = QtCore.Signal()

    relay_clear_output_signal = QtCore.Signal()
    editingFinished = QtCore.Signal()
    name_changed_signal = QtCore.Signal(str, str)

    def __init__(self, handle_shortcuts=True):
        super(Editor, self).__init__()
        self.setObjectName('Editor')
        self.setAcceptDrops(True)
        # font = QtGui.QFont('Consolas')
        # font.setPointSize(9)
        # self.setFont(font)

        self._changed = False
        self.textChanged.connect(self._handle_text_changed)

        linenumberarea.LineNumberArea(self)
        syntaxhighlighter.Highlight(self.document())
        self.contextmenu = contextmenu.ContextMenu(self)
        # self.setStyleSheet(themes['Monokai Smooth'])

        self.wait_for_autocomplete = True
        self.autocomplete = autocompletion.AutoCompleter(self)

        if handle_shortcuts:
            sch = shortcuts.ShortcutHandler(self, use_tabs=False)
            sch.clear_output_signal.connect(self.relay_clear_output_signal)
            self.shortcuteditor = shortcuteditor.ShortcutEditor(sch)

        self._uid = str(uuid.uuid4())
        self._name = ''

        self.selectionChanged.connect(self.highlight_same_words)

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, uid):
        self._uid = uid

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        old_name = self._name
        self._name = name
        self.name_changed_signal.emit(old_name, name)

    def _handle_text_changed(self):
        self._changed = True

    def setTextChanged(self, state=True):
        self._changed = state

    def highlight_same_words(self):
        """
        Highlights other matching words in document
        when full word selected.
        TODO: implement this!
        """
        textCursor = self.textCursor()
        if not textCursor.hasSelection():
            return

        # text = textCursor.selection().toPlainText()
        # textCursor.select(QtGui.QTextCursor.WordUnderCursor)
        # word = textCursor.selection().toPlainText()
        # print(text, word)
        # if text == word:
            # print(word)

    def focusInEvent(self, event):
        self.focus_in_signal.emit(event)
        super(Editor, self).focusInEvent(event)

    def focusOutEvent(self, event):
        if self._changed:
            self.editingFinished.emit()
        super(Editor, self).focusOutEvent(event)

    def keyPressEvent(self, event):
        """
        Emit signals for key events
        that QShortcut cannot override.
        """
        if self.wait_for_autocomplete:
            self.key_pressed_signal.emit(event)
            return

        if event.modifiers() == QtCore.Qt.NoModifier:
            if event.key() == QtCore.Qt.Key_Tab:
                return self.tab_signal.emit()
            if event.key() == QtCore.Qt.Key_Return:
                return self.return_signal.emit(event)

        if (event.key() == QtCore.Qt.Key_Return
                and event.modifiers() == QtCore.Qt.ControlModifier):
            return self.ctrl_enter_signal.emit()

        if (event.text() in self.wrap_types
                and self.textCursor().hasSelection()):
            return self.wrap_signal.emit(event.text())

        if event.key() == QtCore.Qt.Key_Home:
            if event.modifiers() == CTRL_ALT:
                self.home_key_ctrl_alt_signal.emit()
            elif event.modifiers() == QtCore.Qt.NoModifier:
                return self.home_key_signal.emit()

        if (event.key() == QtCore.Qt.Key_End
                and event.modifiers() == CTRL_ALT):
            self.end_key_ctrl_alt_signal.emit()

        if (event.key() == QtCore.Qt.Key_X
                and event.modifiers() == QtCore.Qt.ControlModifier):
            self.ctrl_x_signal.emit()

        if (event.key() == QtCore.Qt.Key_N
                and event.modifiers() == QtCore.Qt.ControlModifier):
            self.ctrl_n_signal.emit()

        if (event.key() == QtCore.Qt.Key_W
                and event.modifiers() == QtCore.Qt.ControlModifier):
            self.ctrl_w_signal.emit()

        super(Editor, self).keyPressEvent(event)
        self.post_key_pressed_signal.emit(event)

    def keyReleaseEvent(self, event):
        self.wait_for_autocomplete = True
        super(Editor, self).keyReleaseEvent(event)

    def contextMenuEvent(self, event):
        """
        Creates a standard context menu
        and emits it for futher changes
        and execution elsewhere.
        """
        menu = self.createStandardContextMenu()
        self.context_menu_signal.emit(menu)

    def dragEnterEvent(self, e):
        mimeData = e.mimeData()
        if mimeData.hasUrls:
            e.accept()
        else:
            super(Editor, self).dragEnterEvent(e)

        # let's see what the data contains, at least!
        # maybe restrict this to non-known formats...
        for f in mimeData.formats():
            data = str(mimeData.data(f)).replace(b'\0', b'')
            data = data.replace(b'\x12', b'')
            print(f, data)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            super(Editor, self).dragMoveEvent(e)

    def dropEvent(self, e):
        """
        TODO: e.ignore() files and send to edittabs to
        create new tab instead?
        """
        mimeData = e.mimeData()
        if (mimeData.hasUrls
                and mimeData.urls()):
            urls = mimeData.urls()

            text_list = []
            for url in urls:
                path = url.toLocalFile()
                with open(path, 'r') as f:
                    text_list.append(f.read())

            self.textCursor().insertText('\n'.join(text_list))
        else:
            super(Editor, self).dropEvent(e)

    def wheelEvent(self, e):
        """
        Restore focus and emit signal if ctrl held.
        """
        self.setFocus(QtCore.Qt.MouseFocusReason)
        if (e.modifiers() == QtCore.Qt.ControlModifier
                and e.orientation() == QtCore.Qt.Orientation.Vertical):
            return self.wheel_signal.emit(e)
        super(Editor, self).wheelEvent(e)
