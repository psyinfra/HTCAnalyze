"""Blackbox tests with test files."""

import sys
import pytest
from io import StringIO
from rich.console import Console
from htcanalyze.globals import NORMAL_EXECUTION
from htcanalyze.main import run
from .redirection_test import PseudoTTY


# needed because stdin is set from pytest
# sys.stdin = PseudoTTY(sys.stdin, True)


# @pytest.fixture(scope="module")
# def console():
#     return Console(file=StringIO())


def run_htcanalyze(paths, *args):
    cli_args = paths
    if isinstance(paths, str):
        cli_args = [paths]
    cli_args.extend(list(*args))
    run(cli_args)


def test_valid_files_summarized():
    # monkeypatch.setattr("builtins.input", lambda _: None)
    paths = "tests/test_logs/valid_logs"
    # default summarization
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        run_htcanalyze(paths)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == NORMAL_EXECUTION
    # summarization with a bunch of args
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        run_htcanalyze(
            paths,
            "--rdns-lookup "
            "--tolerated-usage 0.2 "
            "--bad-usage 0.35".split()
        )
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == NORMAL_EXECUTION


def test_valid_files_analyzed():
    paths = "tests/test_logs/valid_logs"
    # default analysis
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        run_htcanalyze(paths, ["--analyze"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == NORMAL_EXECUTION
    # analysis with a bunch of args
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        run_htcanalyze(
            paths,
            "--analyze "
            "--show htc-err htc-out "
            "--rdns-lookup "
            "--tolerated-usage 0.2 "
            "--bad-usage 0.35".split()
        )
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == NORMAL_EXECUTION




