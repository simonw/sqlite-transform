from click.testing import CliRunner
from sqlite_transform import cli
import pytest


def test_parsedate(test_db_and_path):
    db, db_path = test_db_and_path
    result = CliRunner().invoke(cli.cli, ["parsedate", db_path, "example", "dt"])
    assert 0 == result.exit_code, result.output
    assert [
        {"id": 1, "dt": "2019-10-05"},
        {"id": 2, "dt": "2019-10-06"},
        {"id": 3, "dt": ""},
        {"id": 4, "dt": None},
    ] == list(db["example"].rows)


def test_parsedatetime(test_db_and_path):
    db, db_path = test_db_and_path
    result = CliRunner().invoke(cli.cli, ["parsedatetime", db_path, "example", "dt"])
    assert 0 == result.exit_code, result.output
    assert [
        {"id": 1, "dt": "2019-10-05T12:04:00"},
        {"id": 2, "dt": "2019-10-06T00:05:06"},
        {"id": 3, "dt": ""},
        {"id": 4, "dt": None},
    ] == list(db["example"].rows)


@pytest.mark.parametrize(
    "command,options,expected",
    (
        ("parsedate", [], "2005-03-04"),
        ("parsedate", ["--dayfirst"], "2005-04-03"),
        ("parsedatetime", [], "2005-03-04T00:00:00"),
        ("parsedatetime", ["--dayfirst"], "2005-04-03T00:00:00"),
    ),
)
def test_dayfirst_yearfirst(fresh_db_and_path, command, options, expected):
    db, db_path = fresh_db_and_path
    db["example"].insert_all(
        [
            {"id": 1, "dt": "03/04/05"},
        ],
        pk="id",
    )
    result = CliRunner().invoke(cli.cli, [command, db_path, "example", "dt"] + options)
    assert result.exit_code == 0
    assert list(db["example"].rows) == [
        {"id": 1, "dt": expected},
    ]
