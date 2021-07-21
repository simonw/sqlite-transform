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


def test_lambda_output_column(test_db_and_path):
    db, db_path = test_db_and_path
    result = CliRunner().invoke(
        cli.cli,
        [
            "lambda",
            db_path,
            "example",
            "dt",
            "--code",
            "value.replace('October', 'Spooktober')",
            "--output",
            "newcol",
        ],
    )
    assert 0 == result.exit_code, result.output
    assert [
        {
            "id": 1,
            "dt": "5th October 2019 12:04",
            "newcol": "5th Spooktober 2019 12:04",
        },
        {
            "id": 2,
            "dt": "6th October 2019 00:05:06",
            "newcol": "6th Spooktober 2019 00:05:06",
        },
        {"id": 3, "dt": "", "newcol": ""},
        {"id": 4, "dt": None, "newcol": None},
    ] == list(db["example"].rows)


@pytest.mark.parametrize(
    "output_type,expected",
    (
        ("text", [(1, "1"), (2, "2"), (3, "3"), (4, "4")]),
        ("float", [(1, 1.0), (2, 2.0), (3, 3.0), (4, 4.0)]),
        ("integer", [(1, 1), (2, 2), (3, 3), (4, 4)]),
        (None, [(1, "1"), (2, "2"), (3, "3"), (4, "4")]),
    ),
)
def test_lambda_output_column_output_type(test_db_and_path, output_type, expected):
    db, db_path = test_db_and_path
    args = [
        "lambda",
        db_path,
        "example",
        "id",
        "--code",
        "value",
        "--output",
        "new_id",
    ]
    if output_type:
        args += ["--output-type", output_type]
    result = CliRunner().invoke(
        cli.cli,
        args,
    )
    assert 0 == result.exit_code, result.output
    assert expected == list(db.execute("select id, new_id from example"))


@pytest.mark.parametrize(
    "options,expected_error",
    [
        (
            [
                "dt",
                "id",
                "--code",
                "value.replace('October', 'Spooktober')",
                "--output",
                "newcol",
            ],
            "Cannot use --output with more than one column",
        ),
        (
            [
                "dt",
                "--code",
                "value.replace('October', 'Spooktober')",
                "--output",
                "newcol",
                "--output-type",
                "invalid",
            ],
            "Error: Invalid value for '--output-type'",
        ),
    ],
)
def test_lambda_output_error(test_db_and_path, options, expected_error):
    db_path = test_db_and_path[1]
    result = CliRunner().invoke(
        cli.cli,
        [
            "lambda",
            db_path,
            "example",
        ]
        + options,
    )
    assert result.exit_code != 0
    assert expected_error in result.output
