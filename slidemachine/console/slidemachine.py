#!/usr/bin/env python3
__description__ = \
"""
Command line frontend for slidemachine.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-05-10"

import os, sys, argparse


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="render each layer of an inkscape svg file as an individual image file")
    parser.add_argument('svg_file', type=str, nargs=1,
                        help='Inkscape svg file with layers to write out')
    parser.add_argument('--root', type=str,default=None,
                        help='root for output files [default is svg_file]')
    parser.add_argument("--type",type=str,default="png",
                        help="type of output (svg,png,pdf)")

    args = parser.parse_args(argv)
    svg_file = args.svg_file[0]
    if args.root is None:
        output_root = svg_file[:-4]
    else:
        output_root = args.root

    out_type = args.type

    s = InkscapeSVG(svg_file)
    s.render_layers(output_root,format=out_type)


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    try:
        markdown_file = argv[0]
        reveal_html_file = argv[1]
    except IndexError:
        err = "Incorrect arguments. Usage:\n\n{}\n\n".format(__usage__)
        raise IndexError(err)

    sm = SlideMachine(markdown_file)
    html = sm.process()

    reveal = MergerRevealHtml(reveal_html_file)
    reveal.merge(html,"rock.html")


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description=__description__)

    # Positionals
    parser.add_argument("enrich_file",help="enrichment file from which features will be extracted")

    # Options
    parser.add_argument("-o","--outfile",help="output file",action="store",type=str,default=None)
    parser.add_argument("-n","--numcpu",help="number of cpus to use.  if -1, use all cpus",action="store",type=int,default=-1)

    parser.add_argument("-w","--window",help="Number of windows to use. -1 (default) creates sliding windows from 1 to the sequence length. 0 means do not use sliding windows",action="store",type=int,default=-1)

    parser.add_argument("-f","--flip",help="Do not calculate a flip pattern feature. This accounts for possible periodicity in a given feature across sequence.",action="store_false")

    parser.add_argument("-c","--column",help="Load weights from specified column (The first column is 0).  If -1 (default), do not read weights from the file.",action="store",type=int,default=-1)

    args = parser.parse_args(argv)

    # Figure out number of threads
    if args.numcpu == -1:
        num_threads = os.cpu_count()
    else:
        num_threads = args.numcpu

    # Figure out output files
    if args.outfile is None:
        base_file = os.path.split(args.enrich_file)[1]
        data_out_file = "{}_features.pickle".format(base_file)
    else:
        data_out_file = args.outfile

    if os.path.isfile(data_out_file):
        err = "out file '{}' already exists.\n".format(data_out_file)
        raise FileExistsError(err)

    # Figure out the column from which to pull weights:
    if args.column == -1:
        weight_column= None
    else:
        weight_column = args.column

    # calculate features
    features = hops.calc_features(args.enrich_file,
                                  num_threads=num_threads,
                                  use_flip_pattern=args.flip,
                                  use_sliding_windows=args.window,
                                  weight_column=weight_column)

    f = open(data_out_file,"wb")
    pickle.dump(features,f)
    f.close()

if __name__ == "__main__":
    main()
