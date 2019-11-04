import click
from dateutil import parser
import sqlite3
import tqdm


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
def parsedatetime(db_path, table, columns):
    """
    Run specified columns through a datetime parser and convert them
    to an ISO timestamp.
    """
    db = sqlite3.connect(db_path)
    count_sql = "select count(*) from [{}]".format(table)
    todo_count = list(db.execute(count_sql).fetchall())[0][0] * len(columns)

    with tqdm.tqdm(total=todo_count) as bar:

        def _parsedatetime(v):
            bar.update(1)
            if not v:
                return v
            try:
                return parser.parse(v).isoformat()
            except Exception as e:
                return str(e)

        db.create_function("parsedatetime", 1, _parsedatetime)
        sql = "update [{table}] set {sets};".format(
            table=table,
            sets=", ".join(
                [
                    "[{column}] = parsedatetime([{column}])".format(column=column)
                    for column in columns
                ]
            ),
        )
        with db:
            db.execute(sql)
