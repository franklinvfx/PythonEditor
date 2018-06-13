from __future__ import print_function
import sys

from PythonEditor.utils.Qt import QtGui, QtWidgets, QtCore
from PythonEditor.core import stream


class Terminal(QtWidgets.QPlainTextEdit):
    """ Output text display widget """
    link_activated = QtCore.Signal(str)

    def __init__(self):
        super(Terminal, self).__init__()
        # self.setStyleSheet('background:rgb(45,42,46);')

        self.setObjectName('Terminal')
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setReadOnly(True)
        self.setup()
        self.destroyed.connect(self.stop)

    @QtCore.Slot(str)
    def receive(self, text):
        try:
            textCursor = self.textCursor()
            if bool(textCursor):
                self.moveCursor(QtGui.QTextCursor.End)
                # pos = textCursor.position()
                # self.moveCursor(pos-1)
        except Exception:
            pass
        self.insertPlainText(text)
        # self.appendHtml(text)

    def stop(self):
        sys.stdout.reset()
        sys.stderr.reset()

    def setup(self):
        """
        Checks for an existing stream wrapper
        for sys.stdout and connects to it. If
        not present, creates a new one.
        TODO:
        The FnRedirect sys.stdout is always active.
        With a singleton object on a thread,
        that reads off this stream, we can make it
        available to Python Editor even before opening
        the panel.
        """

        if hasattr(sys.stdout, '_signal'):
            speaker = sys.stdout._signal
        else:
            speaker = stream.Speaker()
            sys.stdout = stream.SESysdStdOut(sys.stdout, speaker)
            sys.stderr = stream.SESysStdErr(sys.stderr, speaker)

        speaker.emitter.connect(self.receive)

    def mousePressEvent(self, e):
        if not hasattr(self, 'anchorAt'):
            #pyqt doesn't use anchorAt
            return super(Terminal, self).mousePressEvent(e)

        if (e.button() == QtCore.Qt.LeftButton):
            clickedAnchor = self.anchorAt(e.pos())
            if clickedAnchor:
                self.link_activated.emit(clickedAnchor)
        super(Terminal, self).mousePressEvent(e)
