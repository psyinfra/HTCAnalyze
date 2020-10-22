import sys
import io
from htcanalyze import main as ht


class PseudoTTY(object):

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


def reset():
    sys.stdin = PseudoTTY(copy_sys_stdin, True)
    sys.stdout = PseudoTTY(copy_sys_stdout, True)


def test_no_input_and_no_output():
    reset()
    ht.RedirectionChecker.check_for_redirection()
    assert ht.RedirectionChecker.reading_stdin is False
    assert ht.RedirectionChecker.redirecting_stdout is False


def test_input_and_no_output():
    reset()
    normal_log_str = "tests/test_logs/valid_logs/normal_log.log"
    sys.stdin = io.StringIO(normal_log_str)
    ht.RedirectionChecker.check_for_redirection()
    assert ht.RedirectionChecker.reading_stdin is True
    assert ht.RedirectionChecker.stdin_input == [normal_log_str]
    assert ht.RedirectionChecker.redirecting_stdout is False


def test_output_and_no_input():
    reset()
    sys.stdout = open('test_output.txt', 'w')
    ht.RedirectionChecker.check_for_redirection()
    assert ht.RedirectionChecker.reading_stdin is False
    assert ht.RedirectionChecker.redirecting_stdout is True


def test_input_and_output():
    reset()
    normal_log_str = "tests/test_logs/valid_logs/normal_log.log"
    sys.stdin = io.StringIO(normal_log_str)
    sys.stdout = open('test_output.txt', 'w')
    ht.RedirectionChecker.check_for_redirection()
    assert ht.RedirectionChecker.reading_stdin is True
    assert ht.RedirectionChecker.stdin_input == [normal_log_str]
    assert ht.RedirectionChecker.redirecting_stdout is True
