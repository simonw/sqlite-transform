from click.testing import CliRunner
import json
import pathlib
import pytest
from sqlite_transform import cli
import sqlite_utils


@pytest.mark.parametrize("delimiter", [None, ";", "-"])
def test_jsonsplit(tmpdir, delimiter):
    db_path = str(pathlib.Path(tmpdir) / "data.db")
    db = sqlite_utils.Database(db_path)
    db["example"].insert_all(
        [
            {"id": 1, "tags": (delimiter or ",").join(["foo", "bar"])},
            {"id": 2, "tags": (delimiter or ",").join(["bar", "baz"])},
        ],
        pk="id",
    )
    args = ["jsonsplit", db_path, "example", "tags"]
    if delimiter is not None:
        args.extend(["--delimiter", delimiter])
    result = CliRunner().invoke(cli.cli, args)
    assert 0 == result.exit_code, result.output
    assert list(db["example"].rows) == [
        {"id": 1, "tags": '["foo", "bar"]'},
        {"id": 2, "tags": '["bar", "baz"]'},
    ]


@pytest.mark.parametrize(
    "type,expected_array",
    (
        (None, ["1", "2", "3"]),
        ("float", [1.0, 2.0, 3.0]),
        ("int", [1, 2, 3]),
    ),
)
def test_jsonsplit_type(fresh_db_and_path, type, expected_array):
    db, db_path = fresh_db_and_path
    db["example"].insert_all(
        [
            {"id": 1, "records": "1,2,3"},
        ],
        pk="id",
    )
    args = ["jsonsplit", db_path, "example", "records"]
    if type is not None:
        args.extend(("--type", type))
    result = CliRunner().invoke(cli.cli, args)
    assert 0 == result.exit_code, result.output
    assert json.loads(db["example"].get(1)["records"]) == expected_array
