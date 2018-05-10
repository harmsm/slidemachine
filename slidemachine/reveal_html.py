__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2018-05-09"
__usage__ = ""

import sys, re, os

class RevealHtml:

    def __init__(self,reveal_html_file):

        self._reveal_html_file = reveal_html_file
        self._read_reveal_file()

    def _read_reveal_file(self):
        """
        Read in a reveal html file, breaking at first tag with the attribute
        class="slides".  Populate self._reveal_top and self._reveal_bottom.
        Slide content will be inserted between these blocks.
        """

        search_pattern = re.compile("class=\"slides\"")

        filling_top = True
        top = []
        bottom = []
        with open(self._reveal_html_file,"r") as lines:
            for l in lines:

                if filling_top:
                    m = search_pattern.search(l)
                    if m:

                        attrib_end = m.end()
                        end_of_tag = re.search(">",l[attrib_end:]).end()

                        break_index = attrib_end + end_of_tag + 1
                        with_top = l[:break_index]

                        try:
                            with_bottom = l[break_index:]
                        except IndexError:
                            with_bottom = ""

                        top.append(with_top)
                        bottom.append("\n")
                        bottom.append(with_bottom)
                        filling_top = False

                        self._indent = (len(l) - len(l.lstrip()) + 2)*" "

                        continue
                    else:
                        top.append(l)
                else:
                    bottom.append(l)

        self._reveal_top = "".join(top)
        self._reveal_bottom = "".join(bottom)

    def merge(self,slides_html,output_file):

        if os.path.isfile(output_file):
            err = "{} already exists.\n".format(output_file)
            raise IOError(err)

        # Add appropriate indentation
        html = slides_html.split("\n")
        html = "\n".join(["{}{}".format(self._indent,h) for h in html])

        out = "{}{}{}".format(self._reveal_top,html,self._reveal_bottom)

        f = open(output_file,"w")
        f.write(out)
        f.close()
