# sqlite-transform

[![PyPI](https://img.shields.io/pypi/v/sqlite-transform.svg)](https://pypi.org/project/sqlite-transform/)
[![Changelog](https://img.shields.io/github/v/release/simonw/sqlite-transform?include_prereleases&label=changelog)](https://github.com/simonw/sqlite-transform/releases)
[![Tests](https://github.com/simonw/sqlite-transform/workflows/Test/badge.svg)](https://github.com/simonw/sqlite-transform/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/dogsheep/sqlite-transform/blob/main/LICENSE)

Tool for running transformations on columns in a SQLite database.

## How to install

    pip install sqlite-transform

## parsedate and parsedatetime

These subcommands will run all values in the specified column through `dateutils.parser.parse()` and replace them with the result, formatted as an ISO timestamp or ISO date.

For example, if a row in the database has an `opened` column which contains `10/10/2019 08:10:00 PM`, running the following command:

    sqlite-transform parsedatetime my.db mytable opened

Will result in that value being replaced by `2019-10-10T20:10:00`.

Using the `parsedate` subcommand here would result in `2019-10-10` instead.

In the case of ambiguous dates such as `03/04/05` these commands both default to assuming American-style `mm/dd/yy` format. You can pass `--dayfirst` to specify that the day should be assumed to be first, or `--yearfirst` for the year.

## jsonsplit

The `jsonsplit` subcommand takes columns that contain a comma-separated list, for example a `tags` column containing records like `"trees,park,dogs"` and converts it into a JSON array `["trees", "park", "dogs"]`.

This is useful for taking advantage of Datasette's [Facet by JSON array](https://docs.datasette.io/en/stable/facets.html#facet-by-json-array) feature.

    sqlite-transform jsonsplit my.db mytable tags

It defaults to splitting on commas, but you can specify a different delimiter character using the `--delimiter` option, for example:

    sqlite-transform jsonsplit \
        my.db mytable tags --delimiter ';'

Values within the array will be treated as strings, so a column containing `123,552,775` will be converted into the JSON array `["123", "552", "775"]`.

You can specify a different type for these values using `--type int` or `--type float`, for example:

    sqlite-transform jsonsplit \
        my.db mytable tags --type int

This will result in that column being converted into `[123, 552, 775]`.

## lambda for executing your own code

The `lambda` subcommand lets you specify Python code which will be executed against the column.

Here's how to convert a column to uppercase:

    sqlite-transform lambda my.db mytable mycolumn --code='str(value).upper()'

The code you provide will be compiled into a function that takes `value` as a single argument. You can break your function body into multiple lines, provided the last line is a `return` statement:

    sqlite-transform lambda my.db mytable mycolumn --code='value = str(value)
    return value.upper()'

You can also specify Python modules that should be imported and made available to your code using one or more `--import` options:

    sqlite-transform lambda my.db mytable mycolumn \
        --code='"\n".join(textwrap.wrap(value, 10))' \
        --import=textwrap

The `--dry-run` option will output a preview of the transformation against the first ten rows, without modifying the database.

## Saving the result to a separate column

Each of these commands accepts optional `--output` and `--output-type` options. These can be used to save the result of the transformation to a separate column, which will be created if the column does not already exist.

To save the result of `jsonsplit` to a new column called `json_tags`, use the following:

    sqlite-transform jsonsplit my.db mytable tags \
      --output json_tags

The type of the created column defaults to `text`, but a different column type can be specified using `--output-type`. This example will create a new floating point column called `float_id` with a copy of each item's ID increased by 0.5:

    sqlite-transform lambda my.db mytable id \
      --code 'float(value) + 0.5' \
      --output float_id \
      --output-type float

### Terminology warning

This tool uses the word "transform" to mean something different from the [sqlite-utils transform](https://sqlite-utils.datasette.io/en/stable/cli.html#transforming-tables) command.

In `sqlite-utils`, "transform" is used to describe running complex alter table statements, see [Executing advanced ALTER TABLE operations in SQLite](https://simonwillison.net/2020/Sep/23/sqlite-advanced-alter-table/)

`sqlite-transform` uses the term to describe performing a transformation or conversion on every value in a column.

I apologize for this confusion! I wish I had used different names for these two concepts.
