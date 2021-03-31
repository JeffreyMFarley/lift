import itertools

from .file import File


class Subgraph(object):
    id_iter = itertools.count(100, 10)

    def __init__(self, label, manager):
        assert(label)
        self.id = next(self.id_iter)
        self.label = label
        self.manager = manager
        self.nodes = set()
        self.sg_children = []
        self.synecdoche = None

    @property
    def size(self):
        return len(self.nodes)

    def add(self, node):
        assert(isinstance(node, File))
        self.nodes.add(node)
        self.manager.all_nodes[node] = self
        if node.is_init or self.synecdoche is None:
            self.synecdoche = node

    def add_edge(self, member, other, sg_other):
        pass

    def add_subgraph_child(self, child):
        self.sg_children.append(child)


class Subgraphs(dict):
    def __init__(self, relations):
        self.all_nodes = {}

        self.build_subgraphs(relations)
        self.build_hierarchy()

    def __missing__(self, key):
        value = self[key] = Subgraph(key, self)
        return value

    def build_hierarchy(self):
        # Build hierarchy
        # Sort paths in longest to shortest order
        rev_paths = sorted(self.keys(), key=len, reverse=True)

        while rev_paths:
            # pop the longest path
            y = self[rev_paths.pop(0)]

            # looking through the rest of the list,
            # starting longest moving shortest
            for k in rev_paths:
                x = self[k]
                xl = x.label
                yl = y.label
                if xl in yl and x.synecdoche.is_ancestor(y.synecdoche) == 1:
                    x.add_subgraph_child(y)
                    break  # stop finding ancestors of this element

    def build_subgraphs(self, relations):
        for r in relations:
            rpath = r.start.dotted_path
            self[rpath].add(r.start)

            if isinstance(r.end, File):
                rpath = r.end.dotted_path
                self[rpath].add(r.end)
