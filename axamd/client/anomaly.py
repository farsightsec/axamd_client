class Anomaly:
    def __init__(self, module, watches=None, options=None):
        self.module = module
        self.watches = watches
        self.options = options

    def to_dict(self):
        d = { 'module': self.module }
        if self.watches:
            d['watches'] = self.watches
        if self.options:
            d['options'] = self.options
        return d

    def __str__(self):
        return '{}{}: [{}]'.format(self.watches,
                self.options and ' '+self.options or '', # prefix with space
                ', '.join('[{}]'.format(w) for w in self.watches))
