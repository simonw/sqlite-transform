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
def test_lambda_single_line(test_db_and_path, code):
    db, db_path = test_db_and_path
    result = CliRunner().invoke(
        cli.cli, ["lambda", db_path, "example", "dt", "--code", code]
    )
    assert 0 == result.exit_code, result.output
    assert [
        {"id": 1, "dt": "5th Spooktober 2019 12:04"},
        {"id": 2, "dt": "6th Spooktober 2019 00:05:06"},
        {"id": 3, "dt": ""},
        {"id": 4, "dt": None},
    ] == list(db["example"].rows)


def test_lambda_multiple_lines(test_db_and_path):
    db, db_path = test_db_and_path
    result = CliRunner().invoke(
        cli.cli,
        [
            "lambda",
            db_path,
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
        {"id": 3, "dt": ""},
        {"id": 4, "dt": None},
    ] == list(db["example"].rows)


def test_lambda_import(test_db_and_path):
    db, db_path = test_db_and_path
    result = CliRunner().invoke(
        cli.cli,
        [
            "lambda",
            db_path,
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
        {"id": 3, "dt": ""},
        {"id": 4, "dt": None},
    ] == list(db["example"].rows)


def test_lambda_dryrun(test_db_and_path):
    db, db_path = test_db_and_path
    result = CliRunner().invoke(
        cli.cli,
        [
            "lambda",
            db_path,
            "example",
            "dt",
            "--code",
            "return re.sub('O..', 'OXX', value)",
            "--import",
            "re",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert result.output.strip() == (
        "5th October 2019 12:04\n"
        " --- becomes:\n"
        "5th OXXober 2019 12:04\n"
        "\n"
        "6th October 2019 00:05:06\n"
        " --- becomes:\n"
        "6th OXXober 2019 00:05:06\n"
        "\n"
        "\n"
        " --- becomes:\n"
        "\n"
        "\n"
        "None\n"
        " --- becomes:\n"
        "None"
    )
    # But it should not have actually modified the table data
    assert list(db["example"].rows) == [
        {"id": 1, "dt": "5th October 2019 12:04"},
        {"id": 2, "dt": "6th October 2019 00:05:06"},
        {"id": 3, "dt": ""},
        {"id": 4, "dt": None},
    ]
