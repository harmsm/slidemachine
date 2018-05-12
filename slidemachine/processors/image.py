#!/usr/bin/env python3
__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2018-05-09"

from .base import Processor


class ImageProcessor(Processor):
    """
    Process an image file. Looks for lines like this:

    ![sm.image](image_file) html_formatting_options

    and copies images into the target directory.
    """

    def process(self,line):
        """
        Process an image line.
        """

        # If the line does not match, return the original line
        if not self._pattern.match(line):
            return line

        image_file, args = self._parse_markdown_line(line,delim=None)

        new_file = self._copy_file(image_file)

        if args is not None:
            style = args
        else:
            style = ""

        out_line = "<img src=\"{}\" {} />".format(new_file,style)

        return out_line
