from click.testing import CliRunner
from sqlite_transform import cli
import sqlite_utils
import pytest


@pytest.mark.parametrize(
    "code",
    [
        "return value.replace('October', 'Spooktober')",
        # Return is optional:
        "value.replace('October', 'Spooktober')",
    ],
)
def test_lambda_single_line(test_db, code):
    result = CliRunner().invoke(
        cli.cli, ["lambda", test_db, "example", "dt", "--code", code]
    )
    assert 0 == result.exit_code, result.output
    assert [
        {"id": 1, "dt": "5th Spooktober 2019 12:04"},
        {"id": 2, "dt": "6th Spooktober 2019 00:05:06"},
    ] == list(sqlite_utils.Database(test_db)["example"].rows)


def test_lambda_multiple_lines(test_db):
    result = CliRunner().invoke(
        cli.cli,
        [
            "lambda",
            test_db,
            "example",
            "dt",
            "--code",
            "v = value.replace('October', 'Spooktober')\nreturn v.upper()",
        ],
    )
    assert 0 == result.exit_code, result.output
    assert [
        {"id": 1, "dt": "5TH SPOOKTOBER 2019 12:04"},
        {"id": 2, "dt": "6TH SPOOKTOBER 2019 00:05:06"},
    ] == list(sqlite_utils.Database(test_db)["example"].rows)


def test_lambda_import(test_db):
    result = CliRunner().invoke(
        cli.cli,
        [
            "lambda",
            test_db,
            "example",
            "dt",
            "--code",
            "return re.sub('O..', 'OXX', value)",
            "--import",
            "re",
        ],
    )
    assert 0 == result.exit_code, result.output
    assert [
        {"id": 1, "dt": "5th OXXober 2019 12:04"},
        {"id": 2, "dt": "6th OXXober 2019 00:05:06"},
    ] == list(sqlite_utils.Database(test_db)["example"].rows)
