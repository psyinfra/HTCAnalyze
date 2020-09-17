
import sys
import pytest
import io
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

def test_check_for_redirection():

    # sys.stdin = io.StringIO('file1 file2')
    # sys.stdin.__setattr__('isatty()', True)
    # setattr(sys.stdin, 'isatty', True)

    # test all cases of different redirection combinations
    sys.stdin = PseudoTTY(sys.stdin, True)
    sys.stdout = PseudoTTY(sys.stdout, True)
    ht.check_for_redirection()
    assert ht.GlobalServant.reading_stdin is False \
           and ht.GlobalServant.redirecting_stdout is False

    sys.stdin = io.StringIO('Some file')
    sys.stdout = PseudoTTY(sys.stdout, True)
    ht.check_for_redirection()
    assert ht.GlobalServant.reading_stdin is True \
           and ht.GlobalServant.redirecting_stdout is False

    sys.stdin = PseudoTTY(sys.stdin, True)
    sys.stdout = PseudoTTY(sys.stdout, False)
    ht.check_for_redirection()
    assert ht.GlobalServant.reading_stdin is False \
           and ht.GlobalServant.redirecting_stdout is True

    sys.stdin = io.StringIO('Some file')
    sys.stdout = PseudoTTY(sys.stdout, False)
    ht.check_for_redirection()
    assert ht.GlobalServant.reading_stdin is True \
           and ht.GlobalServant.redirecting_stdout is True

    # lastly check if all COLORS are set to ""
    assert ht.COLORS == {
        'red': "",
        'green': "",
        'yellow': "",
        'magenta': "",
        'cyan': "",
        'blue': "",
        'light_grey': "",
        'back_to_default': ""
    }


def test_reverse_dns_lookup():
    ht.gethostbyaddr("172.217.0.0")
    assert ht.GlobalServant.store_dns_lookups["172.217.0.0"]\
           == "ord38s04-in-f0.1e100.net"
    ht.gethostbyaddr("NoIP")
    assert ht.GlobalServant.store_dns_lookups["NoIP"] == "NoIP"


def test_manage_params():
    pass  # Todo

    # test exit params
    args = "--print-event-table".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.manage_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0
    args = "--version".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.manage_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0
    args = "--help".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.manage_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    # normal parameters
    args = "--std-log=.logging --std-out=.output --std-err=.error".split()
    ht.manage_params(args)
    assert ht.GlobalServant.std_log == ".logging"
    assert ht.GlobalServant.std_out == ".output"
    assert ht.GlobalServant.std_err == ".error"

    # args = "--std-log=logging --std-out=output --std-err=error tests/test_logs/valid_logs".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.std_log == ".logging"
    # assert ht.GlobalServant.std_out == ".output"
    # assert ht.GlobalServant.std_err == ".error"
    # # files are set globaly so no more system exit is raised
    # args = "--std-log logging --std-out output --std-err error".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.std_log == ".logging"
    # assert ht.GlobalServant.std_out == ".output"
    # assert ht.GlobalServant.std_err == ".error"
    #
    # args = "--show-more std-err,std-out --ignore execution-details," \
    #        "times,errors,host-nodes,used-resources," \
    #        "requested-resources,allocated-resources,all-resources".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.show_list == "std-err,std-out".split(',')
    # assert ht.GlobalServant.ignore_list == "execution-details,times,errors,host-nodes," \
    #                          "used-resources,requested-resources," \
    #                          "allocated-resources,all-resources".split(',')
    # args = "--table-format=plain --table-format simple --table-format github".split()
    # ht.manage_params(args)
    # assert ht.table_format == "github"
    # args = "--table-format=None".split()
    # ht.manage_params(args)
    # assert ht.table_format == "github"  # should still be github
    #
    # args = "--reverse-dns-lookup --no-config --generate-log -v".split()
    # ht.manage_params(args)
    # assert ht.reverse_dns_lookup is True
    #
    # args = "--what_is_this".split()
    # with pytest.raises(SystemExit) as pytest_wrapped_e:
    #     ht.manage_params(args)
    # assert pytest_wrapped_e.type == SystemExit
    # assert pytest_wrapped_e.value.code == 1
    #
    # args = "--mode whatever".split()
    # with pytest.raises(SystemExit) as pytest_wrapped_e:
    #     ht.manage_params(args)
    # assert pytest_wrapped_e.type == SystemExit
    # assert pytest_wrapped_e.value.code == 1
    #
    # args = "--mode default".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "default"
    # args = "--mode d".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "default"
    # args = "-m default".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "default"
    # args = "-m d".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "default"
    #
    # # all ways to start analyser mode
    # args = "-a".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "analyse"
    # args = "--mode analyse".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "analyse"
    # args = "--mode a".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "analyse"
    # args = "-m analyse".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "analyse"
    # args = "-m a".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "analyse"
    #
    # # all ways to start summarizer mdoe
    # args = "-s".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "summarize"
    # args = "--mode summarize".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "summarize"
    # args = "--mode s".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "summarize"
    # args = "-m summarize".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "summarize"
    # args = "-m s".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "summarize"
    #
    # # all ways to start the analysed-summary mode
    # args = "-as".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "analysed-summary"
    # args = "--mode analysed-summary".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "analysed-summary"
    # ht.GlobalServant.mode = None
    # args = "--mode as".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "analysed-summary"
    # args = "-m analysed-summary".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "analysed-summary"
    # args = "-m as".split()
    # ht.manage_params(args)
    # assert ht.GlobalServant.mode == "analysed-summary"



# Todo: other methods test