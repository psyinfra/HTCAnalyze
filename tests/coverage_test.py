
import sys
import io
import pytest
import imp
ht = imp.load_source('htcompact', 'htcompact')


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

    # Argument starts with -, this will not raise an error, but is considered sceptical
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
           "all-resources errors -as tests/test_logs/valid_logs/gpu_usage.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_independent_opts():
    args = "--std-log=.log --std-out=.output " \
           "--std-err=.error --reverse-dns-lookup".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert ht.GlobalServant.std_log == ".log"
    assert ht.GlobalServant.std_err == ".error"
    assert ht.GlobalServant.std_out == ".output"
    assert ht.GlobalServant.reverse_dns_lookup is True
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1  # no valid file is given

    args = "--std-log log --std-out output " \
           "--std-err error " \
           "--reverse-dns-lookup tests/test_logs/valid_logs".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert ht.GlobalServant.std_log == ".log"
    assert ht.GlobalServant.std_err == ".error"
    assert ht.GlobalServant.std_out == ".output"
    assert ht.GlobalServant.reverse_dns_lookup is True
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_default_mode():
    args = "tests/test_logs/valid_logs/aborted_before_submission.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "--mode default tests/test_" \
           "logs/valid_logs/aborted_before_submission.log".split()
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
    ht.input = lambda x: 'y'
    args = "-m a tests/test_logs/valid_logs/".split()
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

    sys.stdin = PseudoTTY(copy_sys_stdin, True)
    sys.stdout = PseudoTTY(copy_sys_stdout, True)

    ht.input = lambda x: 'd'
    args = "tests/test_logs/valid_logs --filter gpu --extend".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert ht.GlobalServant.reading_stdin is False\
           and ht.GlobalServant.redirecting_stdout is False
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    ht.input = lambda x: 'a'
    args = "tests/test_logs/valid_logs --filter gpu --extend".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert ht.GlobalServant.reading_stdin is False \
           and ht.GlobalServant.redirecting_stdout is False
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    ht.input = lambda x: 's'
    args = "tests/test_logs/valid_logs --filter gpu --extend".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert ht.GlobalServant.reading_stdin is False\
           and ht.GlobalServant.redirecting_stdout is False
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    ht.input = lambda x: 'as'
    args = "tests/test_logs/valid_logs --filter gpu --extend".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert ht.GlobalServant.reading_stdin is False \
           and ht.GlobalServant.redirecting_stdout is False
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    ht.input = lambda x: 'e'
    args = "tests/test_logs/valid_logs --filter gpu --extend".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert ht.GlobalServant.reading_stdin is False \
           and ht.GlobalServant.redirecting_stdout is False
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "--filter gpu -a tests/test_logs/valid_logs/gpu_usage.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "--filter gpu -as tests/test_logs/valid_logs/gpu_usage.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "--filter gpu -s tests/test_logs/valid_logs/gpu_usage.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    args = "--filter gpu --mode default" \
           " tests/test_logs/valid_logs/gpu_usage.log".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_redirection():
    # test stdout
    sys.stdout = open('test_output.txt', 'w')
    args = "tests/test_logs/valid_logs/ --filter gpu".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert ht.GlobalServant.reading_stdin is False
    assert ht.GlobalServant.redirecting_stdout is True
    assert pytest_wrapped_e.value.code == 0

    sys.stdout = open('test_output.txt', 'w')
    args = "-a tests/test_logs/valid_logs/".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert pytest_wrapped_e.type == SystemExit
    assert ht.GlobalServant.reading_stdin is False
    assert ht.GlobalServant.redirecting_stdout is True
    assert pytest_wrapped_e.value.code == 0

    sys.stdout = PseudoTTY(copy_sys_stdout, True)  # change back to not redirecting

    # test stdin
    sys.stdin = io.StringIO('tests/test_logs/valid_logs/gpu_usage.log')
    args = "-a --std-log=.logging".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert ht.GlobalServant.redirecting_stdout is False
    assert ht.GlobalServant.reading_stdin is True
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1  # because std_log is .logging

    sys.stdin = io.StringIO('tests/test_logs/valid_logs')
    args = "--filter gpu --std-log=.logging -a".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert ht.GlobalServant.redirecting_stdout is False
    assert ht.GlobalServant.reading_stdin is True
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    sys.stdin = PseudoTTY(copy_sys_stdin, True)  # change back

    # test both
    sys.stdout = open('test_output.txt', 'w')
    sys.stdin = io.StringIO('tests/test_logs/valid_logs')
    args = "--filter gpu --std-log=.logging -a".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.run(args)
    assert ht.GlobalServant.redirecting_stdout is True
    assert ht.GlobalServant.reading_stdin is True
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    # change back to default
    sys.stdout = PseudoTTY(copy_sys_stdout, True)
    sys.stdin = PseudoTTY(copy_sys_stdin, True)


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