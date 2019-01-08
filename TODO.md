# Python Editor TODO list


#### Bug fixes
- [x] Single line (selection-based) Ctrl+Enter no longer uses accurate lineno
- [x] When pressing keys simultaneously, the document changed window appears
- [ ] Clicking on a tab to the right of the QLineEdit when editing a tab name causes a jump, and the wrong tab to be selected.
- [ ] Save functions need to be amended to work with new single editor
- [ ] On first open (if not pinned to layout), tab may not display contents
- [x] CRITICAL BUG: Currently not fully reloadable (error with redirector)
- [x] After saving, close button appears stuck on saved symbol
- [x] Extra indentation occurs in some other programs - this was due to not using a monospaced font.
- [ ] Word wrapping and blocks can cause errors, especially in moving text up/down
- [x] Greedy shortcuts override Script Editor when Python Editor is open
- [ ] Tooltip colour permanently set in autocompletion
- [ ] Search causes cursor to go missing
- [ ] # in string causes rest of line to be greyed out
- [x] Autocomplete doesn't dissappear when parentheses are typed
- [ ] Double printing to sys.stdout (/probably/ caused by writing to sys.__stdout__ as well as outputRedirector)
- [ ] Override setPlainText to avoid string encoding errors (can this affect copy paste?)
- [x] CRITICAL BUG: In rare cases with network disruption the PythonEditorHistory.xml can be overwritten with 0 contents. PythonEditor will then not load.
      Add in a pre-check for xml contents in the file (if it exists) and implement some sort of backup procedure (e.g. copy to /tmp/ on script close)
- [x] Don't set QT_PREFERRED_BINDING if present.


#### Testing
- [ ] WRITE TESTS. [x] exploratory testing, [ ]  integration testing,
- [x] Check that tab closing and then cancelling restores the current tab (without causing disconnect/connect issues)
- [x] Check that tab renaming is consistent with autosave file
- [ ] Are editor properties correctly kept in sync? Any time a tab name or xml subscript changes, the editor
      should also change. What is the best way to monitor this?
- [ ] Are all function and method names clear in the API?
- [ ] Are all documentation strings up to date and correctly reflect the functions and classes?
- [ ] Thoroughly test that documents in autosave are not updating other documents
- [/] Autocomplete bug when typing inside list comprehension e.g. [nuke.selectedNodes] - partially fixed, doesn't
      autocomplete all names (and only completes every other character!)


#### Features - parity
- [x] Highlight line with error
- [x] Read stdout/stderr on open
- [ ] Add Script Editor buttons to Menu bar


#### Features - desired
- [ ] Move all actions to actions.py and have shortcuts simply setShortcut() on the Actions() class, which can be picked up by menus.
- [ ] Pre-reload PythonEditor safety backup
- [ ] Foldable sidebar with directory tree
- [ ] File Browser with connected file path
- [ ] Recent Files List
- [ ] Implement events or signals to redirect Script Editor stream (for speed)
- [x] Snippet file library (currently reads from a file called PythonEditor_snippets.json in .nuke dir if found.)
- [ ] Snippet save actions - write to PythonEditor_snippets.json
- [ ] Writing to external files instead of xml. Keeping those files in tab session until closed with a JSON file
- [x] Check if there's a better way to connect widgets/objects, synchronously
      (bypassing signal in cases where it's not wanted) - Resolved, starting to use DirectConnection
- [x] Set tab order as a property on the editor and in the autosave
- [/] Set up an execution model where stdout, stderr and stdin are temporarily encapsulated within a context managing with
      statement - is this a good idea? it means output will only be shown when text is executed from PythonEditor.
- [ ] Would be nice to highlight line on Ctrl+B execution (of single line)
- [ ] Tabs need QLabels so that they can be italicized when in read_only mode
- [ ] Tooltip displaying file path when hovering over tabs would be nice. (Easy to implement with QLabels)
- [ ] When save dialog comes up, the suggested name should be the tab name/editor.name - and if there's an
      editor path, the dialog should open to that path
- [ ] Add menu on the top right corner to select between tabs
- [ ] Preferences - colour
- [ ] Preferences - shortcuts - just need a place to save new shortcuts and override actions_dict
- [ ] Preferences - indentation (backspace deletes single space or tab)
- [ ] Preferences - disable autocompletion in comments
- [ ] Warn if file has changed on disk (as with autosave when regaining tab focus)
- [x] Small button at right of tab bar with a list of tab names
- [ ] After updating to saved version of autosave, there should be a possibility to undo if replacing with the autosave text wasn't desired.
- [ ] Autocompletion weighting (a la tabtabtab)
- [ ] Add reverse ' = '.join(reversed('sys.stdout = backup'.split(' = ')))
- [ ] GOTO tooltip over selected text
- [ ] Edit Snippets Dialog (for snippets in /.nuke/)
- [ ] Improve speed by loading tabs separately - (Lazy loading of tabs (or one single Autosave read/load operation instead of read/load/write/read))
- [ ] Duplicate cursors
- [ ] Search box at bottom of editor widget (with "all tabs" checkbox)
- [ ] Autocomplete 'toNode', node.knob() and node[knob]
- [ ] Projects
- [ ] Goto Links in errors/regular paths in the editor
- [ ] Hover over varibles to get definition goto, type info, short help()
- [ ] Hover over paths in output window to get goto link
- [ ] Paste into sublime subprocess.Popen('sublime -n --command paste', executable='/bin/tcsh', shell=True)


#### General
- [ ] Test moving TODO.md to github issues (not so great for local)


