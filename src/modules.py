import glob
import io
import json

from .file import File, jsonEncoderFile


# -----------------------------------------------------------------------------
# Modules - a dictionary of names that a particular file may appear as

class Modules(object):
    def __init__(self, options):
        self._cache = {}
        self._nodes = set()
        self.options = options

        self.build_module_list()

    def __getitem__(self, key):
        entry = self._cache.get(key, None)
        if entry is None:
            return None

        return entry

    def __iter__(self):
        return iter(self._nodes)

    def __repr__(self):
        return json.dumps(
            self._cache, indent=2, sort_keys=True, default=jsonEncoderFile
        )

    def add_module(self, key, node):
        self._nodes.add(node)
        if key in self._cache:
            if self.options.warn_on_duplicate_module:
                print(key, 'already added!')
                print('\tin \t', self._cache[key]['node'])
                print('\tout\t', node)
                print('\taka\t', self._cache[key]['aka'])
            self._cache[key]['aka'].append(node)
        else:
            self._cache[key] = {
                'key': key,
                'node': node,
                'aka': []
            }

    def build_module_list(self):
        for file in glob.glob(self.options.modules_path, recursive=True):
            node = File(file)
            if node.is_root:
                continue
            if node.is_test and not self.options.include_tests:
                continue

            key = node.basename
            self.add_module(key, node)

            if not node.is_init:
                paths = node.paths
                up = paths.pop(-1)
                # TODO: Use self.options.modules_path
                while up and up != '.' and up != 'dcm-intuition':
                    key = '{}.{}'.format(up, key)
                    self.add_module(key, node)
                    up = paths.pop(-1)

    def dump(self, outfile):
        with io.open(outfile, 'w') as f:
            print(self, file=f)
