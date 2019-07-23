#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-graph
# Created by the Natural History Museum in London, UK

from setuptools import find_packages, setup

__version__ = u'1.0.0-alpha'

with open(u'README.md', u'r') as f:
    __long_description__ = f.read()

setup(
    name=u'ckanext-graph',
    version=__version__,
    description=u'A CKAN extension that adds a graph view for resources.',
    long_description=__long_description__,
    classifiers=[
        u'Development Status :: 3 - Alpha',
        u'Framework :: Flask',
        u'Programming Language :: Python :: 2.7'
    ],
    keywords=u'CKAN data graph',
    author=u'Natural History Museum',
    author_email=u'data@nhm.ac.uk',
    url=u'https://github.com/NaturalHistoryMuseum/ckanext-graph',
    license=u'GNU GPLv3',
    packages=find_packages(exclude=[u'tests']),
    namespace_packages=[u'ckanext', u'ckanext.graph'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    entry_points= \
        u'''
        [ckan.plugins]
            graph=ckanext.graph.plugin:GraphPlugin
        ''',
    )
