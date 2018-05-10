__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2018-05-09"
__usage__ = ""

import inkscape_render
import mistune
import sys, re, copy, os, random, string, shutil

def _split_string(s, delim, escape='\\', unescape=True):
    """
    Split a string on delim, properly accounting for escape. Not particularly
    fast, but I'm not anticipating parsing huge markdown files.

    Code taken from solution by Taha Jahangir on stackoverflow.

    https://stackoverflow.com/questions/18092354/python-split-string-without-splitting-escaped-character?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    """
    ret = []
    current = []
    itr = iter(s)
    for ch in itr:
        if ch == escape:
            try:
                # skip the next character; it has been escaped!
                if not unescape:
                    current.append(escape)
                current.append(next(itr))
            except StopIteration:
                if unescape:
                    current.append(escape)
        elif ch == delim:
            # split! (add current to the list and reset it)
            ret.append(''.join(current))
            current = []
        else:
            current.append(ch)
    ret.append(''.join(current))
    return ret

class SMMarkdown:
    """
    """

    def __init__(self,md_file,reveal_html_file):

        self._md_file = md_file
        self._reveal_html_file = reveal_html_file


        self._markdown = mistune.Markdown()
        self._indent = "    "

        self._read_md_file()
        self._read_reveal_file()

    def _read_md_file(self):
        """
        Read a markdown file, looking for a pattern that breaks markdown
        into slides.  Populates self._slides and self._transitions (one for
        each slide).
        """

        f = open(self._md_file,'r')
        self._md_file_content = f.readlines()
        f.close()

        slide_break = re.compile(">>>")

        self._slides = []
        slide_content = []
        for line in self._md_file_content:

            if slide_break.search(line):
                self._slides.append(copy.deepcopy(slide_content))
                slide_content = []
            else:
                slide_content.append(line)

        self._slides.append(copy.deepcopy(slide_content))
        self._transitions = [None for s in self._slides]


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


    def _process_image_lines(self,img_dir):
        """
        Look for lines like this:

        ![blah](img_file)

        Copies image file to img_dir and updates markdown.
        """

        img_pattern = re.compile("!\[")

        new_slides = []
        for slide in self._slides:

            tmp_lines = []
            for line in slide:

                new_line = line[:]
                if img_pattern.search(line):

                    tmp = _split_string(line,"(")[1]
                    img_file = _split_string(tmp,")")[0]

                    if os.path.isfile(img_file):
                        new_file = os.path.join(img_dir,
                                                os.path.split(img_file)[1])
                        shutil.copy(img_file,new_file)
                        new_line = re.sub(img_file,new_file,line)

                tmp_lines.append(new_line)

            new_slides.append(tmp_lines)

        self._slides = copy.deepcopy(new_slides)


    def _process_inkscape_lines(self,img_dir,img_format):
        """
        Looks for lines like this:

        ![inkscape](inkscape_file)layer1,layer2,layer3

        The list of layers on the right is optional.

        Renders each layer as an image, creating its own slide in the markdown.
        """

        inkscape_pattern = re.compile("!\[inkscape\]")

        new_slides = []
        new_transitions = []
        for slide in self._slides:

            tmp_lines = []
            inkscape_line = -1
            for i, line in enumerate(slide):

                if inkscape_pattern.search(line):

                    # quick sanity check
                    if inkscape_line >= 0:
                        err = "only one ![inkscape] tag allowed per slide\n"
                        raise ValueError(err)

                    tmp = _split_string(line,"(")[1]
                    tmp2 = _split_string(tmp,")")

                    svg_file = tmp2[0]

                    layer_list = None
                    if len(tmp2) > 1:
                        layer_list = tmp2[1].split(",")
                        layer_list = [l.strip() for l in layer_list]

                    out_root = os.path.split(svg_file)[1][:-4]
                    out_root = os.path.join(img_dir,out_root)

                    ink = inkscape_render.InkscapeSVG(svg_file,layer_list)
                    renders = ink.render_stack(out_root,format=img_format)

                    render_markdown = []
                    for r in renders:
                        render_markdown.append("![img]({})\n".format(r))

                    tmp_lines.append(render_markdown)

                    inkscape_line = i

                else:
                    tmp_lines.append(line)

            # If we found an inkscape line
            if inkscape_line >= 0:

                first_half = tmp_lines[:inkscape_line]
                second_half = tmp_lines[(inkscape_line+1):]

                for t in tmp_lines[inkscape_line]:
                    out = copy.deepcopy(first_half)
                    out.append(t)
                    out.extend(second_half)

                    new_slides.append(out)
                    new_transitions.append("data-transition=\"fade\"")

            else:
                new_slides.append(slide)
                new_transitions.append(None)

        self._slides = copy.deepcopy(new_slides)
        self._transitions = copy.deepcopy(new_transitions)

    def generate_output(self,out_file,img_dir,img_format):
        """
        """

        os.mkdir(img_dir)
        self._process_image_lines(img_dir)
        self._process_inkscape_lines(img_dir,img_format)

        out = [self._reveal_top]
        for i, s in enumerate(self._slides):
            if self._transitions[i] is not None:
                start = "{:}<section {:}>\n\n".format(self._indent,
                                                      self._transitions[i])
            else:
                start = "{:}<section>\n\n".format(self._indent)

            middle = self._markdown("".join(s))
            middle = middle.split("\n")
            middle = "".join(["  {:}{:}\n".format(self._indent,m) for m in middle])

            end = "{:}</section>\n\n".format(self._indent)

            out.append(start)
            out.append(middle)
            out.append(end)

        out.append(self._reveal_bottom)

        if os.path.isfile(out_file):
            err = "output file ({}) exists.\n".format(out_file)
            raise IOError(err)

        f = open(out_file,'w')
        f.write("".join(out))
        f.close()

def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    try:
        markdown_file = argv[0]
        reveal_html_file = argv[1]
    except IndexError:
        err = "Incorrect arguments. Usage:\n\n{}\n\n".format(__usage__)
        raise IndexError(err)

    sm = SMMarkdown(markdown_file,reveal_html_file)
    sm.generate_output("rock.html","test",img_format="png")

if __name__ == "__main__":
    main()
