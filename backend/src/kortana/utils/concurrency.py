from contextlib import contextmanager
import threading

_logging_stack = threading.local()

@contextmanager
def recursion_guard():
    if getattr(_logging_stack, 'in_progress', False):
        yield False
    else:
        _logging_stack.in_progress = True
        try:
            yield True
        finally:
            _logging_stack.in_progress = False