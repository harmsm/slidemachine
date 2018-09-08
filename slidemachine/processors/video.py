#!/usr/bin/env python3
__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2018-05-09"

from .base import Processor

class VideoProcessor(Processor):
    """
    Process a video file. Looks for lines like this:

    ![sm.video](video_file) video options

    and copies videos into the target directory.
    """

    def process(self,line):
        """
        Process a video line.
        """

        # If the line does not match, return the original line
        if not self._pattern.match(line):
            return line

        video_file, args = self._parse_markdown_line(line,delim=None)

        new_file = self._copy_file(video_file)

        if args is not None:
            style = args
        else:
            style = ""

        out_lines = ["<video {}>".format(style)]
        out_lines.append("<source data-src=\"{}\" />".format(new_file))
        out_lines.append("</video>")

        return "".join(out_lines)
