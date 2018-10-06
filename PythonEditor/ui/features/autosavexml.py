"""
All modifications to the PythonEditor.xml
file are done through this module.

All the out points of this module:
- line 62 in init_file_header
"""

from __future__ import unicode_literals
from __future__ import print_function

import os
import io
import unicodedata
from xml.etree import cElementTree as ElementTree
from functools import partial

from PythonEditor.ui.Qt import QtCore, QtWidgets
from PythonEditor.utils import save
from PythonEditor.utils.signals import connect
from PythonEditor.utils.constants import NUKE_DIR


AUTOSAVE_FILE = os.path.join(NUKE_DIR, 'PythonEditorHistory.xml')
XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'


class CouldNotCreateAutosave(Exception):
    pass


def create_autosave_file():
    """
    Create the autosave file into which
    PythonEditor stores all tab contents.
    """
    # look for the autosave
    if os.path.isfile(AUTOSAVE_FILE):

        # if the autosave file is empty, write header
        with open(AUTOSAVE_FILE, 'r') as f:
            is_empty = not bool(f.read().strip())
        if is_empty:
            init_file_header()
    else:

        # if file not found, check if directory exists
        if not os.path.isdir(NUKE_DIR):
            msg = 'Directory %s does not exist' % NUKE_DIR
            raise CouldNotCreateAutosave(msg)
        else:
            init_file_header()
    return True


def init_file_header():
    """
    Write the default file header into the xml file.
    Overwrites any existing file.
    """
    with open(AUTOSAVE_FILE, 'w') as f:
        f.write(XML_HEADER+'<script></script>')


def get_editor_xml():
    if not create_autosave_file():
        return
    parser = ElementTree.parse(AUTOSAVE_FILE)
    root = parser.getroot()
    editor_elements = root.findall('external_editor_path')
    return root, editor_elements


def get_external_editor_path():
    """
    Checks the autosave file for an
    <external_editor_path> element.
    """
    editor_path = os.environ.get('EXTERNAL_EDITOR_PATH')
    if (editor_path is not None
            and os.path.isdir(os.path.dirname(editor_path))):
        return editor_path

    root, editor_elements = get_editor_xml()

    if editor_elements:
        editor_element = editor_elements[0]
        path = editor_element.text
        if path and os.path.isdir(os.path.dirname(path)):
            editor_path = path

    if editor_path:
        os.environ['EXTERNAL_EDITOR_PATH'] = editor_path
        return editor_path
    else:
        return set_external_editor_path(ask_user=True)


def set_external_editor_path(path=None, ask_user=False):
    """
    Prompts the user for a new
    external editor path.
    TODO: Set temp program if none found.
    """
    root, editor_elements = get_editor_xml()
    for e in editor_elements:
        root.remove(e)

    if ask_user and not path:
        from PythonEditor.ui.Qt import QtWidgets
        dialog = QtWidgets.QInputDialog()
        args = (dialog,
                u'Get Editor Path',
                u'Path to external text editor:')
        results = QtWidgets.QInputDialog.getText(*args)
        path, ok = results
        if not ok:
            msg = 'Certain features will not work without '\
                'an external editor. \nYou can add or change '\
                'an external editor path later in Edit > Preferences.'
            msgBox = QtWidgets.QMessageBox()
            msgBox.setText(msg)
            msgBox.exec_()
            return None

    if path and os.path.isdir(os.path.dirname(path)):
        editor_path = path
        os.environ['EXTERNAL_EDITOR_PATH'] = editor_path

        element = ElementTree.Element('external_editor_path')
        element.text = path
        root.append(element)

        writexml(root)
        return path

    elif ask_user:
        from PythonEditor.ui.Qt import QtWidgets
        msg = u'External editor not found. '\
              'Certain features will not work.'\
              '\nYou can add or change an external '\
              'editor path later in Edit > Preferences.'
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText(msg)
        msgBox.exec_()
        return None


def not_ctrl(ch):
    is_ctrl_char = unicodedata.category(ch) == 'Cc'
    not_newline = ch != '\n'
    return (is_ctrl_char and not_newline)


def remove_control_characters(s):
    """
    Identify and remove any control characters from given string s.
    """
    cc = ''.join(ch for ch in s if not_ctrl(ch))
    print('Removing undesirable control characters:', cc)

    def no_cc(ch):
        if ch == '\n':
            return True
        if unicodedata.category(ch) != "Cc":
            return True
        return False

    return ''.join(ch for ch in s if no_cc(ch))


def get_tab_index(subscript):
    """
    To be used as a key function in a list sort.
    """
    tab_index = subscript.attrib.get('tab_index')
    try:
        return int(tab_index)
    except TypeError:
        return 1


def parsexml(element_name, path=AUTOSAVE_FILE):
    if not create_autosave_file():
        return

    try:
        xmlp = ElementTree.XMLParser(encoding="utf-8")
        parser = ElementTree.parse(path, xmlp)
    except ElementTree.ParseError as e:
        print('ElementTree.ParseError', e)
        parser = fix_broken_xml(path)

    root = parser.getroot()
    elements = root.findall(element_name)
    return root, elements


def writexml(root, path=AUTOSAVE_FILE):
    data = ElementTree.tostring(root)
    data = data.decode('utf-8')
    data = data.replace('><subscript', '>\n<subscript')
    data = data.replace('</subscript><', '</subscript>\n<')

    with io.open(path, 'wt', encoding='utf8', errors='ignore') as f:
        f.write(XML_HEADER+data)


def fix_broken_xml(path=AUTOSAVE_FILE):
    """
    Removes unwanted characters and
    (in case necessary in future
    implementations..) fixes other
    parsing errors with the xml file.
    """
    with io.open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    safe_string = remove_control_characters(content)

    with open(path, 'wt') as f:
        f.write(safe_string)

    xmlp = ElementTree.XMLParser(encoding="utf-8")
    parser = ElementTree.parse(path, xmlp)
    return parser


def remove_empty_autosaves():
    """
    Clean autosave file of subscripts with no
    information (no text and invalid or absent path).
    """
    root, subscripts = parsexml('subscript')
    changes_made = False
    for s in subscripts:
        if not s.text:
            path = s.attrib.get('path')
            if (path is None) or (not os.path.isfile(path)):
                root.remove(s)
                changes_made = True
                continue

            file_name = os.path.basename(path)
            if s.attrib['name'] != file_name:
                s.attrib['name'] = file_name
                changes_made = True

    if changes_made:
        writexml(root)


def update_autosave_attributes(editor_dict):
    """
    Update any of the attributes that may have been
    changed during the reading process, such as
    tab_name or tab_index.
    """
    root, subscripts = parsexml('subscript')

    changes_made = False

    for s in subscripts:
        uid = s.attrib.get('uuid')
        if uid is None:
            continue
        tab = editor_dict[uid]
        for a in 'tab_name', 'path', 'tab_index':
            a1, a2 = a, a
            if a == 'tab_name':
                a1 = 'name'
            if s.attrib.get(a1) != tab[a2]:
                s.attrib[a1] = str(tab[a2])
                changes_made = True

    if changes_made:
        writexml(root)


from PythonEditor.ui import editor as EDITOR
class DummyWidget(QtWidgets.QWidget):
    """docstring for DummyWidget"""
    def __init__(self, tab_data, tabs):
        super(DummyWidget, self).__init__()
        self.tab_data = tab_data
        self._layout = QtWidgets.QHBoxLayout(self)
        self.tabs = tabs
        self.editor_created = False

    def showEvent(self, event):
        if not self.editor_created:
            self.create_editor()
        super(DummyWidget, self).showEvent(event)

    def create_editor(self):
        self.editor_created = True
        # count = self.count()
        # index = 0 if count == 0 else count - 1
        editor = EDITOR.Editor(
            handle_shortcuts=False,
            uid=self.tab_data['uid'],
            init_display=True
            )

        editor.name = self.tab_data['tab_name']
        editor.path = self.tab_data['path']
        editor.uid = self.tab_data['uid']
        editor.tab_index = self.tabs.currentIndex()
        editor.setPlainText(self.tab_data['text'])

        # relay the contents saved signal
        editor.contents_saved_signal.connect(self.tabs.contents_saved_signal)
        self._layout.addWidget(editor)
        self.editor = editor
        editor.show()
        print('adding editor!')
        editor.setFocus()
        # return editor


class AutoSaveManager(QtCore.QObject):
    """
    Simple xml text storage.

    TODO: Check that these rules are being followed.
    # Reads when:
    - A new file is opened (text is set and file path is stored)
    - Restoring Autosave from XML: is read from xml file (unsaved)
    - Restoring Autosave from File: File is read from xml path
    when tab is left open

    # Writes when:
    - A file is saved (asks for file path if xml attrib not present)

    # Autosaves editor contents when:
    - An opened file (in read-only mode) has been edited
    - A new tab is opened and content created

    # Deletes when:
    - When writing to a file, the autosave text
    content is cleared, but the xml entry is left.
    - When closing a tab:
        if there is autosaved content:
            the user will be asked to save.
            if they do:
                the file is saved, the xml content cleared
        the xml entry will be deleted.
    """
    new_tab_signal = QtCore.Signal(str)
    def __init__(self, tabs, tab_index=None):
        super(AutoSaveManager, self).__init__()
        self.setObjectName('AutoSaveManager')
        create_autosave_file()
        self.timer_waiting = False
        self.setup_save_timer(interval=1000)

        self.tabs = tabs
        self.setParent(tabs)

        # connect tab signals
        tss = tabs.tab_switched_signal
        tss.connect(self.handle_tab_switch)
        tss.connect(self.check_document_modified)
        tcr = tabs.tabCloseRequested
        tcr.connect(self.handle_tab_close)
        rts = tabs.reset_tab_signal
        rts.connect(self.clear_subscripts)
        cts = tabs.closed_tab_signal
        cts.connect(self.editor_close_handler, QtCore.Qt.DirectConnection)
        css = tabs.contents_saved_signal
        css.connect(self.handle_document_save)
        tmv = tabs.tab_moved_signal
        tmv.connect(self.handle_tab_moved)

        self.set_editor()
        # self.readautosave()
        self.loadautosave()

    @QtCore.Slot(int, int, bool)
    def handle_tab_switch(self, previous, current, tabremoved):
        if not tabremoved:  # nothing's been deleted
                            # so we need to disconnect
                            # signals from previous editor
            self.disconnect_signals()

        self.set_editor()

    def set_editor(self):
        """
        Sets the current editor
        and connects signals.
        """
        editor = self.tabs.currentWidget()
        hasedit = hasattr(self, 'editor')
        editorChanged = True if not hasedit else self.editor != editor
        isEditor = editor.objectName() == 'Editor'
        if isEditor and editorChanged:
            self.editor = editor
            self.connect_signals()

    def connect_signals(self):
        """ Connects the current editor's signals to this class """
        pairs = [
            (self.editor.textChanged, self.save_timer),
            (self.editor.focus_in_signal, self.check_document_modified),
        ]
        self._connections = []
        for signal, slot in pairs:
            name, _, handle = connect(self.editor, signal, slot)
            self._connections.append((name, slot))

    def disconnect_signals(self):
        """ Disconnects the current editor's signals from this class """
        if not hasattr(self, 'editor'):
            return
        cx = self._connections
        for name, slot in cx:
            for x in range(self.editor.receivers(name)):
                self.editor.disconnect(name, slot)
        self._connections = []

    def setup_save_timer(self, interval=500):
        """
        Initialise the autosave timer.
        :param interval: autosave interval in milliseconds
        :type interval: int
        """
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(interval)

    def save_timer(self):
        """
        On textChanged, if no text present, save immediately.
        Else, start a timer that will trigger autosave after
        a brief pause in typing.
        """
        if not self.editor.toPlainText().strip():
            return self.autosave()

        self.timer_waiting = True
        if self.timer.isActive():
            self.timer.stop()

        self.setup_save_timer()
        autosave = partial(self.autosave_handler, self.editor)
        self.timer.timeout.connect(autosave)
        self.timer.start()

    def autosave_handler(self, editor=None):
        """
        Autosave timeout triggers this.
        """
        self.timer_waiting = False
        self.autosave(editor=editor)

    def set_editor_file(self, editor, path):
        """
        Set editor text and path, and into read-only mode.
        """
        path, text = self.readfile(path)
        editor.read_only = True
        editor.path = path
        editor.setPlainText(text)

    def readfile(self, path):
        """
        Changes .pyc to .py in path arguments.
        Opens the file and returns the text.
        """
        if '.xml' in path:
            return self.readxml(path)

        # do not open compiled python files
        path = path.replace('.pyc', '.py')

        with io.open(path, 'r') as f:
            text = f.read()

        return path, text

    def readxml(self, path):
        parser = ElementTree.parse(path)
        root = parser.getroot()
        self.editor.setPlainText(root.text)

    def readautosave(self):
        """
        Read the autosave file to return a
        dictionary of editor attributes and
        their contents.

        Provides default values if they don't
        exist.
        """
        editor_count = 0
        editor_dict = {}

        root, subscripts = parsexml('subscript')
        subscripts = sorted(subscripts, key=get_tab_index)

        for s in subscripts:

            uid = s.attrib.get('uuid')
            if uid is None:
                uid = str(uuid.uuid4())

            path = s.attrib.get('path')
            if path is None:
                path = ''

            tab_index = s.attrib.get('tab_index')
            if tab_index is None:
                tab_index = editor_count
            tab_index = int(tab_index)

            text = s.text
            if (text is None) or (not bool(text.strip())):
                text = ''
                if os.path.isfile(path):
                    path, text = self.readfile(path)

            tab_name = s.attrib.get('name')
            if tab_name is None:
                tab_name = 'Tab_%s' % editor_count

            editor_dict[uid] = {
            'uid':             uid,
            'tab_name':   tab_name,
            'path':           path,
            'tab_index': tab_index,
            'text':           text,
            }

            editor_count += 1

        return editor_dict

    def create_editors(self, editor_dict):
        """
        Populate the tabwidget with editors.
        The editor_dict may get updated with
        new tab_indexes during this process.
        """
        self.index_has_changed = False

        # return
        test_1 = False
        test_2 = False
        test_3 = False
        test_4 = False

        if test_1:
            self.lazy_load_timer = QtCore.QTimer()
            self.lazy_load_timer.timeout.connect()
            #TEST 1: let's do this via signals. at least that'll improve my numbers.
            self.new_tab_signal.connect(self.tabs.new_tab)
            for tab in editor_dict.values():
                self.new_tab_signal.emit(tab['tab_name'])

            return

        if test_2:
            #TEST 2 - how fast are regular tabs? Answer - MUCH faster.
            self.test_tabs = QtWidgets.QTabWidget()
            tabs = self.test_tabs
            # tabs = self.tabs
            from pprint import pprint
            # pprint(editor_dict)
            for tab in editor_dict.values():
                e = QtWidgets.QPlainTextEdit()
                tabs.insertTab(
                    int(tab['tab_index']),
                    e,
                    unicode(tab['tab_name'])
                    )
                e.setPlainText(tab['text'])

            self.test_tabs.show()
            return
            #TEST

        if test_3:
            #TEST 2 - how fast are regular tabs? Answer - MUCH faster.
            self.test_tabs = QtWidgets.QTabWidget()
            tabs = self.test_tabs
            # tabs = self.tabs
            for x in range(200):
                e = QtWidgets.QPlainTextEdit()
                tabs.insertTab(0, e, 'tab_%s' % x)
            self.test_tabs.show()
            return
            #TEST


        def by_index(item):
            return item.get('tab_index')

        editors_in_order = sorted(editor_dict.values(), key=by_index)

        if test_4: # dummy widget
            self.loading_all_tabs = True
            for tab in editors_in_order:
                w = DummyWidget(tab, self.tabs)
                index = int(tab['tab_index'])
                self.tabs.insertTab(index, w, tab['tab_name'])
                self.tabs.setCurrentIndex(index)

            w.create_editor()
            self.editor = w.editor
            self.set_editor()
            self.loading_all_tabs = False
            return

        editors = []
        self.loading_all_tabs = True
        for tab in editors_in_order:
            editor = self.tabs.new_tab(tab_name=tab['tab_name'], init_features=False)
            editors.append(editor)

            editor.uid  =  tab['uid']
            editor.path = tab['path']
            text        = tab['text']

            editor.read_only = bool(text)
            index = self.tabs.currentIndex()
            editor.tab_index = index

            if index != int(tab['tab_index']):
                self.index_has_changed = True
                tab['tab_index'] = index

            editor.setPlainText(text)
        self.loading_all_tabs = False

        return editor_dict

    def loadautosave(self):
        """
        Sets editor text content. First checks the
        autosave file for <subscript> elements and
        creates a tab per element.
        """

        # 0) Clean autosave file for subscripts with no information (text|path).
        remove_empty_autosaves()

        # 1) Read from autosave
        editor_dict = self.readautosave()

        if len(editor_dict) == 0:
            self.tabs.new_tab()
            return

        # 2) Update xml attributes with latest editor attributes
        update_autosave_attributes(editor_dict)

        # 3) Create the editor tabs using cached data.
        self.create_editors(editor_dict)

        # 4) Update the autosave file with new tab positions if they have changed.
        if self.index_has_changed:
            root, subscripts = parsexml('subscript')
            subscripts = self.update_tab_order(subscripts)
            writexml(root)


    def update_tab_order(self, subscripts):
        uids = [(i, getattr(self.tabs.widget(i), 'uid', None))
                for i in range(self.tabs.count())]
        for s in subscripts:
            for i, uid in uids:
                if s.attrib.get('uuid') == uid:
                    s.attrib['tab_index'] = str(i)

    def check_document_modified(self):
        """
        On focus in event, check the xml
        to see if there are any differences.
        If there are, prompt the user to see
        if they want to update their tab.
        """
        if self.loading_all_tabs:
            return
        if self.timer_waiting:
            return

        root, subscripts = parsexml('subscript')

        all_match = True
        not_matching = []
        for s in subscripts:
            if s.attrib.get('uuid') == self.editor.uid:
                if s.text is None:
                    continue

                editor_text = self.editor.toPlainText()
                text_match = (s.text == editor_text)

                editor_name = self.editor.name
                name_match = (s.attrib.get('name') == editor_name)

                if not (text_match and name_match):
                    all_match = False
                    not_matching.append((s, self.editor))

        if all_match:
            return

        editor_present = False
        for index in range(self.tabs.count()):
            editor = self.tabs.widget(index)
            for _, e in not_matching:
                if e == editor:
                    editor_present = True
                    break

        if not editor_present:
            return

        self.lock = True
        mismatch_count = len(not_matching)
        if mismatch_count != 1:
            count = str(mismatch_count)
            print('More than one mismatch! Found {0}'.format(count))
            for s in not_matching:
                uid = s.attrib.get('uuid')
                name = s.attrib.get('name')
                print(uid, name)

        for s, editor in not_matching:
            # TODO: Display text/differences (difflib?)
            Yes = QtWidgets.QMessageBox.Yes
            No = QtWidgets.QMessageBox.No
            msg = 'Document "{0}" not matching'\
                  '\nPythonEditorHistory.xml "{1}"'\
                  '\n\nClick Yes to update this text to '\
                  'the saved version'\
                  '\nor No to overwrite the saved document.'

            name = s.attrib.get('name')
            msg = msg.format(editor.name, str(name))
            question = QtWidgets.QMessageBox.question
            reply = question(self.editor,
                             'Document Mismatch Warning',
                             msg,
                             Yes,
                             No)

            if reply == Yes:
                self.editor.setPlainText(s.text)
                if name is not None:
                    index = self.tabs.currentIndex()
                    self.tabs.setTabText(index, name)
            else:
                s.text = self.editor.toPlainText()
                writexml(root)
                self.autosave()
        self.lock = True

        self._timer = QtCore.QTimer()
        self._timer.setInterval(500)
        self._timer.setSingleShot(True)

        def unlock(): self.lock = False
        self._timer.timeout.connect(unlock)
        self._timer.start()

    @QtCore.Slot()
    def autosave(self, editor=None):
        """
        Saves editor contents into autosave
        file with a unique identifier (uuid)
        and accompanying file path if available.
        """
        if editor is None:
            editor = self.editor

        root, subscripts = parsexml('subscript')

        found = False
        for s in subscripts:
            if s.attrib.get('uuid') == editor.uid:
                if not editor.read_only:
                    s.text = editor.toPlainText()

                s.attrib['name'] = editor.name
                s.attrib['tab_index'] = str(editor.tab_index)
                if hasattr(editor, 'path'):
                    s.attrib['path'] = editor.path
                found = True

        if not found:
            sub = ElementTree.Element('subscript')
            sub.attrib['uuid'] = editor.uid
            sub.attrib['name'] = editor.name
            sub.attrib['tab_index'] = str(editor.tab_index)
            if hasattr(editor, 'path'):
                sub.attrib['path'] = editor.path
            if not editor.read_only:
                sub.text = editor.toPlainText()
            root.append(sub)

        writexml(root)

    @QtCore.Slot(object)
    def handle_document_save(self, editor):
        """
        Locate editor via uid attribute and remove the autosave
        contents if they match the given path file contents as
        these should be loaded from file on next app load
        (if the tab remains open).

        TODO: Instead of removing the saved file contents,
        it might be better to keep it and diff the file against
        the contents on tab close.
        """
        root, subscripts = parsexml('subscript')

        if not os.path.isfile(editor.path):
            print('No save file found. Retaining autosave.')
            return

        editor_found = False
        for s in subscripts:
            if s.attrib.get('uuid') == editor.uid:
                if not s.text:
                    continue
                with open(editor.path, 'rt') as f:
                    if s.text == f.read():
                        editor_found = True
                        s.text = ''
                        s.attrib['path'] = editor.path
                        editor.read_only = True
                    else:
                        msg = '{0} did not match {1} contents, autosave'
                        print(msg.format(editor.name, editor.path))

        if editor_found:
            writexml(root)
            print('Document {0} has been emptied'.format(editor.uid))

    @QtCore.Slot(object, int)
    def handle_tab_moved(self, editor, tab_index):
        self.autosave(editor=editor)

    @QtCore.Slot(int)
    def handle_tab_close(self, tab_index):
        """
        Called on tabCloseRequested
        Note: if this slot is called via tabCloseRequested,
        the tab will have already been closed, so the tab_index
        will point to a different tab.
        """
        self.remove_empty()

    def remove_empty(self):
        """
        Remove subscripts if they are empty.
        """
        root, subscripts = parsexml('subscript')

        for s in subscripts:
            notext = not s.text
            nopath = s.attrib.get('path') is None
            if notext and nopath:
                root.remove(s)

        writexml(root)

    @QtCore.Slot(object)
    def editor_close_handler(self, editor):
        """
        Called on closed_tab_signal. Checks to see if contents
        have been saved (by checking the read_only state of the
        editor), then removes the autosave contents.
        """
        # reset cancelled status to default
        self.tabs.user_cancelled_tab_close = False

        # check for unsaved contents.
        safe_to_remove = editor.read_only

        # if there's no text and no path
        # (i.e. user doesn't want to resave file as empty)
        is_empty = (editor.toPlainText().strip() == '')
        no_path = not hasattr(editor, 'path')
        if is_empty and no_path:
            safe_to_remove = True

        if not safe_to_remove:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setText('The document has been modified.')
            msg_box.setInformativeText('Do you want to save your changes?')
            buttons = msg_box.Save | msg_box.Discard | msg_box.Cancel
            msg_box.setStandardButtons(buttons)
            msg_box.setDefaultButton(msg_box.Save)
            ret = msg_box.exec_()

            user_cancelled = (ret == msg_box.Cancel)

            if (ret == msg_box.Save):
                path = save.save(editor)
                if path is None:
                    user_cancelled = True

            if user_cancelled:
                self.tabs.user_cancelled_tab_close = True
                return

        # if we arrive here it means one of the following:
        # a) file is not open for editing (read-only)
        # b) we've already saved
        # c) we've discarded the document
        # So it's safe to remove it.
        self.remove_subscript(editor.uid)

    def remove_subscript(self, uid):
        """
        Explicitly remove a subscript entry.

        :param uid: Unique Identifier of subscript
        to remove
        """
        root, subscripts = parsexml('subscript')

        item_removed = False
        for s in subscripts:
            if s.attrib.get('uuid') == uid:
                root.remove(s)
                item_removed = True

        if item_removed:
            writexml(root)

    @QtCore.Slot()
    def clear_subscripts(self):
        root, subscripts = parsexml('subscript')

        for s in subscripts:
            root.remove(s)

        writexml(root)
