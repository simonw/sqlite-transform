import click
from dateutil import parser
import json
import sqlite3
import sqlite_utils
import tqdm

sqlite3.enable_callback_tracebacks(True)


def output_options(fn):
    click.option(
        "--output-type",
        help="Column type to use for the output column",
        default="text",
        type=click.Choice(["integer", "float", "blob", "text"]),
    )(fn)
    click.option(
        "--output", help="Optional separate column to populate with the output"
    )(fn)
    return fn


@click.group()
@click.version_option()
def cli():
    "Tool for running transformations on columns in a SQLite database."


@cli.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument("table", type=str)
@click.argument("columns", type=str, nargs=-1)
@click.option(
    "--dayfirst",
    is_flag=True,
    help="Assume day comes first in ambiguous dates, e.g. 03/04/05",
)
@click.option(
    "--yearfirst",
    is_flag=True,
    help="Assume year comes first in ambiguous dates, e.g. 03/04/05",
)
@output_options
def parsedate(db_path, table, columns, dayfirst, yearfirst, output, output_type):
    """
    Parse and convert columns to ISO dates
    """
    _transform(
        db_path,
        table,
        columns,
        lambda v: parser.parse(v, dayfirst=dayfirst, yearfirst=yearfirst)
        .date()
        .isoformat(),
        output,
        output_type,
    )


@cli.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument("table", type=str)
@click.argument("columns", type=str, nargs=-1)
@click.option(
    "--dayfirst",
    is_flag=True,
    help="Assume day comes first in ambiguous dates, e.g. 03/04/05",
)
@click.option(
    "--yearfirst",
    is_flag=True,
    help="Assume year comes first in ambiguous dates, e.g. 03/04/05",
)
@output_options
def parsedatetime(db_path, table, columns, dayfirst, yearfirst, output, output_type):
    """
    Parse and convert columns to ISO timestamps
    """
    _transform(
        db_path,
        table,
        columns,
        lambda v: parser.parse(v, dayfirst=dayfirst, yearfirst=yearfirst).isoformat(),
        output,
        output_type,
    )


@cli.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument("table", type=str)
@click.argument("columns", type=str, nargs=-1)
@click.option("--delimiter", default=",", help="Delimiter to split on")
@click.option(
    "--type",
    type=click.Choice(("int", "float")),
    help="Type to use for values - int or float (defaults to string)",
)
@output_options
def jsonsplit(db_path, table, columns, delimiter, type, output, output_type):
    """
    Convert columns into JSON arrays by splitting on a delimiter
    """
    value_convert = lambda s: s.strip()
    if type == "int":
        value_convert = lambda s: int(s.strip())
    elif type == "float":
        value_convert = lambda s: float(s.strip())

    def convert(value):
        return json.dumps([value_convert(s) for s in value.split(delimiter)])

    _transform(db_path, table, columns, convert, output, output_type)


@cli.command(name="lambda")
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument("table", type=str)
@click.argument("columns", type=str, nargs=-1)
@click.option(
    "--code", type=str, required=True, help="Python code to transform 'value'"
)
@click.option(
    "--import", "imports", type=str, multiple=True, help="Python modules to import"
)
@click.option(
    "--dry-run", is_flag=True, help="Show results of running this against first 10 rows"
)
@output_options
def lambda_(db_path, table, columns, code, imports, dry_run, output, output_type):
    """
    Transform columns using Python code you supply. For example:

    \b
    $ sqlite-transform lambda my.db mytable mycolumn
        --code='"\\n".join(textwrap.wrap(value, 10))'
        --import=textwrap

    "value" is a variable with the column value to be transformed.
    """
    if output is not None and len(columns) > 1:
        raise click.ClickException("Cannot use --output with more than one column")
    # If single line and no 'return', add the return
    if "\n" not in code and not code.strip().startswith("return "):
        code = "return {}".format(code)
    # Compile the code into a function body called fn(value)
    new_code = ["def fn(value):"]
    for line in code.split("\n"):
        new_code.append("    {}".format(line))
    code_o = compile("\n".join(new_code), "<string>", "exec")
    locals = {}
    globals = {}
    for import_ in imports:
        globals[import_] = __import__(import_)
    exec(code_o, globals, locals)
    fn = locals["fn"]
    if dry_run:
        # Pull first 20 values for first column and preview them
        db = sqlite3.connect(db_path)
        db.create_function("preview_transform", 1, lambda v: fn(v) if v else v)
        sql = """
            select
                [{column}] as value,
                preview_transform([{column}]) as preview
            from [{table}] limit 10
        """.format(
            column=columns[0], table=table
        )
        for row in db.execute(sql).fetchall():
            print(row[0])
            print(" --- becomes:")
            print(row[1])
            print()
    else:
        _transform(db_path, table, columns, fn, output, output_type)


def _transform(db_path, table, columns, fn, output=None, output_type=None):
    db = sqlite3.connect(db_path)
    count_sql = "select count(*) from [{}]".format(table)
    todo_count = list(db.execute(count_sql).fetchall())[0][0] * len(columns)

    if output is not None:
        sqlite_utils_db = sqlite_utils.Database(db)
        if output not in sqlite_utils_db[table].columns_dict:
            sqlite_utils_db[table].add_column(output, output_type or "text")

    with tqdm.tqdm(total=todo_count) as bar:

        def _transform_value(v):
            bar.update(1)
            if not v:
                return v
            return fn(v)

        db.create_function("transform", 1, _transform_value)
        sql = "update [{table}] set {sets};".format(
            table=table,
            sets=", ".join(
                [
                    "[{output_column}] = transform([{column}])".format(
                        output_column=output or column, column=column
                    )
                    for column in columns
                ]
            ),
        )
        with db:
            db.execute(sql)
