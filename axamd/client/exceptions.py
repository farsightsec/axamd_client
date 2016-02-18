import itertools

class AXAMDException(Exception): pass
class ValidationError(AXAMDException): pass

class ProblemDetails(AXAMDException):
    """
    Implementation of draft-ietf-appsawg-http-problem-03
    """
    def __init__(self, problem):
        self.message = problem['title']
        super(ProblemDetails, self).__init__(self.message)
        self._problem = problem

    def __getattr__(self, attr):
        if attr in self._problem:
            return self._problem['attr']
        raise AttributeError

    def keys(self):
        return self._problem.keys()

    def __getitem__(self, k):
        return self._problem[k]

    def __contains__(self, k):
        return k in self._problem

    def __str__(self):
        keys = ['status', 'type', 'title']
        optional_keys = ['detail', 'instance']
        extra_keys = sorted(set(self._problem.keys()).difference(keys).difference(optional_keys))
        lines = []
        for key in itertools.chain(keys, optional_keys, extra_keys):
            if key in self._problem:
                lines.append('{}: {}'.format(key, self._problem[key]))
        return '\n'.join(lines)

