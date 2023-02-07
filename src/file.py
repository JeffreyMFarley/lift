import os.path


class File(object):
    def __init__(self, full_path):
        self.full_path = full_path
        self._basename, self.ext = os.path.splitext(
            os.path.basename(full_path)
        )
        self.path_to = os.path.dirname(full_path)
        self._paths = self.path_to.split('/')

    def __lt__(self, other):
        return self.full_path < str(other)

    def __le__(self, other):
        return self.full_path <= str(other)

    def __eq__(self, other):
        return self.full_path == str(other)

    def __ne__(self, other):
        return self.full_path != str(other)

    def __gt__(self, other):
        return self.full_path > str(other)

    def __ge__(self, other):
        return self.full_path >= str(other)

    def __hash__(self):
        return hash(self.full_path)

    def __str__(self):
        return self.full_path

    @property
    def basename(self):
        return self._paths[-1] if self.is_init else self._basename

    @property
    def gv_name(self):
        '''A name that is safe for graphviz output'''
        x = self.full_path
        return x.replace('-', '_').replace('.', '_').replace('/', '')

    @property
    def dotted_path(self):
        return '.'.join(self._paths[2:])

    @property
    def modulename(self):
        if self.is_init:
            return '{}.{}'.format(self._paths[-2], self._paths[-1])
        return '{}.{}'.format(self._paths[-1], self._basename)

    @property
    def paths(self):
        return self._paths.copy()

    def distance(self, other):
        a = self.paths
        b = other.paths

        while len(a) and len(b):
            ax = a.pop(0)
            bx = b.pop(0)
            if ax != bx:
                return len(a) + len(b) + 2  # ax + bx

        return len(a) + len(b)

    def is_ancestor(self, other):
        a = self.paths
        b = other.paths

        while len(a) and len(b):
            ax = a.pop(0)
            bx = b.pop(0)
            if ax != bx:
                break

        return len(a) == 0 and len(b) > 0

    @property
    def is_init(self):
        return self._basename == '__init__'

    @property
    def is_root(self):
        return self._paths is None

    def is_sibling(self, other):
        return self.path_to == other.path_to

    @property
    def is_test(self):
        return (
            'test' in self._paths or self._basename.startswith('test_')
        )

    def relative_label(self, other):
        rpath = self.relative_path(other)
        if not rpath:
            return other._basename

        return '{}.{}'.format(rpath, other._basename)

    def relative_path(self, other):
        if self.is_sibling(other):
            return ''

        a = self.paths
        b = other.paths

        while len(a) and len(b):
            ax = a.pop(0)
            bx = b.pop(0)
            if ax != bx:
                break

        s = bx
        if len(b):
            s = '{}.{}'.format(bx, '.'.join(b))
        return s


def jsonEncoderFile(o):
    if isinstance(o, File):
        return o.full_path
