# slidemachine

Generate reveal.js slides directly from vector graphics files and markdown text

### Intro
[reveal.js](https://revealjs.com/) is a powerful javascript-based presentation
framework. It renders content in a browser, making it great for displaying
web content, implementing interactive widgets, and for sharing presentations
worldwide.  The dark side is that complicated graphical layouts remain extremely
painful. For example, having an arrow appear on a graph---something trivial in
PowerPoint---can require extensive fiddling with css and html.

*slidemachine* fills this gap by automatically rendering layers within an svg
file into individual reveal.js slides.  The rendering is done by
[Inkscape](https://inkscape.org/en/)---an open-source, vector graphics
program. A user creates their graphics heavy slides in Inkscape, saves their
builds as layers, and then describes how to do the render in simple markdown.
*slidemachine* does the rest.  And, since we're using markdown anyway, you can
conceivably write an entire presentation in markdown and render it
with *slidemachine.*  

### Quick start

0. If you haven't already, [Install reveal.js](https://github.com/hakimel/reveal.js/#installation)
   in a directory somewhere on your computer.

1. Install [Inkscape](https://inkscape.org/en/)

2. Install slidemachine. For now, use github (pip coming soon):

```
git clone https://github.com/harmsm/slidemachine
cd slidemachine
python3 setup.py install
```

3. Go into the `slidemachine/demo` directory and run the demo.

```
cd slidemachine/demo
slidemachine demo.md --template template.html
```

This will generate `index.html` and a directory called `slidemachine_media`.

4. Copy these into a reveal.js directory and run there.

```
cp -r index.html slidemachine_media /some/folder/with/reveal/
cd /some/folder/with/reveal/
grunt serve
```

### Details

*slidemachine* pre-processes markdown to break it into slides and create
appropriate image files using Inkscape.  It then uses
[mistune](https://github.com/lepture/mistune) to render the markdown as html.
If the user specifies a template reveal-style html file, these slides will
be directly inserted into the first element with `class="slides"`.  All
processed files are placed in a single output directory.

By default, the software looks for lines with `>>>` and uses those as breaks
between slides.

*slidemachine* hijacks the image syntax.  It looks for lines such as:

```
![sm.inkscape](inkscape_file.svg) 100,010,111
```

This means:

1. `![sm.inkscape]` indicates that *slidemachine* should use the
   `InkscapeProcessor.`

2. `(inkscape_file.svg)` tells *slidemachine* what file to use.

3. The `100,010,111` chunk is optional. It says which layers to build in what
   order. In this case, create three images: one with bottom layer (`100`), one
   with the middle layer (`010`) and one with all three layers (`111`).  If no
   layers are specified, *slidemachine* automatically builds from the bottom
   layer up: `100 -> 110 -> 111`.  (*Note*: the number of layers in each string
   must match the number of layers in the svg file).

### Intriguing thoughts

 + The code is modular enough that we should be able to drop basically any
   programatically-generated material into *slidemachine*.  Ideas include
   scripts to generate D3 or Vega code, static renders of graphs, etc.
 + *slidemachine* also solves one of the problems I've run into making reveal
   presentations: after fiddling with my talk, removing slides, tweaking
   graphics, etc. I'm never sure which image files I need to keep.  I end up
   with duplicate and extraneous graphics all over the place.  *slidemachine*
   copies all images into a single directory (checking for duplicates using
   and MD5 hash), meaning that sharing the talk requires only sharing that
   directory.  

### Extending

The markdown parsing is quite flexible, so *slidemachine* should be able to
handle any number of processors.  (It currently has two: `InkscapeProcessor`,
which handles layered inkscape svg files and `ImageProcessor` which takes a
generic image and copies it into the output directory).

1. Create a subclass of `Processor`.
2. Redefine the `process` method in the subclass.  *slidemachine* expects this
   method to have the following characteristics:
   + Takes a single line of markdown as input.
   + If the line does not match the search pattern, return the original line.
   + If the processor generates new markdown or html that should all be on the
     *same* slide, return the new text as a string.
   + If the processor returns lines that should be spread over multiple
     slides, return the lines as a tuple of strings.
3. Place the file with the new subclass in the `slidemachine/processors`
   directory and update `slidemachine/processors/__init__.py` so the new
   `Processor` subclass is exposed.
4. Modify `slidemachine/config.json` so that the `processors` key lists the
   new class and the keyword arguments necessary to initialize the class.
