# sqlite-transform

[![PyPI](https://img.shields.io/pypi/v/sqlite-transform.svg)](https://pypi.org/project/sqlite-transform/)
[![CircleCI](https://circleci.com/gh/simonw/sqlite-transform.svg?style=svg)](https://circleci.com/gh/simonw/sqlite-transform)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/dogsheep/sqlite-transform/blob/master/LICENSE)

Tool for running transformations on columns in a SQLite database.

## How to install

    $ pip install sqlite-transform

## parsedate and parsedatetime

These subcommands will run all values in the specified column through `dateutils.parser.parse()` and replace them with the result, formatted as an ISO timestamp or ISO date.

For example, if a row in the database has an `opened` column which contains `10/10/2019 08:10:00 PM`, running the following command:

    $ sqlite-transform parsedatetime my.db mytable opened

Will result in that value being replaced by `2019-10-10T20:10:00`.

Using the `parsedate` subcommand here would result in `2019-10-10` instead.
