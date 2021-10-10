
import pytest
from htcanalyze import main as ht


# To make a copy of stdin and stdout
class PseudoTTY(object):

    def __init__(self, underlying, isset):
        self.__underlying = underlying
        self.__isset = isset

    def __getattr__(self, name):
        return getattr(self.__underlying, name)

    def isatty(self):
        return self.__isset


def test_manage_params():

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
    args = "--ext-log=.logging --ext-out=.output --ext-err=.error".split()
    res_dict = ht.manage_params(args)
    assert res_dict["ext_log"] == ".logging"
    assert res_dict["ext_out"] == ".output"
    assert res_dict["ext_err"] == ".error"

    args = "--anal --show htc-err htc-out --ignore execution-details " \
           "times errors host-nodes used-resources requested-resources " \
           "allocated-resources all-resources ram-history".split()
    res_dict = ht.manage_params(args)
    assert res_dict["show_list"] == "htc-err htc-out".split()
    assert res_dict["ignore_list"] == "execution-details times errors " \
                                      "host-nodes used-resources " \
                                      "requested-resources " \
                                      "allocated-resources " \
                                      "all-resources ram-history".split()

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

    args = "--rdns-lookup --no-config --generate-log -v".split()
    res_dict = ht.manage_params(args)
    assert res_dict["rdns_lookup"] is True
    assert res_dict["generate_log_file"] == "htcanalyze.log"
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


# Todo: other methods test
