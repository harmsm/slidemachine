__description__ = \
"""
Generate reveal.js slides from inkscape svg files
"""
__version__ = "0.1"
__author__ = "Michael J. Harms"
__date__ = "2018-05-10"


import sys

if sys.version_info[0] < 3:
    sys.exit('Sorry, Python < 3.x is not supported')

from setuptools import setup, find_packages
import numpy

setup(name="slidemachine",
      packages=find_packages(),
      version=__version__,
      description="generate reveal.js slides from inkscape svg files",
      long_description=__description__,
      author='Michael J. Harms',
      author_email='harmsm@gmail.com',
      url='https://github.com/harmsm/slidemachine',
      download_url="https://github.com/harmsm/slidemachine/archive/{}.tar.gz".format(__version__),
      install_requires=["mistune"],
      zip_safe=False,
      classifiers=['Programming Language :: Python'],
      entry_points = {
            'console_scripts': [
                  'slidemachine = slidemachine.console.slidemachine:main',
            ]
      })
