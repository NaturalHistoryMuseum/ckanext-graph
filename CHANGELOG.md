# Changelog

## v2.1.10 (2024-11-04)

### Docs

- use variable logo based on colour scheme
- fix tests badge tests workflow file was renamed
- standardise returns field

### Style

- automatic reformat auto reformat with ruff/docformatter/prettier after config changes

### Build System(s)

- remove version from docker compose file version specifier is deprecated

### CI System(s)

- fix python setup action version
- add merge to valid commit types
- add docformatter args and dependency docformatter currently can't read from pyproject.toml without tomli
- only apply auto-fixes in pre-commit F401 returns linting errors as well as auto-fixes, so this disables the errors and just applies the fixes
- update tool config update pre-commit repo versions and switch black to ruff
- add pull request validation workflow new workflow to check commit format and code style against pre-commit config
- update workflow files standardise format, change name of tests file

### Chores/Misc

- add pull request template
- update tool details in contributing guide

## v2.1.9 (2024-08-20)

### Chores/Misc

- add build section to read the docs config
- add regex for version line in citation file
- add citation.cff to list of files with version
- add contributing guidelines
- add code of conduct
- add citation file
- update support.md links

## v2.1.8 (2023-07-17)

### Docs

- update logos

## v2.1.7 (2023-04-11)

### Build System(s)

- fix postgres not loading when running tests in docker

### Chores/Misc

- add action to sync branches when commits are pushed to main

## v2.1.6 (2023-02-20)

### Docs

- fix api docs generation script

### Style

- reformat with prettier

### Chores/Misc

- small fixes to align with other extensions

## v2.1.5 (2023-01-31)

### Docs

- **readme**: change logo url from blob to raw

## v2.1.4 (2023-01-31)

### Docs

- **readme**: direct link to logo in readme
- **readme**: fix github actions badge

## v2.1.3 (2023-01-30)

### Build System(s)

- **docker**: use 'latest' tag for test docker image

## v2.1.2 (2022-12-12)

### Docs

- **readme**: add instruction to install lessc globally

### Style

- change quotes in setup.py to single quotes

### Build System(s)

- remove local less installation
- add package data

## v2.1.1 (2022-12-01)

### Docs

- **readme**: format test section
- **readme**: fix table borders
- **readme**: update installation steps
- **readme**: update ckan patch version in header badge

## v2.1.0 (2022-11-28)

### Docs

- fix markdown-include references
- add section delimiters

### Style

- apply formatting changes

### Build System(s)

- set changelog generation to incremental
- pin ckantools minor version

### CI System(s)

- add cz_nhm as a dependency
- **commitizen**: fix message template
- add pypi release action

### Chores/Misc

- use cz_nhm commitizen config
- improve commitizen message template
- **package.json**: fix license
- standardise package files

## v2.0.1 (2022-04-25)

## v2.0.0 (2021-03-09)

## v1.0.0-alpha (2019-07-23)

## v0.0.1 (2017-08-07)
