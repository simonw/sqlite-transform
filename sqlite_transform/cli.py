import click
from dateutil import parser
import json
import sqlite3
import sqlite_utils
import tqdm

sqlite3.enable_callback_tracebacks(True)


def common_options(fn):
    click.option("-s", "--silent", is_flag=True, help="Don't show a progress bar")(fn)
    click.option("--drop", is_flag=True, help="Drop original column afterwards")(fn)
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
@click.argument("columns", type=str, nargs=-1, required=True)
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
@common_options
def parsedate(
    db_path, table, columns, dayfirst, yearfirst, output, output_type, drop, silent
):
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
        drop,
        silent,
    )


@cli.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument("table", type=str)
@click.argument("columns", type=str, nargs=-1, required=True)
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
@common_options
def parsedatetime(
    db_path, table, columns, dayfirst, yearfirst, output, output_type, drop, silent
):
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
        drop,
        silent,
    )


@cli.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument("table", type=str)
@click.argument("columns", type=str, nargs=-1, required=True)
@click.option("--delimiter", default=",", help="Delimiter to split on")
@click.option(
    "--type",
    type=click.Choice(("int", "float")),
    help="Type to use for values - int or float (defaults to string)",
)
@common_options
def jsonsplit(
    db_path, table, columns, delimiter, type, output, output_type, drop, silent
):
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

    _transform(db_path, table, columns, convert, output, output_type, drop, silent)


@cli.command(name="lambda")
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument("table", type=str)
@click.argument("columns", type=str, nargs=-1, required=True)
@click.option(
    "--code", type=str, required=True, help="Python code to transform 'value'"
)
@click.option(
    "--import", "imports", type=str, multiple=True, help="Python modules to import"
)
@click.option(
    "--dry-run", is_flag=True, help="Show results of running this against first 10 rows"
)
@click.option(
    "--multi", is_flag=True, help="Populate columns for keys in returned dictionary"
)
@common_options
def lambda_(
    db_path,
    table,
    columns,
    code,
    imports,
    dry_run,
    multi,
    output,
    output_type,
    drop,
    silent,
):
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
    if multi and len(columns) > 1:
        raise click.ClickException("Cannot use --multi with more than one column")
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
    elif multi:
        _transform_multi(db_path, table, columns[0], fn, drop, silent)
    else:
        _transform(db_path, table, columns, fn, output, output_type, drop, silent)


def _transform(db_path, table, columns, fn, output, output_type, drop, silent):
    db = sqlite_utils.Database(db_path)
    count_sql = "select count(*) from [{}]".format(table)
    todo_count = list(db.execute(count_sql).fetchall())[0][0] * len(columns)

    if drop and not output:
        raise click.ClickException("--drop can only be used with --output or --multi")

    if output is not None:
        if output not in db[table].columns_dict:
            db[table].add_column(output, output_type or "text")

    with tqdm.tqdm(total=todo_count, disable=silent) as bar:

        def transform_value(v):
            bar.update(1)
            if not v:
                return v
            return fn(v)

        db.register_function(transform_value)
        sql = "update [{table}] set {sets};".format(
            table=table,
            sets=", ".join(
                [
                    "[{output_column}] = transform_value([{column}])".format(
                        output_column=output or column, column=column
                    )
                    for column in columns
                ]
            ),
        )
        with db.conn:
            db.execute(sql)
            if drop:
                db[table].transform(drop=columns)


def _transform_multi(db_path, table, column, fn, drop, silent):
    db = sqlite_utils.Database(db_path)
    # First we execute the function
    pk_to_values = {}
    new_column_types = {}
    pks = [column.name for column in db[table].columns if column.is_pk]
    if not pks:
        pks = ["rowid"]
    with tqdm.tqdm(total=db[table].count, disable=silent, desc="1: Evaluating") as bar:
        for row in db[table].rows_where(
            select=", ".join(
                "[{}]".format(column_name) for column_name in (pks + [column])
            )
        ):
            row_pk = tuple(row[pk] for pk in pks)
            if len(row_pk) == 1:
                row_pk = row_pk[0]
            values = fn(row[column])
            if values is not None and not isinstance(values, dict):
                raise click.ClickException(
                    "With --multi code must return a Python dictionary - returned {}".format(
                        repr(values)
                    )
                )
            if values:
                for key, value in values.items():
                    new_column_types.setdefault(key, set()).add(type(value))
                pk_to_values[row_pk] = values
            bar.update(1)

    # Add any new columns
    columns_to_create = _suggest_column_types(new_column_types)
    for column_name, column_type in columns_to_create.items():
        if column_name not in db[table].columns_dict:
            db[table].add_column(column_name, column_type)

    # Run the updates
    with tqdm.tqdm(total=db[table].count, disable=silent, desc="2: Updating") as bar:
        with db.conn:
            for pk, updates in pk_to_values.items():
                db[table].update(pk, updates)
                bar.update(1)
            if drop:
                db[table].transform(drop=(column,))


def _suggest_column_types(all_column_types):
    column_types = {}
    for key, types in all_column_types.items():
        # Ignore null values if at least one other type present:
        if len(types) > 1:
            types.discard(None.__class__)
        if {None.__class__} == types:
            t = str
        elif len(types) == 1:
            t = list(types)[0]
            # But if it's a subclass of list / tuple / dict, use str
            # instead as we will be storing it as JSON in the table
            for superclass in (list, tuple, dict):
                if issubclass(t, superclass):
                    t = str
        elif {int, bool}.issuperset(types):
            t = int
        elif {int, float, bool}.issuperset(types):
            t = float
        elif {bytes, str}.issuperset(types):
            t = bytes
        else:
            t = str
        column_types[key] = t
    return column_types
