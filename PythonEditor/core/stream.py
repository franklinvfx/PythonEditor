from __future__ import print_function
import sys

from PythonEditor.utils.Qt import QtCore


class PySingleton(object):
    """
    Return a single instance of a class
    or create a new instance if none exists.
    """
    def __new__(cls, *args, **kwargs):
        if '_the_instance' not in cls.__dict__:
            cls._the_instance = object.__new__(cls)
        return cls._the_instance


class Speaker(QtCore.QObject):
    """
    Used to relay sys stdout, stderr, stdin
    """
    emitter = QtCore.Signal(str)


class SERedirector(object):
    """
    Wraps and replaces a stream object.
    """
    def __init__(self, stream, _signal=None):
        fileMethods = ('fileno',
                       'flush',
                       'isatty',
                       'read',
                       'readline',
                       'readlines',
                       'seek',
                       'tell',
                       'write',
                       'writelines',
                       'xreadlines',
                       '__iter__')

        for i in fileMethods:
            if not hasattr(self, i) and hasattr(stream, i):
                setattr(self, i, getattr(stream, i))

        self.saved_stream = stream
        self._signal = _signal

    def write(self, text):
        if self._signal is not None:
            self._signal.emitter.emit(text)
        # sys.__stdout__.write(text)
        self.saved_stream.write(text)  # TODO: should write
                                       # if not visible, else
                                       # should emit. not both!
                                       # set a global variable on
                                       # terminal visible/invisible.

    def close(self):
        self.flush()

    def stream(self):
        return self.saved_stream

    def __del__(self):
        self.reset()


class SESysStdOut(SERedirector, PySingleton):
    def reset(self):
        sys.stdout = self.saved_stream
        print('reset stream out')


class SESysStdErr(SERedirector, PySingleton):
    def reset(self):
        sys.stderr = self.saved_stream
        print('reset stream err')
    # def write(self, text):  # TODO: Write html links here
                              # (or do it in a post process)
