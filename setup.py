# -*- coding: UTF-8 -*
from setuptools import setup

setup(name='voyager',
      version='1.0',
      description='An agent-based simulation tool for traversing oceans',
      url='http://github.com/waahlstrand/voyager',
      author='Victor Wåhlstrand Skärström',
      license='MIT',
      packages=['voyager'],
      zip_safe=False,
      install_requires=['pandas',
                        'numpy',
                        'pyyaml',
                        'xarray',
                        'opencv-python',
                        'geopy',
                        'scipy',
                        'dask',
                        'netcdf4'])