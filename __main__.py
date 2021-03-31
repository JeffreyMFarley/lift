import configargparse
import os
import os.path

from lift.src.modules import Modules
from lift.src.options import Options
from lift.src.graph import ImportsGraph
from lift.src.traversal import Traversal


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def build_arg_parser():
    main_dir = os.path.dirname(__file__)

    p = configargparse.ArgParser(
        prog='lift_for_graphviz',
        description='select portions of DCM for graphviz',
        ignore_unknown_config_file_keys=True,
        default_config_files=[os.path.join(main_dir, 'config.ini')],
        args_for_setting_config_path=['-c', '--config'],
        args_for_writing_out_config_file=['--save-config']
    )
    p.add('--dump-config', action='store_true', dest='dump_config',
          help='dump config vars and their source')
    g = p.add_argument_group('Modules')
    g.add('--modules-path', default='./**/*.py',
          help='where the python files are located')
    g.add('--warn-on-duplicate-module', action='store_true',
          help='show warnings when there is a simple name collision')
    g = p.add_argument_group('Import Graph')
    g.add('--exclude-unused',
          help='a file of W0611 warnings, showing which imports are not used')
    g.add('--include-tests', action='store_true',
          help='include tests when making the import graph')
    g.add('--warn-on-ambiguous-edge', action='store_true',
          help='show warnings when there is more than one module match')
    g = p.add_argument_group('Traversal')
    g.add('--start-file', required=True,
          help="a file that lists the starting point(s) for the traversal")
    g.add('--end-file', required=True,
          help="a file that lists the ending point(s) for the traversal")
    g.add('--highlights-file',
          help="an optional file that calls out important modules")
    g.add('--max-depth', default=3, type=int,
          help='how many modules away from the entrypoint should be explored')
    g = p.add_argument_group('Output')
    g.add('--output-dot-starts',
          help="write the forward traversals to this directory")
    g.add('--output-dot-ends',
          help="write the backward traversals to this directory")
    g.add('--output-externals',
          help="list the package/external dependencies to this file")
    g.add('--output-imports-graph',
          help="write the import graph to this file")
    g.add('--output-modules',
          help="write the modules object to this file")
    return p


p = build_arg_parser()
opt = Options()
cfg = p.parse_args(namespace=opt)

if cfg.dump_config:
    print(p.format_values())

modules = Modules(cfg)

if cfg.output_modules:
    modules.dump(cfg.output_modules)

graph = ImportsGraph(cfg, modules)
if cfg.output_imports_graph:
    graph.dump(cfg.output_imports_graph)

if cfg.output_externals:
    graph.dump_externals(cfg.output_externals)

if cfg.output_dot_starts:
    os.makedirs(cfg.output_dot_starts, exist_ok=True)
    for i, s in enumerate(cfg.starts, 1):
        traversal = Traversal(cfg, graph, s, True)
        print('Output start [{}] {}...'.format(
            i, traversal.initial_node.modulename), end='')
        if len(traversal.relations):
            outfile = os.path.join(
                cfg.output_dot_starts,
                traversal.initial_node.basename + '.gv'
            )
            traversal.output_dot(outfile)
            print('{} nodes {} edges'.format(
                len(traversal.subgraphs.all_nodes),
                len(traversal.relations)
            ))
        else:
            print('no edges found. Skipping')

if cfg.output_dot_ends:
    os.makedirs(cfg.output_dot_ends, exist_ok=True)
    for i, k in enumerate(cfg.ends, 1):
        print('Output end [{}] {}...'.format(i, k), end='')
        traversal = Traversal(cfg, graph, k, False)
        if len(traversal.relations):
            outfile = os.path.join(
                cfg.output_dot_ends,
                k.replace('.', '_') + '.gv'
            )
            traversal.output_dot(outfile)
            print('{} nodes {} edges'.format(
                len(traversal.subgraphs.all_nodes),
                len(traversal.relations)
            ))
        else:
            print('no edges found. Skipping')
