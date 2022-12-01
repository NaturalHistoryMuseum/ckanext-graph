<!--header-start-->
<img src=".github/nhm-logo.svg" align="left" width="150px" height="100px" hspace="40"/>

# ckanext-graph

[![Tests](https://img.shields.io/github/workflow/status/NaturalHistoryMuseum/ckanext-graph/Tests?style=flat-square)](https://github.com/NaturalHistoryMuseum/ckanext-graph/actions/workflows/main.yml)
[![Coveralls](https://img.shields.io/coveralls/github/NaturalHistoryMuseum/ckanext-graph/main?style=flat-square)](https://coveralls.io/github/NaturalHistoryMuseum/ckanext-graph)
[![CKAN](https://img.shields.io/badge/ckan-2.9.7-orange.svg?style=flat-square)](https://github.com/ckan/ckan)
[![Python](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8-blue.svg?style=flat-square)](https://www.python.org/)
[![Docs](https://img.shields.io/readthedocs/ckanext-graph?style=flat-square)](https://ckanext-graph.readthedocs.io)

_A CKAN extension that adds a graph view for resources._

<!--header-end-->

# Overview

<!--overview-start-->
Adds graph views for resources on a CKAN instance. Two types of graph are available: temporal (a line graph showing count over time based on a specified date field), and categorical (a bar chart showing counts for various values in a specified field).


**NB**: the current version of this extension only works with the Natural History Museum's [ElasticSearch datastore CKAN backend](https://github.com/NaturalHistoryMuseum/ckanext-versioned-datastore). _However_, it is designed to be extensible, so if you would like to use this extension with a different backend (e.g. the standard PostgreSQL datastore), please see the [Extending](#extending) section.

<!--overview-end-->

# Installation

<!--installation-start-->
Path variables used below:
- `$INSTALL_FOLDER` (i.e. where CKAN is installed), e.g. `/usr/lib/ckan/default`
- `$CONFIG_FILE`, e.g. `/etc/ckan/default/development.ini`

## Installing from PyPI

```shell
pip install ckanext-graph
```

## Installing from source

1. Clone the repository into the `src` folder:
   ```shell
   cd $INSTALL_FOLDER/src
   git clone https://github.com/NaturalHistoryMuseum/ckanext-graph.git
   ```

2. Activate the virtual env:
   ```shell
   . $INSTALL_FOLDER/bin/activate
   ```

3. Install via pip:
   ```shell
   pip install $INSTALL_FOLDER/src/ckanext-graph
   ```

### Installing in editable mode

Installing from a `pyproject.toml` in editable mode (i.e. `pip install -e`) requires `setuptools>=64`; however, CKAN 2.9 requires `setuptools==44.1.0`. See [our CKAN fork](https://github.com/NaturalHistoryMuseum/ckan) for a version of v2.9 that uses an updated setuptools if this functionality is something you need.

## Post-install setup

1. Add 'graph' to the list of plugins in your `$CONFIG_FILE`:
   ```ini
   ckan.plugins = ... graph
   ```

<!--installation-end-->

# Configuration

<!--configuration-start-->
These are the options that can be specified in your .ini config file.

Name|Description|Options|Default
--|--|--|--
`ckanext.graph.backend`|The name of the backend to use (currently only `elasticsearch` is implemented)|elasticsearch, sql|elasticsearch

<!--configuration-end-->

# Usage

<!--usage-start-->
## Templates

The view will be added as an option with no further configuration necessary. However, if you wish to override or add content to the template, you can extend `templates/graph/view.html`:

```html+jinja
{% ckan_extends %}

{% block my_new_block %}
  <p>Look, some exciting new content.</p>
{% endblock %}
```


# Extending

To use this extension with a datastore backend other than the ElasticSearch backend already implemented, you'll have to subclass from `Query` in `ckanext-graph/ckanext/graph/db.py`.

An unimplemented class for SQL queries is already in the file as an example:

```python
class SqlQuery(Query):
    @property
    def _date_query(self):
        raise NotImplementedError()

    @property
    def _count_query(self):
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()
```

If you add a new class, you'll have to add it to the dictionary in `Query.new()` method to make it available as a configurable option.

If you do this, please submit a pull request! Contributions are always welcome.

<!--usage-end-->

# Testing

<!--testing-start-->
There is a Docker compose configuration available in this repository to make it easier to run tests.

To run the tests against ckan 2.9.x on Python3:

1. Build the required images
```bash
docker-compose build
```

2. Then run the tests.
   The root of the repository is mounted into the ckan container as a volume by the Docker compose
   configuration, so you should only need to rebuild the ckan image if you change the extension's
   dependencies.
```bash
docker-compose run ckan
```

The ckan image uses the Dockerfile in the `docker/` folder.

<!--testing-end-->
