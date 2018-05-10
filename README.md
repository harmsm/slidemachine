#slidemachine

Easily creates complicated graphical builds in reveal.js by generating slides
directly from vector graphics files.  

###Intro
[reveal.js](https://revealjs.com/) is a powerful javascript-based presentation
framework. It renders content in a browser, making it great for displaying
web content, implementing interactive widgets, and for sharing presentations
worldwide.  The dark side is that complicated graphical layouts remain extremely
painful in html. For example, having an arrow appear on a graph---something
trivial in PowerPoint---...  

slidemachine fills this gap by allowing users to create their graphics in

allowing users to create slides, with builds, in
[Inkscape](https://inkscape.org/en/)---an open-source, vector graphics program---
and then automatically render the builds as individual reveal.js slides.

###Quick start

0. Install [Inkscape](https://inkscape.org/en/) and slidemachine

```
pip3 install slidemachine
```

1. Create an inkscape .svg file.  Place the content you want for each build on
   different [layers](http://wiki.inkscape.org/wiki/index.php/Layer_Dialog). See
   `examples/example_1.svg` for an example file.

2. Write a markdown file that describes how to render the file.  The content of
   `examples/example_1.md` is:

```
![inkscape](example_1.svg)
```

3. Run slidemachine:

```
slidemachine examples/example_1.md -o build
```

This will use inkscape to render the layers in the svg file into a collection of
images, which are then placed in `build/slidemachine/`.  It also returns reveal-
ready html in `build/index.html`:

```
<section data-transition="none">
  <p><img src="slidemachine/example_1_10.png" alt="img"></p>
</section>

<section data-transition="none">
  <p><img src="slidemachine/example_1_11.png" alt="img"></p>
</section>
```

###More Features

####Multiple slides



####Custom build orders

Lets say you have a three layer file and want to show the bottom layer alone,
the middle layer alone, and then the bottom and the top layers together.  That
would be specified by:

```
![inkscape](inkscape_file)100,010,101
```

The only rule on the tags to the right is that the length of each comma-separated
string must be the same as the number of layers in the inkscape file.
