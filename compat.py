# flake8: noqa

import sys

PY2 = sys.version_info[0] == 2
PY3 = (sys.version_info[0] >= 3)

if PY2:
    import Queue as queue
else:  # PY3
    import queue
    #print('PY3= ', PY3)

try:
    import cPickle as pickle
except ImportError:
    import pickle
