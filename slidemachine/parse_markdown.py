__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2018-05-09"
__usage__ = ""

import inkscape_render
import mistune
import sys, re, copy, os, random, string, shutil, hashlib


def _split_string(s, delim, escape='\\', unescape=True):
    """
    Split a string on delim, properly accounting for escape. Not particularly
    fast, but I'm not anticipating parsing huge markdown files.

    Code taken from solution by Taha Jahangir on stackoverflow.

    https://stackoverflow.com/questions/18092354/python-split-string-without-splitting-escaped-character
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

class SlideMachine:
    """
    """

    def __init__(self,md_file,img_dir="img",slide_break=">>>"):

        self._md_file = md_file
        self._img_dir = img_dir

        self._slide_break = slide_break
        self._markdown = mistune.Markdown()

        self._md_file_content = None
        self._html = None

        # Dictionary of every image seen during processing. key is the
        # md5 hash of the file; value is the filename.  This is used to
        # minimize the number of files in the final output.  Only unique
        # files are copied into _img_dir
        self._img_seen_dict = {}

    def _read_md_file(self):
        """
        Read a markdown file, looking for a pattern that breaks markdown
        into slides.  Populates self._slides and self._transitions (one for
        each slide).
        """

        # Read contents of md file as a set of lines
        try:
            f = open(self._md_file,'r')
            self._md_file_content = f.readlines()
            f.close()
        except AttributeError:
            err = "No markdown file specified.\n"
            raise ValueError(err)

        # pattern for slide break
        slide_break = re.compile(self._slide_break)

        # Break markdown into individual slides
        self._slides = []
        slide_content = []
        for line in self._md_file_content:

            if slide_break.search(line):
                self._slides.append(copy.deepcopy(slide_content))
                slide_content = []
            else:
                slide_content.append(line)
        self._slides.append(copy.deepcopy(slide_content))

        # Create transitions for slides (None)
        self._transitions = [None for s in self._slides]

    def _process_image(self,img_file):
        """
        Copies img_file into the img_dir, returning he new file name as a
        string.  If multiple lines in the markdown point to the same image file
        (even if they have different names) the file is only copied once.  If
        two different files have the same name, the second file renamed to
        avoid the conflict.
        """

        # Make sure the output directory is real before parsing
        try:
            if not os.path.isdir(self._img_dir):
                err = "output ({}) is not a directory\n".format(self._img_dir)
                raise ValueError(err)
        except AttributeError:
            err = "output directory not specified.\n"
            raise ValueError(err)

        # Determine the md5 hash of the input file
        hash_md5 = hashlib.md5()
        with open(img_file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        file_hash = hash_md5.hexdigest()

        # see if this image has been seen before
        try:
            new_file = self._img_seen_dict[file_hash]

        # if not, process it
        except KeyError:

            img_root = os.path.split(img_file)[1]
            new_file = os.path.join(self._img_dir,img_root)

            # name conflict, add counter until no conflict
            counter = 0
            while os.path.isfile(new_file):
                new_root = "{:05d}_{:s}".format(counter,img_root)
                new_file = os.path.join(self._img_dir,new_root)
                counter += 1

            self._img_seen_dict[file_hash] = new_file

            shutil.copy(img_file,new_file)

        return new_file

    def _process_image_lines(self):
        """
        Look for lines like this:

        ![blah](img_file)

        Process the image, copying it into img_dir.
        """

        img_pattern = re.compile("!\[")

        new_slides = []
        for slide in self._slides:

            tmp_lines = []
            for line in slide:

                new_line = copy.deepcopy(line)
                if img_pattern.search(line):

                    # Split on "(" and ")" in markdown. Using _split_string
                    # rather than the normal str.split in case we have someone
                    # using \( in their filenames.
                    tmp = _split_string(line,"(")[1]
                    img_file = _split_string(tmp,")")[0]

                    # If the image file is actually a file (rather than, say,
                    # a url...)
                    if os.path.isfile(img_file):

                        # Process image (copy, etc.)
                        new_file = self._process_image(img_file)

                        # Update the markdown so it points to the image file
                        # in the image directory
                        new_line = re.sub(img_file,new_file,line)

                tmp_lines.append(new_line)

            new_slides.append(tmp_lines)

        self._slides = copy.deepcopy(new_slides)

    def _process_inkscape_lines(self,img_format):
        """
        Looks for lines like this:

        ![inkscape](inkscape_file)100,001,111

        Renders each layer as an image, creating its own slide in the markdown.

        The list of layer configurations on the right is optional. Those strings
        specify the layer configurations to render.  The example above would
        render bottom layer alone, the top layer alone, and then all three
        layers together, in that order.  It would then create three slides,
        one for each render.  The length of each 0/1 string must be the same as
        the number of layers in the input inkscape file.  If no configurations
        are specified, the renderer will build the layers sequentially from
        bottom to top (i.e. 1000, 1100, 1110, 1111).
        """

        inkscape_pattern = re.compile("!\[inkscape\]")

        new_slides = []
        new_transitions = []
        for slide in self._slides:

            tmp_lines = []
            inkscape_line = -1
            for i, line in enumerate(slide):

                # If we've got an inkscape tag...
                if inkscape_pattern.search(line):

                    # quick sanity check
                    if inkscape_line >= 0:
                        err = "only one ![inkscape] tag allowed per slide\n"
                        raise ValueError(err)

                    tmp = _split_string(line,"(")[1]
                    tmp2 = _split_string(tmp,")")

                    # Get svg file
                    svg_file = tmp2[0]

                    # If there's leftover junk, treat it as layer configs
                    layer_configs = None
                    if len(tmp2) > 1:
                        layer_configs = tmp2[1].split(",")
                        layer_configs = [l.strip() for l in layer_configs]


                    # Create temporary output directory
                    id = "".join([random.choice(string.ascii_letters)
                                  for i in range(10)])
                    tmp_dir = "tmp_{}".format(id)
                    os.mkdir(tmp_dir)

                    # Render layers according to what's in layer_configs
                    out_root = os.path.split(svg_file)[1][:-4]
                    out_root = os.path.join(tmp_dir,out_root)

                    ink = inkscape_render.InkscapeSVG(svg_file)
                    renders = ink.render_layers(out_root,
                                                format=img_format,
                                                layer_configs=layer_configs)

                    # Process the final, rendered files
                    render_markdown = []
                    for r in renders:
                        img_name = self._process_image(r)
                        render_markdown.append("![img]({})\n".format(img_name))

                    # Nuke temporary files
                    shutil.rmtree(tmp_dir)

                    tmp_lines.append(render_markdown)
                    inkscape_line = i

                else:
                    tmp_lines.append(line)

            # If we found an inkscape line on this slide, expand it out into
            # as many slides as rendered layers
            if inkscape_line >= 0:

                # Break slide in half at the inkscape line
                first_half = tmp_lines[:inkscape_line]
                second_half = tmp_lines[(inkscape_line+1):]

                # Now build a new slide for each rendered file
                for i, t in enumerate(tmp_lines[inkscape_line]):
                    out = copy.deepcopy(first_half)
                    out.append(t)
                    out.extend(second_half)

                    new_slides.append(out)
                    new_transitions.append("data-transition=\"none\"")

            else:
                new_slides.append(slide)
                new_transitions.append(None)

        self._slides = copy.deepcopy(new_slides)
        self._transitions = copy.deepcopy(new_transitions)

    def process(self,img_format="png"):
        """
        """

        # Try to make output directory. Will fail if it already exists
        os.mkdir(self._img_dir)

        # Read markdown file
        self._read_md_file()

        # Pre-treat markdown, creating blocks of slides
        self._process_image_lines()
        self._process_inkscape_lines(img_format)

        # Create <section> html breaks that can be read by reveal.js
        out = []
        for i, s in enumerate(self._slides):
            if self._transitions[i] is not None:
                start = "<section {:}>\n\n".format(self._transitions[i])
            else:
                start = "<section>\n\n"

            middle = self._markdown("".join(s))
            middle = middle.split("\n")
            middle = "".join(["  {:}\n".format(m) for m in middle])

            end = "</section>\n\n"

            out.append(start)
            out.append(middle)
            out.append(end)

        self._html = "".join(out)

        return self._html

    @property
    def markdown(self):
        """
        Input markdown.
        """

        if self._md_file_content is None:
            return None

        return "".join(self._md_file_content)

    @property
    def html(self):
        """
        Final html.
        """

        return self._html



class MergerRevealHtml:

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


if __name__ == "__main__":
    main()
