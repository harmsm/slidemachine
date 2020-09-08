#!/usr/bin/env python3
__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2020-09-07"

import re

from .base import Processor

class FileProcessor(Processor):
    """
    Look for any html pointing to a local file and copy it into the target
    directory.
    """

    def process(self,line):
        """
        Look for local files and copy them into the output directory.
        """

        pattern_str = f"src=.?[\s\"].*?[\s\"]"
        p = re.compile(pattern_str)
        for m in p.finditer(line):

            file = m.group(0).split("src=")[1][1:-1]
            if file.startswith("http"):
                continue

            new_file = self._copy_file(file)

            re.sub(file,new_file,line)

        return line
