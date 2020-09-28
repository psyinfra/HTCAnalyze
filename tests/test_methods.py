
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
    ht.GlobalServant.check_for_redirection()
    assert ht.GlobalServant.reading_stdin is False \
           and ht.GlobalServant.redirecting_stdout is False

    sys.stdin = io.StringIO('Some file')
    sys.stdout = PseudoTTY(sys.stdout, True)
    ht.GlobalServant.check_for_redirection()
    assert ht.GlobalServant.reading_stdin is True \
           and ht.GlobalServant.redirecting_stdout is False

    sys.stdin = PseudoTTY(sys.stdin, True)
    sys.stdout = PseudoTTY(sys.stdout, False)
    ht.GlobalServant.check_for_redirection()
    assert ht.GlobalServant.reading_stdin is False \
           and ht.GlobalServant.redirecting_stdout is True

    sys.stdin = io.StringIO('Some file')
    sys.stdout = PseudoTTY(sys.stdout, False)
    ht.GlobalServant.check_for_redirection()
    assert ht.GlobalServant.reading_stdin is True \
           and ht.GlobalServant.redirecting_stdout is True


def test_reverse_dns_lookup():
    ht.GlobalServant.reset()
    ht.gethostbyaddr("172.217.0.0")
    assert ht.GlobalServant.store_dns_lookups["172.217.0.0"]\
           == "ord38s04-in-f0.1e100.net"
    ht.gethostbyaddr("NoIP")
    assert ht.GlobalServant.store_dns_lookups["NoIP"] == "NoIP"


def test_manage_params():
    ht.GlobalServant.reset()

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

    args = "--show std-err std-out --ignore execution-details " \
           "times errors host-nodes used-resources " \
           "requested-resources allocated-resources all-resources".split()
    res_dict = ht.manage_params(args)
    assert res_dict["show_list"] == "std-err std-out".split()
    assert res_dict["ignore_list"] == "execution-details times errors " \
                                      "host-nodes used-resources " \
                                      "requested-resources " \
                                      "allocated-resources " \
                                      "all-resources".split()

    args = "--show something".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.manage_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    args = "--ignore something".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.manage_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    args = "--reverse-dns-lookup --no-config --generate-log -v".split()
    res_dict = ht.manage_params(args)
    assert ht.GlobalServant.reverse_dns_lookup is True
    assert res_dict["generate_log_file"] == "htcompact.log"
    assert res_dict["verbose"] is True

    args = "--what_is_this".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.manage_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    args = "--mode whatever".split()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.manage_params(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    args = "--mode default".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "default"
    args = "--mode d".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "default"
    args = "-m default".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "default"
    args = "-m d".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "default"

    # all ways to start analyser mode
    args = "-a".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "analyse"
    args = "--mode analyse".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "analyse"
    args = "--mode a".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "analyse"
    args = "-m analyse".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "analyse"
    args = "-m a".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "analyse"

    # all ways to start summarizer mdoe
    args = "-s".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "summarize"
    args = "--mode summarize".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "summarize"
    args = "--mode s".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "summarize"
    args = "-m summarize".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "summarize"
    args = "-m s".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "summarize"

    # all ways to start the analysed-summary mode
    args = "-as".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "analysed-summary"
    args = "--mode analysed-summary".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "analysed-summary"
    res_dict["mode"] = None
    args = "--mode as".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "analysed-summary"
    args = "-m analysed-summary".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "analysed-summary"
    args = "-m as".split()
    res_dict = ht.manage_params(args)
    assert res_dict["mode"] == "analysed-summary"



# Todo: other methods test