#!/usr/bin/env python3
__description__ = \
"""
Class for manipulating and rendering the layers in an Inkscape-generated svg
file.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-05-09"

import sys, os, re, subprocess, copy, random, string
from xml.dom import minidom

class Inkscape:
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

            # Construct a default set of layer configurations going like:
            #   100, 110, 111
            # This starts with layer one, then layer one+two, then layer
            # one+two+three

            layer_configs = []

            config = [False for s in self._layer_list]
            for i in range(len(self._layer_list)):
                config[i] = True

                layer_configs.append(copy.deepcopy(config))

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

            # If user specified 100101, convert to boolean
            tmp = []
            for config in layer_configs:
                if type(config) is str:
                    tmp.append([bool(int(c)) for c in list(config)])
                else:
                    tmp.append(config)

            layer_configs = copy.deepcopy(tmp)

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
