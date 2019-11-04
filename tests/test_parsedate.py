from click.testing import CliRunner
from sqlite_transform import cli
import pathlib
import pytest
import sqlite_utils


@pytest.fixture
def db_with_dates(tmpdir):
    db_path = str(pathlib.Path(tmpdir) / "data.db")
    db = sqlite_utils.Database(db_path)
    db["example"].insert_all(
        [
            {"id": 1, "dt": "5th October 2019 12:04"},
            {"id": 2, "dt": "6th October 2019 00:05:06"},
        ],
        pk="id",
    )
    return db_path


def test_parsedate(db_with_dates):
    result = CliRunner().invoke(cli.cli, ["parsedate", db_with_dates, "example", "dt"])
    assert 0 == result.exit_code, result.output
    assert [{"id": 1, "dt": "2019-10-05"}, {"id": 2, "dt": "2019-10-06"}] == list(
        sqlite_utils.Database(db_with_dates)["example"].rows
    )


def test_parsedatetime(db_with_dates):
    result = CliRunner().invoke(
        cli.cli, ["parsedatetime", db_with_dates, "example", "dt"]
    )
    assert 0 == result.exit_code, result.output
    assert [
        {"id": 1, "dt": "2019-10-05T12:04:00"},
        {"id": 2, "dt": "2019-10-06T00:05:06"},
    ] == list(sqlite_utils.Database(db_with_dates)["example"].rows)
