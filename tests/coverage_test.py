
import sys
import pytest
from htcompact import main as ht


# To make a copy of stdin and stdout
class PseudoTTY(object):

    def __init__(self, underlying, isset):
        self.__underlying = underlying
        self.__isset = isset

    def __getattr__(self, name):
        return getattr(self.__underlying, name)

    def isatty(self):
        return self.__isset


# print("Stdin is set: ",sys.stdin.isatty())
# sdtin and stdout isatty should return true
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

    args = "--mode=None".split()
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

    # wrong show-more value
    args = "--show-more None ".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    # Argument starts with -,
    # this will not raise an error, but is considered sceptical
    args = "--std-log -log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2


def test_show_values():
    # default
    args = "tests/test_logs/valid_logs/normal_log.log " \
           "tests/test_logs/valid_logs/gpu_usage.log " \
           "--show std-err std-out".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0  # no valid file is given

    # analyse
    args = "tests/test_logs/valid_logs/normal_log.log " \
           "tests/test_logs/valid_logs/gpu_usage.log " \
           "--show std-err std-out -a".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0  # no valid file is given


def test_ignore_values():
    args = "--ignore execution-details times host-nodes " \
           "used-resources requested-resources allocated-resources " \
           "all-resources errors -as " \
           "tests/test_logs/valid_logs/gpu_usage.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_independent_opts():
    args = "--std-log=.log --std-out=.output " \
           "--std-err=.error --reverse-dns-lookup".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1  # no valid file is given

    args = "--std-log log --std-out output " \
           "--std-err error " \
           "--reverse-dns-lookup tests/test_logs/valid_logs".split()
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


def test_default_mode():
    args = "tests/test_logs/valid_logs/aborted_before_submission.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "--mode default tests/test_" \
           "logs/valid_logs".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_analyser_mode():

    args = "--mode analyse tests/test_logs/valid_" \
           "logs/aborted_before_submission.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    # dictionary
    sys.stdout = open('test_output.txt', 'w')
    args = "-m a tests/test_logs/valid_logs/normal_log.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_summarizer_mode():
    # single files
    args = "--mode summarize tests/test_" \
           "logs/valid_logs/aborted_before_submission.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    # dictionary
    args = "-m s tests/test_logs/valid_logs/".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_analysed_summary():
    args = "--mode analysed-summary " \
           "tests/test_logs/valid_logs/aborted_before_submission.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "-m analysed-summary tests/test_logs/valid_logs".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_filter_mode():

    args = "tests/test_logs/valid_logs --filter err --extend".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "--filter err -a tests/test_logs/valid_logs/gpu_usage.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "--filter err -as tests/test_logs/valid_logs/gpu_usage.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "--filter err -s tests/test_logs/valid_logs/gpu_usage.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "--filter err --mode default" \
           " tests/test_logs/valid_logs/gpu_usage.log".split()
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
    args = ["-a", logfile, "--no-config"]
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == return_value

    args = ["-s", logfile, "--no-config"]
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == return_value

    args = ["-as", logfile, "--no-config"]
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
