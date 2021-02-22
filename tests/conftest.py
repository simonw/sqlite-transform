import pathlib
import pytest
import sqlite_utils


@pytest.fixture
def test_db_and_path(fresh_db_and_path):
    db, db_path = fresh_db_and_path
    db["example"].insert_all(
        [
            {"id": 1, "dt": "5th October 2019 12:04"},
            {"id": 2, "dt": "6th October 2019 00:05:06"},
            {"id": 3, "dt": ""},
            {"id": 4, "dt": None},
        ],
        pk="id",
    )
    return db, db_path


@pytest.fixture
def fresh_db_and_path(tmpdir):
    db_path = str(pathlib.Path(tmpdir) / "data.db")
    db = sqlite_utils.Database(db_path)
    return db, db_path
