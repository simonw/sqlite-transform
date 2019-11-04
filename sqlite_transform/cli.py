import click
from dateutil import parser
import sqlite3
import tqdm

sqlite3.enable_callback_tracebacks(True)


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
def parsedate(db_path, table, columns):
    """
    Parse and convert columns to ISO dates
    """
    _transform(db_path, table, columns, lambda v: parser.parse(v).date().isoformat())


@cli.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument("table", type=str)
@click.argument("columns", type=str, nargs=-1)
def parsedatetime(db_path, table, columns):
    """
    Parse and convert columns to ISO timestamps
    """
    _transform(db_path, table, columns, lambda v: parser.parse(v).isoformat())


@cli.command(name="lambda")
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument("table", type=str)
@click.argument("columns", type=str, nargs=-1)
@click.option("--code", type=str, required=True)
@click.option("--import", "imports", type=str, multiple=True)
def lambda_(db_path, table, columns, code, imports):
    """
    Transform columns using Python code you supply
    """
    # First we need to build the code into a function body called fn(value)
    new_code = ["def fn(value):"]
    for line in code.split("\n"):
        new_code.append("    {}".format(line))
    code_o = compile("\n".join(new_code), "<string>", "exec")
    locals = {}
    globals = {}
    for import_ in imports:
        globals[import_] = __import__(import_)
    exec(code_o, globals, locals)
    _transform(db_path, table, columns, locals["fn"])


def _transform(db_path, table, columns, fn):
    db = sqlite3.connect(db_path)
    count_sql = "select count(*) from [{}]".format(table)
    todo_count = list(db.execute(count_sql).fetchall())[0][0] * len(columns)

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
                    "[{column}] = transform([{column}])".format(column=column)
                    for column in columns
                ]
            ),
        )
        with db:
            db.execute(sql)
