#!/usr/bin/env python3
__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2020-09-07"

import re

from .base import Processor

class CustomMDProcessor(Processor):
    """
    Do some custom markdown processing.
    """

    def process(self,line):
        """
        Apply some custom markdown tags.

        @something@ gives <small>something</small>
        """

        pattern = re.compile("@.*?@")
        matches = pattern.findall(line)
        for m in matches:
            replacement = r"<small>{}</small>".format(re.escape(m[1:-1]))
            line = pattern.sub(replacement,line)

        return line
