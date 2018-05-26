#!/usr/bin/env python3
__description__ = \
"""
Class for manipulating and rendering the layers in an Inkscape-generated svg
file.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-05-09"

from .base import Processor

import sys, os, re, subprocess, copy, random, string, shutil
from xml.dom import minidom

class InkscapeSVG:
    """
    Class that holds an inkscape svg file and allows manipulation of layers.
    """

    def __init__(self,svg_file):

        self._svg_file = svg_file

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
        self._layer_list = []
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

            self._layer_list.append(layer_id)


    def _toggle_layer(self,layer_id,layer_on):
        """
        Edit the svg file so that layer_id is visible (layer_on = True)
        or invisible (layer_on = False).
        """

        # Sanity check
        if layer_id not in self._layer_list:
            err = "layer ({}) not in file.\n".format(layer_id)
            raise ValueError(err)

        layer_on = bool(layer_on)

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

        # Iterate through all matches --> tag_start will be last match by
        # the end of loop
        tag_start = None
        for tag_start in self._before_pattern.finditer(before):
            pass

        # If we did not actually find the beginning of the tag
        if tag_start is None:
            err = "Mangled xml.\n"
            raise ValueError(err)

        # Record the position of that tag
        tag_start = tag_start.end()

        # Take the first tag terminator that occurs after the layer_id
        tag_end = self._after_pattern.search(after).start()

        # Replace style attribute with appropriate transition.

        # If before the layer_id
        style_attribute_found = False
        if self._style_pattern.search(before[tag_start:]):

            b1 = before[:tag_start]
            b2 = before[tag_start:]
            b2 = re.sub(find_string,replace_string,b2)

            before = "{}{}".format(b1,b2)

            style_attribute_found = True

        # If after the layer_id
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

        # If there was not a style attribute already, make one
        if not style_attribute_found:

            a1 = after[:tag_end]
            a2 = after[tag_end:]

            after = "{}\n     style=\"{}\"{}".format(a1,replace_string,a2)

        # Reassemble output string
        self._current_svg = "{}{}{}".format(before,layer_string,after)

    def set_layer_config(self,layer_config):
        """
        Set the layers according to the list-like object in layer_config.
        Must have one entry per layer that can be interpreted as bool.
        False means that layer is off, True means that layer is on.
        Returns a string representation of the layer config as 0s and 1s.

        Examples:

        layer_config = "0010" would turn on the third layer of four (counting
        from the bottom of the stack)

        layer_config = [1,1,1,1,1,1] would turn on all 6 layers of 6

        """

        # Sanity check
        if len(self._layer_list) != len(layer_config):
            err = "layer_config must have the same length as the number of layers\n"
            raise ValueError(err)

        # If user specified string like 100101, convert to int
        if type(layer_config) is str:
            layer_config = [int(c) for c in list(layer_config)]

        # Convert to list of bool
        processed_config = [bool(c) for c in list(layer_config)]

        # Set layers according to config
        for i in range(len(self._layer_list)):
            self._toggle_layer(layer_id=self._layer_list[i],
                               layer_on=processed_config[i])

        # Create a string representation of the configuration
        config_name = "".join(["{}".format(int(c)) for c in processed_config])

        return config_name

    def write_inkscape_svg(self,output_file,force=False):
        """
        Write the current svg to an inkscape svg file.  Will not overwrite
        an existing file unless force == True.
        """

        if os.path.isfile(output_file) and not force:
            err = "output file ({}) already exists\n".format(output_file)
            raise ValueError(err)

        if output_file[-4:] != ".svg":
            err = "output file must be an svg file\n".format(output_file)
            raise ValueError(err)

        f = open(output_file,"w")
        f.write(self._current_svg)
        f.close()

    def render(self,output_file,text_to_path=True):
        """
        Render the current state of the svg string as an image file using
        inkscape.

        output_file: filename to write.  the type of file is inferred from the
                     extension on the file.  Can be .svg, .png, or .pdf.  An
                     svg file will be a "plain" svg rather than an inkscape
                     svg.
        text_to_path: whether to convert text in svg to paths
        """

        # Figure out what kind of file we want to write
        extension = output_file[-3:]

        # Map output type to inkscape flag
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

        # Don't overwrite a file if it already exists
        if os.path.isfile(output_file):
            err = "output file ({}) already exists\n".format(output_file)
            raise IOError(err)

        # Write out the inkscape svg file to a temporary file
        rand_id = "".join([random.choice(string.ascii_letters)
                           for i in range(10)])
        tmp_file = "{}.svg".format(rand_id)
        self.write_inkscape_svg(tmp_file)

        # Construct an inkscape command that renders the svg to the output
        # file
        cmd = ["inkscape","-z","--file={}".format(tmp_file)]
        cmd.append("--export-area-page")
        if text_to_path:
            cmd.append("--export-text-to-path")
        cmd.append(output_flag.format(output_file))

        # Run the command
        result = subprocess.check_output(cmd)

        # Make sure the command wrote an output error
        if not os.path.isfile(output_file):
            err = "Unknown error. No file written out.\n"
            raise IOError(err)

        # Clean up
        os.remove(tmp_file)

    def render_layers(self,output_root,
                      format="png",
                      text_to_path=True,
                      layer_configs=None):
        """
        Render the layers in the specified output format. Returns a list of the
        rendered files.

        output_root: root for output file name
        format: svg, png, pdf
        text_to_path: whether to render text as paths in final render
        layer_configs: list of layer configurations to render.  If None,
                       render will go like 100, 110, 111 ... meaning that the
                       each render will have one more layer turned on.

        """

        # Save backup of current state -- will return to this after
        # writing out
        current_state = copy.deepcopy(self._current_svg)

        if layer_configs is None:

            layer_configs = self.default_layer_render

        else:

            # sanity checks on user-generated configs

            try:
                len(layer_configs)
            except TypeError:
                err = "layer_configs must be a list-like object\n"
                raise ValueError(err)

            if len(layer_configs) == 0:
                err = "layer_configs must have at least one configuration\n"
                raise ValueError(err)

        configs_seen = {}

        # Go through each layer configuration
        rendered = []
        for config in layer_configs:

            # Set the layer state
            config_name = self.set_layer_config(config)

            # Render output
            out_name = "{}_{}.{}".format(output_root,config_name,format)

            # Only render if we haven't already rendered this configuration
            try:
                configs_seen[out_name]
            except KeyError:
                configs_seen[out_name] = 0
                self.render(out_name,text_to_path)

            # Record that we rendered this layer
            rendered.append(out_name)

        # Restore to pristine state
        self._current_svg = copy.deepcopy(current_state)

        # Return list of rendered files
        return rendered

    @property
    def svg(self):
        """
        svg as text.
        """

        return self._current_svg

    @property
    def layers(self):
        """
        List of layers to render.
        """

        return self._layer_list

    @property
    def default_layer_render(self):
        """
        Default set of layers to render.
        """

        # Construct a default set of layer configurations going like:
        #   100, 110, 111
        # This starts with layer one, then layer one+two, then layer
        # one+two+three

        layer_configs = []

        config = [False for s in self._layer_list]
        for i in range(len(self._layer_list)):
            config[i] = True

            layer_configs.append(copy.deepcopy(config))

        return layer_configs


class InkscapeProcessor(Processor):
    """
    Process and inkscape SVG file, creating individual slides from layers.

    Looks for lines like this:

    ![sm.inkscape](inkscape_file) 100,001,111

    The list of layer configurations on the right is optional. Those strings
    specify the layer configurations to render.  The example above would
    render bottom layer alone, the top layer alone, and then all three
    layers together, in that order.  It would then create three slides,
    one for each render.  The length of each 0/1 string must be the same as
    the number of layers in the input inkscape file.  If no configurations
    are specified, the renderer will build the layers sequentially from
    bottom to top (i.e. 1000, 1100, 1110, 1111).
    """

    def __init__(self,
                 target_dir="slidemachine.data",
                 img_format="png",
                 text_to_path=True,
                 pattern="!\[sm.inkscape\]"):
        """
        target_dir: directory in which to write out rendered files
        img_format: image format (png, pdf, svg)
        text_to_path: convert text in svg to path
        pattern: pattern to use to look for inkscape lines in markdown
        """

        self._img_format = img_format
        self._text_to_path = text_to_path

        self._configs_rendered = {}
        self._prev_build_dict = {}

        super(InkscapeProcessor, self).__init__(target_dir,pattern)

    def process(self,line):
        """
        Process a line, either returning input line or new lines for rendered
        svg.
        """

        this_processing = {}

        # If the line does not match, return the original line
        if not self._pattern.match(line):
            return line

        svg_file, layer_configs = self._parse_markdown_line(line)

        # Create inkscape object and figure out what layer configurations
        # we are going to render
        ink = InkscapeSVG(svg_file)
        if layer_configs is None:
            tmp_layer_configs = ink.default_layer_render

            # Convert the bool lists from the InkscapeSVG object to
            # strings.
            layer_configs = []
            for config in tmp_layer_configs:
                layer_configs.append("".join([str(int(l)) for l in config]))

        # Get the md5 of the input file.  This will change if that file
        # changed
        input_file_md5 = self._get_file_md5(svg_file)

        try:

            prev_file_render = self._previous_build_dict[input_file_md5]

            tmp_layer_configs = []
            for config in layer_configs:
                try:

                    # Get file written out the last time this svg file was
                    # rendered
                    prev_output = prev_file_render[config]

                    # If the file still exists, we don't need to render it,
                    # so we should record it as already rendered
                    if os.path.isfile(prev_output):
                        this_processing[input_file_md5][config] = prev_output

                    # If not, raise an error
                    else:
                        raise KeyError

                # If we get a KeyError here, we need to render this config
                except KeyError:
                    tmp_layer_configs.append(config)

            # the layer_configs to keep are whatever wasn't already rendered
            # above.
            layer_configs = copy.deepcopy(layer_configs)

        # A KeyError here means that the input_file_md5 has never been seen --
        # render all layers
        except KeyError:
            pass

        # Check to see if we have already rendered this svg/layer combo during
        # this session.
        #
        # The final_file_names list will have output file names for
        # things that have already been rendered and None for things that
        # have yet to be rendered. configs_to_render will have only
        # configurationns that should be rendered.

        final_file_names = []
        configs_to_render = []

        for config in layer_configs:

            expected_render = (svg_file,config)
            try:
                output_file = self._configs_rendered[expected_render]
                final_file_names.append(output_file)
            except KeyError:
                configs_to_render.append(config)
                final_file_names.append(None)

            # Record that this file was processed
            this_processing[input_file_md5][config] = output_file

        # ------ Render everything in configs_to_render -----------

        # Create temporary output directory
        id = "".join([random.choice(string.ascii_letters)
                      for i in range(10)])
        tmp_dir = "tmp_{}".format(id)
        os.mkdir(tmp_dir)

        # Make temporary output file root
        out_root = os.path.split(svg_file)[1][:-4]
        out_root = os.path.join(tmp_dir,out_root)

        if len(configs_to_render) > 0:

            # Do rendering
            renders = ink.render_layers(out_root,
                                        format=self._img_format,
                                        layer_configs=configs_to_render)
        else:
            renders = []

        # Now go through final_file_names.  Things that were rendered in
        # the past will have an actual file name.  Things we just
        # rendered will be None.  When we hit a None, grab the file from
        # the renders list and use the _copy_file method to copy it into
        # the final output directory.  Finally, update the markdown
        # with the final file name.

        final_markdown = []

        new_render_counter = 0
        for file in final_file_names:
            if file is None:

                # Get the file out of the new renders
                new_file = renders[new_render_counter]

                # Copy the file from wherever it is in the filesystem to
                # the appropriate output directory
                file = self._copy_file(new_file)

                # Record that we rendered this file/config combo
                key = (svg_file,configs_to_render[new_render_counter])
                self._configs_rendered[key] = file

                # Update index to new renders
                new_render_counter += 1

            # Update markdown with the file
            final_markdown.append("![an image]({})\n".format(file))

        # Nuke temporary files
        shutil.rmtree(tmp_dir)

        # 
        for k in this_processing.keys():
            self._this_proc_dict[k] = this_processing[k]

        # If there is only one line to return, return as a string
        if len(final_markdown) == 1:
            to_return = final_markdown[0]

        # If there is more than one line to return, return as tuple of str
        else:
            to_return = tuple(final_markdown)

        return to_return
