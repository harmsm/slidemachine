__description__ = \
"""
Render the layers in an Inkscape-generated svg file into a collection of
images.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-05-09"

import sys, os, re, subprocess, copy, random, string, argparse
from xml.dom import minidom

class InkscapeSVG:
    """
    Class that holds an inkscape svg file and manipulates layers.
    """

    def __init__(self,svg_file,layer_list=None):

        self._svg_file = svg_file
        self._layer_list = layer_list

        # Read in the svg file
        f = open(svg_file)
        self._original_svg = f.read()
        f.close()

        self._current_svg = copy.deepcopy(self._original_svg)

        # Extract layers from file
        self._parse_layers()

        # patterns to find "g" tags and style attributes
        self._before_pattern = re.compile("<g")
        self._after_pattern = re.compile(">")
        self._style_pattern = re.compile("style=")

    def _parse_layers(self):
        """
        Create a list of layers in the svg file.
        """

        # Read the svg file xml
        xmldoc = minidom.parseString(self._current_svg)

        # Make list of groups
        group_list = xmldoc.getElementsByTagName('g')

        # Go through each group
        include_in_stack = []
        for g in group_list:

            # See if this is a layer (inkscape:groupmode="layer")
            try:
                group_type = g.attributes['inkscape:groupmode'].value
                if group_type != "layer":
                    continue
            except KeyError:
                continue

            # Grab the layer id
            layer_id = g.attributes['id'].value

            # If the user specifies a list of layers to take, grab any layer
            # that matches
            if self._layer_list is not None:
                if layer_id in self._layer_list:
                    include_in_stack.append(layer_id)
                else:
                    continue

            # If the user does not specify a list of layers, only take those
            # that are visible
            else:

                try:
                    style = g.attributes['style'].value

                    # Hidden layer -- ignore it
                    if style == "display:none":
                        continue

                except KeyError:
                    pass

                include_in_stack.append(layer_id)

        # If a layer list is specified, make sure that all of those layers were
        # found.  Sort them into the same order as layer_list.
        if self._layer_list is not None:
            layer_list_to_sort = copy.deepcopy(self._layer_list)
            found_layers_to_sort = copy.deepcopy(include_in_stack)

            layer_list_to_sort.sort()
            found_layers_to_sort.sort()

            if len(layer_list_to_sort) != len(found_layers_to_sort):
                err = "Not all layers found.\n"
                raise ValueError(err)

            score = sum([layer_list_to_sort[i] == l
                         for i, l in enumerate(found_layers_to_sort)])
            if score != len(layer_list_to_sort):
                err = "Duplicate layers found.\n"
                raise ValueError(err)

            self._include_in_stack = copy.deepcopy(include_in_stack)

        # If no layer list is specified, show the layers in reverse order
        # relative to when found in the file, as Inkscape stores the top layer
        # at the bottom of the file.
        else:
            include_in_stack.reverse()
            self._include_in_stack = copy.deepcopy(include_in_stack)


    def _toggle_layer(self,layer_id,layer_on):
        """
        Edit an svg_string so that layer_id is visible (layer_on = True)
        or invisible (layer_on = False).
        """

        # Set search strings appropriately for turning on or off
        if layer_on:
            find_string = "display:none"
            replace_string = "display:inline"
        else:
            find_string = "display:inline"
            replace_string = "display:none"

        # Create string for looking for layer_id
        layer_string = "id=\"{}\"".format(layer_id)

        # Split svg text into text before the layer_id and after the
        # layer_id.
        layer_pattern = re.compile("id=\"{}\"".format(layer_id))
        before, after = layer_pattern.split(self._current_svg)

        # Take the last tag start from before the layer_id
        tag_start = None

        # Iterate through all matches --> tag_start will be last match by
        # the end of loop
        for tag_start in self._before_pattern.finditer(before):
            pass

        if tag_start is None:
            err = "mangled xml\n"
            raise ValueError(err)

        tag_start = tag_start.end()

        # Take the first tag from after the layer id
        tag_end = self._after_pattern.search(after).start()

        # Replace style attribute if before the layer_id
        style_attribute_found = False
        if self._style_pattern.search(before[tag_start:]):

            b1 = before[:tag_start]
            b2 = before[tag_start:]
            b2 = re.sub(find_string,replace_string,b2)

            before = "{}{}".format(b1,b2)

            style_attribute_found = True

        # Replace style attribute if after the layer_id
        if self._style_pattern.search(after[:tag_end]):

            # Multiple style attributes in the same tag!
            if style_attribute_found:
                err = "mangled xml.\n"
                raise ValueError(err)

            a1 = after[:tag_end]
            a2 = after[tag_end:]
            a1 = re.sub(find_string,replace_string,a1)

            after = "{}{}".format(a1,a2)

            style_attribute_found = True

        # If there is not style attribute, make one
        if not style_attribute_found:

            a1 = after[:tag_end]
            a2 = after[tag_end:]

            after = "{}\n     style=\"{}\"{}".format(a1,replace_string,a2)

        # Reassemble output string
        self._current_svg = "{}{}{}".format(before,layer_string,after)

    def _write_file(self,output_file):

        if os.path.isfile(output_file):
            err = "output file ({}) already exists\n".format(output_file)
            raise ValueError(err)

        f = open(output_file,"w")
        f.write(self._current_svg)
        f.close()


    def render(self,output_file,text_to_path=True):
        """
        Render the current state of the svg string as a flat file.  Can
        write to plain svg, pdf, or png.  Uses inkscape.
        """

        extension = output_file[-3:]

        # Parse the output flag
        output_flags = {"svg":"--export-plain-svg={}",
                        "pdf":"--export-pdf={}",
                        "png":"--export-png={}"}

        try:
            output_flag = output_flags[extension]
        except KeyError:
            err = "file type of \"{}\" not recognized\n".format(output_file)
            err = err + "\n\nfile must be one of\n\n"
            for k in output_flags.keys():
                err += "    {}\n".format(k)

        if os.path.isfile(output_file):
            err = "output file ({}) already exists\n".format(output_file)
            raise ValueError(err)

        # Write out the svg file to a temporary file
        rand_id = "".join([random.choice(string.ascii_letters)
                           for i in range(10)])
        tmp_file = "{}.svg".format(rand_id)
        self._write_file(tmp_file)

        # Construct an inkscape command that renders the svg to the output
        # file
        cmd = ["inkscape","-z","--file={}".format(tmp_file)]
        if text_to_path:
            cmd.append("--export-text-to-path")
        cmd.append(output_flag.format(output_file))

        # Run the command
        result = subprocess.run(cmd)

        # Make sure the command wrote an output error
        if not os.path.isfile(output_file):
            err = "Unknown error. No file written out.\n"
            raise IOError(err)

        os.remove(tmp_file)

    def write(self,output_file):
        """
        Write the current svg to an inkscape svg file.
        """

        self._write_file(output_file)

    def render_stack(self,output_root,format="svg",text_to_path=True):
        """
        Render the stack of layers.
        """

        current_state = copy.deepcopy(self._current_svg)

        # Start by turning all layers off
        for layer_id in self._include_in_stack:
            self._toggle_layer(layer_id,layer_on=False)

        for layer_id in self._include_in_stack:
            self._toggle_layer(layer_id,layer_on=True)
            out_name = "{}_{}.{}".format(output_root,layer_id,format)
            self.render(out_name,text_to_path)

        self._current_svg = copy.deepcopy(current_state)

    @property
    def svg(self):
        """
        svg text file.
        """

        return self._current_svg

    @property
    def layers(self):
        """
        list of layers to render.
        """

        return self._layer_list

def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="render each layer of an inkscape svg file as an individual image file")
    parser.add_argument('svg_file', type=str, nargs=1,
                        help='Inkscape svg file with layers to write out')
    parser.add_argument('--root', type=str,default=None,
                        help='root for output files [default is svg_file]')
    parser.add_argument("--type",type=str,default="svg",
                        help="type of output (svg,png,pdf)")
    parser.add_argument("--layers",type=str,default=None,
                        help="file with list of layers to include")

    args = parser.parse_args()
    svg_file = args.svg_file[0]
    if args.root is None:
        output_root = svg_file[:-4]
    else:
        output_root = args.root

    out_type = args.type

    layer_list = None
    if args.layers is not None:
        
        f = open(args.layers,'r')
        lines = f.readlines()
        f.close()

        layer_list = [l.strip() for l in lines
                      if l.strip() != "" and not l.startswith("#")]

    s = InkscapeSVG(svg_file,layer_list=layer_list)
    s.render_stack(output_root,format=out_type)

if __name__ == "__main__":
    main()
