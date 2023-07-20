#!/usr/bin/env python3

from setuptools import setup

if __name__ == '__main__':
    setup(name='powermodes',

          entry_points={
              'console_scripts': [
                   'powermodes = powermodes.main:main'
               ]
          }
         )

