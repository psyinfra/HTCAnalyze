import pytest
from htcanalyze.cli_argument_parser import setup_parser
from htcanalyze.globals import (
    NORMAL_EXECUTION,
    HTCANALYZE_ERROR,
    EXT_LOG_DEFAULT,
    EXT_OUT_DEFAULT,
    EXT_ERR_DEFAULT,
    ALLOWED_SHOW_VALUES,
)


@pytest.fixture(scope="function")
def parser():
    parser = setup_parser()
    parser.ignore_configs()
    return parser


def test_version(parser):
    params = parser.get_params()
    assert params.version is False
    args = "--version".split()
    params = parser.get_params(args)
    assert params.version is True


def test_help(parser):
    args = "-h".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        parser.get_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == NORMAL_EXECUTION
    args = "--help".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        parser.get_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == NORMAL_EXECUTION


def test_paths(parser):
    args = "somepath".split()
    params = parser.get_params(args)
    assert params.paths == args

    args = "path1 path2 path3".split()
    params = parser.get_params(args)
    assert params.paths == args


def test_extensions(parser):
    params = parser.get_params()
    assert params.ext_log == EXT_LOG_DEFAULT
    assert params.ext_out == EXT_OUT_DEFAULT
    assert params.ext_err == EXT_ERR_DEFAULT
    args = "--ext-log=.logging --ext-out=.output --ext-err=.error".split()
    params = parser.get_params(args)
    assert params.ext_log == ".logging"
    assert params.ext_out == ".output"
    assert params.ext_err == ".error"


def test_analyze(parser):
    params = parser.get_params()
    assert params.analyze is False
    args = "--analyze".split()
    params = parser.get_params(args)
    assert params.analyze is True


def test_show(parser):
    params = parser.get_params()
    assert params.show_list == []
    args = "--show".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        parser.get_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == HTCANALYZE_ERROR

    args = "--show something".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        parser.get_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == HTCANALYZE_ERROR

    args = "--show".split()
    args.extend(ALLOWED_SHOW_VALUES)
    params = parser.get_params(args)
    assert params.show_list == ALLOWED_SHOW_VALUES


def test_rdns_lookup(parser):
    params = parser.get_params()
    assert params.rdns_lookup is False
    args = "--rdns-lookup".split()
    params = parser.get_params(args)
    assert params.rdns_lookup is True


def test_ignore_config(parser):
    params = parser.get_params()
    assert params.ignore_config is False
    args = "--ignore-config".split()
    params = parser.get_params(args)
    assert params.ignore_config is True


def test_config(parser):
    params = parser.get_params()
    assert params.config is None
    args = "-c tests/test_configs/test.conf".split()
    params = parser.get_params(args)
    assert params.config == "tests/test_configs/test.conf"
    assert params.tolerated_usage == 0.25
    assert params.bad_usage == 0.4
    assert params.recursive is True
    assert params.rdns_lookup is True
    assert params.show_list == [""]
    assert params.ext_log == ".logging"
    assert params.ext_out == ".output"
    assert params.ext_err == ".error"


def test_config_with_ignore_config(parser):
    args = "-c tests/test_configs/test.conf --ignore-config".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        parser.get_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == HTCANALYZE_ERROR


def test_unknown_arg(parser):
    args = "--what_is_this".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        parser.get_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == HTCANALYZE_ERROR
