from setuptools import setup
import os

VERSION = "1.0"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="sqlite-transform",
    description="Tool for running transformations on columns in a SQLite database.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/sqlite-transform",
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["sqlite_transform"],
    entry_points="""
        [console_scripts]
        sqlite-transform=sqlite_transform.cli:cli
    """,
    install_requires=["dateutils", "tqdm", "click", "sqlite-utils"],
    extras_require={"test": ["pytest"]},
    tests_require=["sqlite-transform[test]"],
)
