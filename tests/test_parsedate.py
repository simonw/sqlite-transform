from click.testing import CliRunner
from sqlite_transform import cli
import sqlite_utils


def test_parsedate(test_db):
    result = CliRunner().invoke(cli.cli, ["parsedate", test_db, "example", "dt"])
    assert 0 == result.exit_code, result.output
    assert [
        {"id": 1, "dt": "2019-10-05"},
        {"id": 2, "dt": "2019-10-06"},
        {"id": 3, "dt": ""},
        {"id": 4, "dt": None},
    ] == list(sqlite_utils.Database(test_db)["example"].rows)


def test_parsedatetime(test_db):
    result = CliRunner().invoke(cli.cli, ["parsedatetime", test_db, "example", "dt"])
    assert 0 == result.exit_code, result.output
    assert [
        {"id": 1, "dt": "2019-10-05T12:04:00"},
        {"id": 2, "dt": "2019-10-06T00:05:06"},
        {"id": 3, "dt": ""},
        {"id": 4, "dt": None},
    ] == list(sqlite_utils.Database(test_db)["example"].rows)
