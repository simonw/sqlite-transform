from click.testing import CliRunner
from sqlite_transform import cli
import pathlib
import sqlite_utils


def test_parsedatetime(tmpdir):
    db_path = str(pathlib.Path(tmpdir) / "data.db")
    db = sqlite_utils.Database(db_path)
    db["example"].insert_all(
        [
            {"id": 1, "dt": "5th October 2019 12:04"},
            {"id": 2, "dt": "6th October 2019 00:05:06"},
        ],
        pk="id",
    )
    result = CliRunner().invoke(cli.cli, ["parsedatetime", db_path, "example", "dt"])
    assert 0 == result.exit_code
    # Did the conversion work?
    assert [
        {"id": 1, "dt": "2019-10-05T12:04:00"},
        {"id": 2, "dt": "2019-10-06T00:05:06"},
    ] == list(db["example"].rows)
