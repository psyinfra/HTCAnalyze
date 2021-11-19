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


copy_sys_stdout = sys.stdout
copy_sys_stdin = sys.stdin


def reset_decorator(func):
    """
    Reset sys.stdout and sys.stdin to default.

    Does not work with pytest.fixture, as pytest manipulates stdout
    """
    def reset():
        """Resets stdin/stdout to initial."""
        sys.stdout = PseudoTTY(copy_sys_stdout, True)
        sys.stdin = PseudoTTY(copy_sys_stdin, True)

    def call_func():
        """Calls reset before and after executing a function"""
        reset()
        func()
        reset()

    return call_func()


@reset_decorator
def test_no_input_and_no_output():
    redirecting_stdout, reading_stdin, std_in = ht.check_for_redirection()
    assert redirecting_stdout is False
    assert reading_stdin is False
    assert std_in is None


@reset_decorator
def test_input_and_no_output():
    normal_log_str = "tests/test_logs/valid_logs/normal_log.log"
    sys.stdin = io.StringIO(normal_log_str)
    redirecting_stdout, reading_stdin, std_in = ht.check_for_redirection()
    assert redirecting_stdout is False
    assert reading_stdin is True
    assert std_in == [normal_log_str]


@reset_decorator
def test_output_and_no_input():
    sys.stdout = open('test_output.txt', 'w')
    redirecting_stdout, reading_stdin, std_in = ht.check_for_redirection()
    assert redirecting_stdout is True
    assert reading_stdin is False
    assert std_in is None


@reset_decorator
def test_input_and_output():
    normal_log_str = "tests/test_logs/valid_logs/normal_log.log"
    sys.stdin = io.StringIO(normal_log_str)
    sys.stdout = open('test_output.txt', 'w')
    redirecting_stdout, reading_stdin, std_in = ht.check_for_redirection()
    assert redirecting_stdout is True
    assert reading_stdin is True
    assert std_in == [normal_log_str]
