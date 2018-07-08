from __future__ import print_function
from PythonEditor.utils.Qt import QtWidgets, QtCore, QtGui
from PythonEditor.ui import editor


css = open('C:\Repositories\PythonEditor\css\qtabwidget.css').read()


class EditTabs(QtWidgets.QTabWidget):
    """
    QTabWidget containing Editor
    QPlainTextEdit widgets.
    TODO: Set stylesheet to
    have tabs the same height as Nuke's.
    """
    reset_tab_signal = QtCore.Signal()
    closed_tab_signal = QtCore.Signal(object)
    tab_switched_signal = QtCore.Signal(int, int, bool)
    new_editor_signal = QtCore.Signal(editor.Editor)
    tab_rename_signal = QtCore.Signal(str, str)

    def __init__(self):
        QtWidgets.QTabWidget.__init__(self)
        self.setTabBar(TabBar(self))
        self.setTabsClosable(True)
        self.setTabShape(QtWidgets.QTabWidget.Rounded)

        self.tab_count = 0
        self.current_index = 0

        tabBar = self.tabBar()
        tabBar.setMovable(True)
        tabBar.tabMoved.connect(self.tab_restrict_move)
        tabBar.enter_signal.connect(self.tab_enter_handler)
        tabBar.tab_rename_signal.connect(self.tab_rename_signal)

        # self.setup_new_tab_btn()
        self.tabCloseRequested.connect(self.close_tab)
        self.reset_tab_signal.connect(self.reset_tabs)
        self.currentChanged.connect(self.widgetChanged)
        # self.setStyleSheet("QTabBar::tab { height: 24px; }")
        self.setStyleSheet(css)

    @QtCore.Slot(int, QtCore.QPoint)
    def tab_enter_handler(self, index, pos):
        editor = self.widget(index)
        if not hasattr(editor, 'objectName'):
            return
        if (editor.objectName() != 'Editor'
                or not hasattr(editor, 'path')):
            return

        info = editor.path

        global_rect = self.tabBar().mapToGlobal(pos)
        palette = QtWidgets.QToolTip.palette()
        palette.setColor(QtGui.QPalette.ToolTipText,
                         QtGui.QColor("#F6F6F6"))
        palette.setColor(QtGui.QPalette.ToolTipBase,
                         QtGui.QColor(45, 42, 46))
        QtWidgets.QToolTip.setPalette(palette)

        # TODO: Scrollable! Does QToolTip have this?
        QtWidgets.QToolTip.showText(global_rect, info)

    @QtCore.Slot(int, int)
    def tab_restrict_move(self, from_index, to_index):
        """
        Prevents tabs from being moved beyond the +
        new tab button.
        """
        if from_index >= self.count()-1:
            self.tabBar().moveTab(to_index, from_index)

    def setup_new_tab_btn(self):
        """
        Adds a new tab [+] button to the right of the tabs.
        """
        widget = QtWidgets.QWidget()
        widget.setObjectName('Tab_Widget_New_Button')
        self.insertTab(0, widget, '')
        nb = self.new_btn = QtWidgets.QToolButton()
        nb.setMinimumSize(QtCore.QSize(50, 10))
        nb.setText('+')  # you could set an icon instead of text
        nb.setAutoRaise(True)
        nb.clicked.connect(self.new_tab)

        tabBar = self.tabBar()
        tabBar.setTabButton(0, QtWidgets.QTabBar.RightSide, nb)
        tabBar.setTabEnabled(0, False)

    @QtCore.Slot(str)
    def new_tab(self, tab_name=None):
        """
        Creates a new tab.
        """
        count = self.count()
        index = 0 if count == 0 else count - 1
        _editor = editor.Editor(handle_shortcuts=False)

        if (tab_name is None):
            # tab_name = 'Tab_{0}'.format(index)
            tab_name = ''

        _editor.name = tab_name

        self.insertTab(index,
                       _editor,
                       tab_name
                       )
        self.setCurrentIndex(index)

        if not hasattr(self, 'tab_buttons'):
            self.tab_buttons = {}
        nb = TabButton(self, _editor)
        self.tab_buttons[nb] = self.widget(index)
        nb.setMinimumSize(QtCore.QSize(50, 10))
        nb.setAutoRaise(True)
        nb.setText('Tab_{0}'.format(index))
        from functools import partial
        # nb.clicked.connect(partial(self.set_tab, nb))
        self.tabBar().setTabButton(index, QtWidgets.QTabBar.RightSide, nb)

        self.tab_count = self.count()
        self.current_index = self.currentIndex()
        _editor.setFocus()
        self.new_editor_signal.emit(_editor)
        return _editor

    # def set_tab(self, nb):
    #     self.indexOf(self.tab_buttons[nb])

    def close_current_tab(self):
        """
        Closes the active tab.
        """
        _index = self.currentIndex()
        self.tabCloseRequested.emit(_index)

    def close_tab(self, index):
        if self.count() < 3:
            return
        _index = self.currentIndex()

        _editor = self.widget(index)
        if _editor.objectName() == 'Tab_Widget_New_Button':
            return

        self.closed_tab_signal.emit(_editor)
        _editor.deleteLater()

        self.removeTab(index)
        index = self.count() - 1
        self.setCurrentIndex(_index-1)
        self.tab_count = self.count()

    def reset_tabs(self):
        for index in reversed(range(self.count())):
            widget = self.widget(index)
            if widget is None:
                continue
            if widget.objectName() == 'Editor':
                self.removeTab(index)
        self.new_tab()

    @QtCore.Slot(int)
    def widgetChanged(self, index):
        """
        Triggers widget_changed signal with current widget.
        TODO: Investigate why this sometimes seems to cause
        signal connection errors in autosavexml and shortcuts.
        """
        tabremoved = self.count() < self.tab_count
        previous = self.current_index
        current = self.currentIndex()
        self.tab_switched_signal.emit(previous,
                                      current,
                                      tabremoved)
        self.current_index = self.currentIndex()
        self.tab_count = self.count()


class TabBar(QtWidgets.QTabBar):
    enter_signal = QtCore.Signal(int, QtCore.QPoint)
    tab_rename_signal = QtCore.Signal(str, str)

    def __init__(self, edittabs):
        super(TabBar, self).__init__()
        self.edittabs = edittabs
        self.setMouseTracking(True)
        self.current_hovered_index = -1
        self.read_only = True

    def paintEvent(self, event):
        """
        In case we are going to intercept how
        QTabBar paints tabs based on tab widget status.
        """
        super(TabBar, self).paintEvent(event)

    # def mousePressEvent(self, event):
    #     if event.button() == QtCore.Qt.RightButton:
    #         index = self.tabAt(event.pos())
    #         # enabled = self.isTabEnabled(index)
    #         # print(enabled)
    #         # self.setTabData('data', [])
    #         # self.setTabEnabled(index, not enabled)
    #     super(TabBar, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.pos()
        index = self.tabAt(pos)
        if index == self.current_hovered_index:
            return
        rect = self.tabRect(index)
        pos = QtCore.QPoint(rect.right()/2, rect.bottom())
        self.enter_signal.emit(index, pos)
        self.current_hovered_index = index
        super(TabBar, self).mouseMoveEvent(event)


class TabButton(QtWidgets.QToolButton):
    def __init__(self, edittabs, _editor):
        super(TabButton, self).__init__()
        self.edittabs = edittabs
        self.tab_bar = edittabs.tabBar()
        self._editor = _editor

    def mouseDoubleClickEvent(self, event):
        self.show_name_edit()
        super(TabButton, self).mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        # TODO: implement drag and drop to change tab positions
        self.edittabs.setCurrentWidget(self._editor)
        super(TabButton, self).mousePressEvent(event)

    def show_name_edit(self):
        """
        Shows a QLineEdit widget where the tab
        text is, allowing renaming of tabs.
        """
        self.rename_tab()

        editor = self.edittabs.currentWidget()
        if not editor.objectName() == 'Editor':
            return

        index = self.edittabs.indexOf(self._editor)
        # title = self.tabText(index)
        title = self.text()

        # self.editor = editor
        self.tab_text = title
        self.tab_index = index
        # self.setTabText(index, '')
        self.setText('')

        self.name_edit = QtWidgets.QLineEdit(self)
        self.name_edit.editingFinished.connect(self.rename_tab)
        self.name_edit.setText(title)
        self.name_edit.selectAll()

        self.tab_bar.setTabButton(index,
                          QtWidgets.QTabBar.RightSide,
                          self.name_edit)

        self.name_edit.setFocus(QtCore.Qt.MouseFocusReason)

    def rename_tab(self):
        """
        Sets the title of the current tab, then sets
        the editor 'name' property and refreshes the
        editor text to trigger the autosave which
        updates the name in the xml element.
        TODO: Needs to be the active tab to
        commit to the xml file!
        """
        if not (hasattr(self, 'name_edit')
                and self.name_edit.isVisible()):
            return

        self.name_edit.hide()

        text = self.name_edit.text().strip()
        if not bool(text):
            text = self.tab_text

        for tab_index in range(self.edittabs.count()):
            widget = self.edittabs.widget(tab_index)
            if widget == self._editor:
                self.tab_index = tab_index
            elif widget.objectName() == 'Editor':
                # prevent duplicate tab names
                if hasattr(widget, 'name'):
                    if widget.name == text:
                        text = self.tab_text

        self.setText(text)
        self.tab_bar.setTabButton(self.tab_index,
                          QtWidgets.QTabBar.RightSide,
                          self)

        editor = self._editor
        self.edittabs.setCurrentIndex(self.tab_index)
        if editor.objectName() == 'Editor':
            editor.name = text
            editor.setPlainText(editor.toPlainText())

        if text != self.tab_text:
            old_name = self.tab_text
            new_name = text
            self.tab_bar.tab_rename_signal.emit(old_name, new_name)
