import os
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import textwrap
import unittest

import axamd.client
import pyflakes.api
import pyflakes.reporter
import six

class TestFlakes(unittest.TestCase):
    _base_dir = os.path.dirname(axamd.client.__file__)
    for fn in pyflakes.api.iterSourceCode([_base_dir]):
        six.exec_(textwrap.dedent('''\
            def _tcase(self):
                errors = StringIO()
                reporter = pyflakes.reporter.Reporter(errors, errors)
                f = open({0!r})
                pyflakes.api.check(f.read(), {0!r}, reporter=reporter)
                f.close()
                if errors.tell():
                    self.fail(errors.getvalue())
                '''.format(fn)))
        _tname = fn[len(_base_dir)+1:-3].replace('/','_')
        six.exec_('test_flakes_{} = _tcase'.format(_tname))
    longMessage = True
