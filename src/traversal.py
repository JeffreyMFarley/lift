from .edge import Edge
from .file import File
from .subgraphs import Subgraphs


# -----------------------------------------------------------------------------
# Traversal - tracks a path through the graph

class Traversal(object):
    def __init__(self, options, graph, initial_node, forward=True):
        self.graph = graph
        self.options = options
        self.initial_node = initial_node
        if initial_node in graph:
            self.initial_node = graph[initial_node].node

        self.forward = forward

        # Get the root nodes
        self.roots = [self.graph[x].node for x in options.starts]

        self.relations = self._find_paths()

        self.subgraphs = Subgraphs(self.relations)

        self.sinks = set(
            [r.end for r in self.relations if r.end in options.ends]
        )

    def _find_paths(self):
        if self.forward:
            paths = self.graph.find_all_paths(
                self.initial_node, self.options.ends
            )
        else:
            l = []
            l += self.graph.sources
            l += self.options.highlights
            
            paths = self.graph.find_all_paths_backward(
                self.initial_node, l
            )

        edges = set()

        for p in paths:
            start = None
            end = None

            if not self.forward:
                p.reverse()

            for step in p:
                if start is None:
                    start = step
                    continue
                elif end is None:
                    end = step

                edges.add(Edge(start, end))
                start = step
                end = None

        return edges

    def output_dot(self, outfile):
        visited_sg = set()

        def output_sg(f, sg, d, parent_label):
            if sg in visited_sg:
                return

            tabs = '\t' * d
            label = sg.label.replace(parent_label, '').strip('.')

            if sg.size == 1 and not sg.sg_children:
                n = sg.synecdoche
                print('{}{} [label="{}.{}" shape="component"]\n'.format(
                    tabs, n.gv_name, label, n.basename
                ), file=f)
            else:
                print('{}subgraph cluster_{} {{'.format(tabs, sg.id), file=f)
                print('{}\tlabel="{}"\n'.format(tabs, label), file=f)
                for csg in sg.sg_children:
                    output_sg(f, csg, d + 1, sg.label)
                for n in sg.nodes:
                    if n in self.roots:
                        print('{}\t{} [label="{}" style=filled fillcolor=gold]'.format(
                            tabs, n.gv_name, n.basename), file=f
                        )
                    elif n in self.options.highlights:
                        print('{}\t{} [label="{}" style=filled fillcolor=skyblue1]'.format(
                            tabs, n.gv_name, n.basename), file=f
                        )
                    else:
                        print('{}\t{} [label="{}"]'.format(tabs, n.gv_name, n.basename), file=f)
                print('{}}}\n'.format(tabs), file=f)

            visited_sg.add(sg)

        with open(outfile, 'w') as f:
            print('digraph imports {', file=f)
            print('\trankdir=LR;', file=f)
            print('\tcompound=true', file=f)
            print('\tnode [fontsize=10 shape="rect"]', file=f)
            print('\tedge [fontsize=9]', file=f)
            print('\n', file=f)

            for k in sorted(self.subgraphs.keys(), key=len):
                sg = self.subgraphs[k]
                output_sg(f, sg, 1, '')

            print('\n', file=f)
            for p in sorted(self.sinks):
                print(
                    '\t{} [label="{}" style=filled fillcolor=salmon]'.format(
                        p.replace('.', '_'), p),
                    file=f
                )

            print('\n', file=f)
            for r in self.relations:
                assert(isinstance(r.start, File))
                # Both are local modules
                if isinstance(r.end, File):
                    # sga = self.subgraphs.all_nodes[r.start]
                    # sgb = self.subgraphs.all_nodes[r.end]

                    a = r.start.gv_name
                    b = r.end.gv_name

                    comment = ''
                    if r.start.is_sibling(r.end):
                        comment = '/* sibling {} */'.format(
                            r.start.dotted_path)
                    elif r.start.is_ancestor(r.end):
                        comment = '/* family {} */'.format(
                            r.start.relative_label(r.end))
                    elif r.end.is_ancestor(r.start):
                        comment = '/* family {} */'.format(
                            r.end.relative_label(r.start))
                    else:
                        comment = '/* neighbors {} */'.format(
                            r.start.distance(r.end))

                    # if sga.size > 1 and sgb.size > 1:
                    #     a = sga.synecdoche.basename
                    #     b = sgb.synecdoche.basename
                    #     print(
                    #         '\t{} -> {} [ltail="cluster_{}"
                    #                      lhead="cluster_{}"]'.format(
                    #             a, b, sga.id, sgb.id
                    #         ),
                    #         file=f)
                    # else:
                    print('\t{} -> {}'.format(a, b), comment, file=f)
                else:
                    a = r.start.gv_name
                    b = r.end.replace('.', '_')
                    print('\t{} -> {} /* ext */'.format(a, b), file=f)

            print('}', file=f)
