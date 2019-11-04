# sqlite-transform

[![PyPI](https://img.shields.io/pypi/v/sqlite-transform.svg)](https://pypi.org/project/sqlite-transform/)
[![CircleCI](https://circleci.com/gh/simonw/sqlite-transform.svg?style=svg)](https://circleci.com/gh/simonw/sqlite-transform)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/dogsheep/sqlite-transform/blob/master/LICENSE)

Tool for running transformations on columns in a SQLite database.

## How to install

    $ pip install sqlite-transform

## How to use

    $ sqlite-transform parsedatetime my.db mytable column1 column2

There are only one subcommand at the moment: `parsedatetime`.

These will run all values in the specified column through `dateutils.parser.parse()` and replace them with the result, formatted as an ISO timestamp.
