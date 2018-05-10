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

    parser = argparse.ArgumentParser(description="render layers of an inkscape svg file as an individual image file")
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


if __name__ == "__main__":
    main()
