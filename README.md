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

## lambda for executing your own code

The `lambda` subcommand lets you specify Python code which will be executed against the column.

Here's how to convert a column to uppercase:

    $ sqlite-transform lambda my.db mytable mycolumn --code='str(value).upper()'

The code you provide will be compiled into a function that takes `value` as a single argument. You can break your function body into multiple lines, provided the last line is a `return` statement:

    $ sqlite-transform lambda my.db mytable mycolumn --code='value = str(value)
    return value.upper()'

You can also specify Python modules that should be imported and made available to your code using one or more `--import` options:

    $ sqlite-transform lambda my.db mytable mycolumn \
        --code='"\n".join(textwrap.wrap(value, 10))' \
        --import=textwrap
