ckanext-graph
=============

[![Travis branch](https://img.shields.io/travis/NaturalHistoryMuseum/ckanext-graph/master.svg?style=flat-square)](https://travis-ci.org/NaturalHistoryMuseum/ckanext-graph) [![Coveralls github branch](https://img.shields.io/coveralls/github/NaturalHistoryMuseum/ckanext-graph/master.svg?style=flat-square)](https://coveralls.io/github/NaturalHistoryMuseum/ckanext-graph)

CKAN extension for graph views, with data processing moved to the backend.

At the moment it just has one type of graph - temporal.  Select a date created field, and a graph will show how the dataset has increaed over time.

More graphs are planner for the future.

Configuration
-------------

ckanext.gallery.field_separator

Defaults to ;