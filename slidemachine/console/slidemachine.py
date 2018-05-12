#!/usr/bin/env python3
__description__ = \
"""
Command line frontend for slidemachine.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-05-10"

from .. import slidemachine

import os, sys, argparse


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="generate reveal.js html from a markdown file with generator tags")
    parser.add_argument('markdown_file', type=str, nargs=1,
                        help='markdown file to process')
    parser.add_argument('--html', type=str,default=None,
                        help='reveal html file in which to insert slides')
    parser.add_argument("--out",type=str,default="index.html",
                        help="html file to write output")
    parser.add_argument("--config",type=str,default=None,
                        help="configuration file (json)")



    args = parser.parse_args(argv)
    markdown_file = markdown_file[0]
    #if args.root is None:
    #    output_root = svg_file[:-4]
    #else:
    #    output_root = args.root

    #out_type = args.type

    s = slidemachine.SlideMachine(markdown_file,
                                  target_dir=args.target_dir,
                                  json_file=args.json_file)

    s.process(output_file=args.out,
              reveal_html_file=args.html)


if __name__ == "__main__":
    main()
