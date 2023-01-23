import glob
import io
import json
import os.path
import sys
from collections import namedtuple, OrderedDict

from .file import File, jsonEncoderFile
from .pymods import PYMODS

# -----------------------------------------------------------------------------
# Graph - contains the relation between files

ImportsGraphNode = namedtuple('ImportsGraphNode', [
    'node', 'imports', 'imported_by'
])


class ImportsGraph(object):
    def __init__(self, options, modules):
        self.modules = modules
        self.nodes = OrderedDict()
        self.options = options
        self.externals = OrderedDict()
        self.unused = set()

        if options.exclude_unused:
            if os.path.exists(options.exclude_unused):
                self.unused = self.parse_unused()
            else:
                print(options.exclude_unused,
                      'does not exist', file=sys.stderr)

        self.build_import_graph()

    def __contains__(self, key):
        k = str(key)
        return k in self.nodes or k in self.externals

    def __getitem__(self, key):
        k = str(key)
        if k in self.nodes:
            return self.nodes[k]
        elif k in self.externals:
            return self.externals[k]

        return None

    def __repr__(self):
        o = self._to_json(self.nodes)
        return json.dumps(
            o, indent=2, sort_keys=True, default=jsonEncoderFile
        )

    @property
    def sources(self):
        ''' find all the nodes that are not imported '''
        candidates = set()
        for v in self.nodes.values():
            if len(v.imported_by) == 0:
                candidates.add(v.node)

        return [str(x) for x in candidates if not x.is_init and not x.is_root]

    # --------------------------------------------------------------------------
    # Traversals

    def BFS(self, start, group, visited, forward=True):
        queue = []
        queue.append(start)
        while queue != []:
            node = queue.pop(0)
            visited.add(node)
            group.add(node)

            ign = self[node]
            if ign:
                edges = ign.imports if forward else ign.imported_by
                for successor in edges:
                    if successor not in visited and successor not in queue:
                        queue.append(successor)

    def DFS(self, start, visited, order, forward=True):
        visited.add(start)
        ign = self[start]
        if ign:
            edges = ign.imports if forward else ign.imported_by
            for successor in edges:
                if successor not in visited:
                    visited.add(successor)
                    self.DFS(successor, visited, order, forward)
        order.append(start)

    # --------------------------------------------------------------------------
    # Building

    def add_node(self, node):
        assert(isinstance(node, File))
        self.nodes[node.full_path] = ImportsGraphNode(node, set(), set())

    def add_edge(self, node, module_key):
        assert(isinstance(node, File))
        v = self[node.full_path]

        # Skip Python modules
        if module_key in PYMODS:
            return

        # Skip unused
        if (node.full_path, module_key) in self.unused:
            # print('skipping', node.full_path, module_key)
            return

        # Is this module local?
        entry = self.modules[module_key]
        if entry:
            other = self.resolve_entry(node, entry)
            v.imports.add(other)

            if other not in self:
                self.add_node(other)
            oe = self[other.full_path]
            oe.imported_by.add(node)
        else:
            if module_key not in self.externals:
                self.externals[module_key] = ImportsGraphNode(
                    module_key, set(), set()
                )
            self.externals[module_key].imported_by.add(node)
            v.imports.add(module_key)

    def build_import_graph(self):
        import ast

        for file in glob.glob(self.options.modules_path, recursive=True):
            node = File(file)
            if node.is_root:
                continue
            if node.is_test and not self.options.include_tests:
                continue

            self.add_node(node)

            with io.open(file, 'r', errors='ignore') as file_handle:
                content = file_handle.read()
            try:
                parsed = ast.parse(content)
            except SyntaxError as se:
                print(file, se, file=sys.stderr)
                continue

            for ast_node in ast.walk(parsed):
                if isinstance(ast_node, ast.Import):
                    for name in ast_node.names:
                        self.add_edge(node, name.name)
                elif isinstance(ast_node, ast.ImportFrom) and ast_node.module:
                    # assert ast_node.module
                    self.add_edge(node, ast_node.module)

    def parse_unused(self):
        unused = set()

        with io.open(self.options.exclude_unused, 'r') as f:
            for line in f:
                tokens = line.strip().split(' ')
                assert(tokens[1] == 'W0611')

                # dcm-intuition/integration/broker/order_service.py:8:1:
                a = './' + tokens[0].split(':')[0]

                # 'broker.flextrade.business_operation.BusinessOperation'
                b = tokens[2].strip("'")

                unused.add((a, b))

        return unused

    def resolve_entry(self, node, entry):
        # Check for aka
        if len(entry['aka']) == 0:
            return entry['node']

        if self.options.warn_on_ambiguous_edge:
            print(node, 'has ambiguous edge', entry['key'])

        candidates = [entry['node'], *entry['aka']]
        min_dist = 100000
        min_node = None

        for x in candidates:
            d = node.distance(x)
            if self.options.warn_on_ambiguous_edge:
                print('\t' + str(x), d)
            if d < min_dist:
                min_dist = d
                min_node = x
            elif d == min_dist and x.is_init:
                min_node = x

        if self.options.warn_on_ambiguous_edge:
            print('\tchoosing', str(min_node))
        return min_node

    # --------------------------------------------------------------------------
    # Queries

    def connected(self, candidates, forward=True):
        visited = set()
        groups = {}
        for node in sorted(candidates):
            if node not in visited:
                group = set()
                self.BFS(node, group, visited, forward)
                groups[node] = group
        return groups

    def find_all_paths(self, start, ends, path=[], depth=0):
        path = path + [start]
        if start in ends:
            return [path]

        if depth > self.options.max_depth:
            return []

        curr = self[start]
        if curr is None:
            return []

        paths = []
        for vertex in curr.imports:
            if vertex not in path:
                extended_paths = self.find_all_paths(vertex,
                                                     ends,
                                                     path,
                                                     depth + 1)
                for p in extended_paths:
                    paths.append(p)

        return paths

    def find_all_paths_backward(self, end, starts, path=[], depth=0):
        path = path + [end]
        if end in starts:
            return [path]

        if depth > self.options.max_depth:
            return []

        paths = []

        curr = self[end]
        if not curr:
            print(end, 'not found!')
            return []

        for vertex in curr.imported_by:
            if vertex not in path:
                extended_paths = self.find_all_paths_backward(vertex,
                                                              starts,
                                                              path,
                                                              depth + 1)
                for p in extended_paths:
                    paths.append(p)

        return paths

    # --------------------------------------------------------------------------
    # Output

    def _to_json(self, ign_dict):
        o = []
        for k in sorted(ign_dict):
            _, imports, imported_by = ign_dict[k]
            o.append({
                'file': k,
                'imports': sorted(list(imports)),
                'imported_by': sorted(list(imported_by))
            })
        return o

    def dump(self, outfile):
        with io.open(outfile, 'w') as f:
            print(self, file=f)

    def dump_externals(self, outfile):
        o = self._to_json(self.externals)
        with io.open(outfile, 'w') as f:
            json.dump(o, f, indent=2, sort_keys=True, default=jsonEncoderFile)
