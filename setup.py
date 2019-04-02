__doc__ = """
=====================
Shapps Introduction
=====================

:Author: Chunlin Zhang <zhangchunlin@gmail.com>,Jiannan Tang <tangjn518@gmail.com>

.. contents:: 

About Shapps
----------------

Shapps is an apps collection project for uliweb. So you can use any app of it
to compose your project.

License
------------

Shapps is released under BSD license. Of cause if there are some third party
apps not written by this project's author, it'll under the license of itself.

"""

from setuptools import setup, find_packages
import shapps

setup(name='shapps',
    version=shapps.__version__,
    description="Another apps collection for uliweb",
    long_description=__doc__,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
    ],
    packages = find_packages(),
    platforms = 'any',
    keywords='wsgi web framework',
    author=shapps.__author__,
    author_email=shapps.__author_email__,
    url=shapps.__url__,
    license=shapps.__license__,
    include_package_data=True,
    zip_safe=False,
    entry_points = {
        'uliweb_apps': [
          'helpers = shapps',
        ],
    },
)
