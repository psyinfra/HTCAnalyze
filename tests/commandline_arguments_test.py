"""Coverage test."""

import sys
import pytest
from htcanalyze import main as ht


class PseudoTTY(object):
    """Pseudo terminal."""

    def __init__(self, underlying, isset):
        """

        :param underlying:
        :param isset:
        """
        self.__underlying = underlying
        self.__isset = isset

    def __getattr__(self, name):
        """

        :param name:
        :return:
        """
        return getattr(self.__underlying, name)

    def isatty(self):
        """

        :return:
        """
        return self.__isset


copy_sys_stdin = sys.stdin
copy_sys_stdout = sys.stdout
sys.stdin = PseudoTTY(copy_sys_stdin, True)
sys.stdout = PseudoTTY(copy_sys_stdout, True)


def _help():
    args = "-h".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def _version():
    args = "--version".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_exit_opts():
    _help()
    _version()


def test_wrong_opts_or_args():
    args = "--abs"  # not a list
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    args = "--abc".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    # wrong ignore value
    args = "--ignore None ".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    # wrong show value
    args = "--show None ".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    # Argument starts with -,
    # this will not raise an error, but is considered sceptical
    args = "--ext-log -log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2


def test_show_values():

    # analyze
    args = "tests/test_logs/valid_logs/normal_log.log " \
           "tests/test_logs/valid_logs/gpu_usage.log " \
           "--show htc-err htc-out --one-by-one".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0  # no valid file is given


def test_ignore_values():
    args = "--ignore execution-details times host-nodes " \
           "used-resources requested-resources allocated-resources " \
           "all-resources errors ram-history " \
           "-f tests/test_logs/valid_logs/gpu_usage.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_independent_opts():
    args = "--ext-log=.log --ext-out=.output " \
           "--ext-err=.error --rdns-lookup".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1  # no valid file is given

    args = "--ext-log log --ext-out output " \
           "--ext-err error " \
           "--rdns-lookup tests/test_logs/valid_logs".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "--recursive --bad-usage 0.3 --tolerated-usage 0.1" \
           " tests/test_logs".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_analyze_mode():

    args = "--one-by-one tests/test_logs/valid_" \
           "logs/aborted_before_submission.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    # dictionary
    sys.stdout = open('test_output.txt', 'w')
    args = "--one-by-one tests/test_logs/valid_logs/normal_log.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_analyzed_summary():
    args = "tests/test_logs/valid_logs/aborted_before_submission.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "tests/test_logs/valid_logs".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_filter_mode():

    args = "tests/test_logs/valid_logs --filter err".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "--filter err -f tests/test_logs/valid_logs/gpu_usage.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def _all_modes_by_logfiles(logfile, return_value):
    args = [logfile, "--no-config", "-v"]
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == return_value

    ht.input = lambda x: 'y'
    args = ["--one-by-one", logfile, "--no-config"]
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == return_value

    args = [logfile, "--no-config"]
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == return_value


def test_all_modes_by_valid_logs():
    folder = "tests/test_logs/valid_logs/"
    _all_modes_by_logfiles(folder, 0)


def test_all_modes_by_faulty_logs():
    folder = "tests/test_logs/faulty_logs/"
    _all_modes_by_logfiles(folder, 0)


def test_all_modes_by_exception_logs():
    folder = "tests/test_logs/faulty_resource_logs"
    _all_modes_by_logfiles(folder, 0)


def test_missing_lines():
    pass
