
import sys
import pytest
import mock
import io
import imp
ht = imp.load_source('htcompact', 'script/htcompact')


# To make a copy of stdin and stdout
class PseudoTTY(object):

    def __init__(self, underlying, isset):
        self.__underlying = underlying
        self.__isset = isset

    def __getattr__(self, name):
        return getattr(self.__underlying, name)

    def isatty(self):
        return self.__isset


def test_initialize():
    ht.initialize()
    assert ht.accepted_states == ["true", "yes", "y", "ja", "j", "enable", "enabled", "wahr", "0"]
    assert type(ht.files) == list
    assert ht.option_shorts == "hsavm:"
    assert ht.option_longs == ["help", "version", "verbose", "mode=",
                               "std-log=", "std-err=", "std-out=",
                               "ignore=", "show-more=", "no-config", "to-csv",
                               "generate-log-file", "filter=", "extend", "print-event-table",
                               "reverse-dns-lookup", "table-format="]

    assert ht.mode is None
    assert ht.allowed_modes == {"a": "analyse",
                                "s": "summarize",
                                "as": "analysed-summary",
                                "d": "default"}

    assert type(ht.show_list) == list
    assert ht.allowed_show_values == ["errors", "warnings", "output"]

    assert type(ht.ignore_list) == list
    assert ht.allowed_ignore_values == ["execution-details", "times",
                                        "gpu", "cpu", "host-nodes",
                                        "used-resources", "requested-resources",
                                        "allocated-resources", "all-resources",
                                        "errors", "warnings"]
    assert ht.no_config is False

    # Features:
    assert ht.reverse_dns_lookup is False
    assert type(ht.store_dns_lookups) == dict
    assert ht.to_csv is False

    # logging tool
    assert ht.generate_log_file is False
    assert ht.verbose_mode is False

    # filter mode
    assert ht.filter_mode is False
    assert ht.filter_keywords == ""
    assert ht.filter_extended is False

    # escape sequences for colors
    assert ht.colors == {
        'red': "\033[0;31m",
        'green': "\033[0;32m",
        'yellow': "\033[0;33m",
        'magenta': "\033[0;35m",
        'cyan': "\033[0;36m",
        'blue': "\033[0;34m",
        'light_grey': "\033[37m",
        'back_to_default': "\033[0;39m"
    }

    # thresholds for bad and low usage of resources
    assert ht.low_usage_threshold == 0.75
    assert ht.bad_usage_threshold == 1.2

    # global variables with default values for err/log/out files
    assert ht.std_log == ".log"
    assert ht.std_err == ".err"
    assert ht.std_out == ".out"

    # global defaults
    assert ht.default_configfile == "htcompact.conf"
    assert ht.table_format == "pretty"  # ascii by default

    assert ht.reading_stdin is False
    assert ht.redirecting_output is False


def test_remove_files_from_args():
    test_initialize()  # first we need to initialize, so we go with the initialize test

    # Now test all the valid long options
    test_all_longs = "--help --version --verbose --mode=anymode --std-log .log --std-err=.err --std-out=.out " \
                     "--ignore -mich  file1 --show-more=alles --no-config --to-csv file2 --generate-log-file " \
                     "--filter Gpu --extend --print-event-table " \
                     "--reverse-dns-lookup --table-format=haesslig file3 file4".split()
    new_args = ht.remove_files_from_args(test_all_longs, ht.option_shorts, ht.option_longs)
    assert ht.files == ["file1", "file2", "file3", "file4"]
    assert new_args == "--help --version --verbose --mode=anymode --std-log .log --std-err=.err --std-out=.out " \
                       "--ignore -mich --show-more=alles --no-config --to-csv --generate-log-file " \
                       "--filter Gpu --extend --print-event-table " \
                       "--reverse-dns-lookup --table-format=haesslig".split()

    # Now test all the valid short opts
    test_all_shorts = "-h -a file1 -s -v file2 -m default file3".split()
    new_args = ht.remove_files_from_args(test_all_shorts, ht.option_shorts, ht.option_longs)
    assert ht.files == ["file1", "file2", "file3"]
    assert new_args == "-h -a -s -v -m default".split()

    # Now test an option which needs an argument, but without
    test_no_argument = "file1 --ignore".split()
    new_args = ht.remove_files_from_args(test_no_argument, ht.option_shorts, ht.option_longs)
    assert ht.files == ["file1"]
    assert new_args == "--ignore".split()
    # If no file is given, the list should not be touched and still hold files (if given by config)
    test_no_file = "--mode analyse".split()
    new_args = ht.remove_files_from_args(test_no_file, ht.option_shorts, ht.option_longs)
    assert ht.files == ["file1"]
    assert new_args == "--mode analyse".split()

    # Now test an other option, where an argument is requested
    test_option_as_argument = "--mode --verbose".split()
    new_args = ht.remove_files_from_args(test_option_as_argument, ht.option_shorts, ht.option_longs)
    assert ht.files == ["file1"]
    assert new_args == "--mode --verbose".split()  # This is true, --verbose will be interpreted as an argument

    # Test option which are not specified by option_shorts or option_longs
    test_not_know_options = "--symmetric=False -w all --all-your-fault".split()
    new_args = ht.remove_files_from_args(test_not_know_options, ht.option_shorts, ht.option_longs)
    # Should still be interpreted as options, but without the knowledge of arguments
    assert ht.files == ["all"]
    assert new_args == "--symmetric=False -w --all-your-fault".split()

    # error test
    test_error_handling = "param"
    with pytest.raises(ValueError):
        ht.remove_files_from_args(test_error_handling, ht.option_shorts, ht.option_longs)


def test_check_for_redirection():
    test_initialize()

    # sys.stdin = io.StringIO('file1 file2')
    # sys.stdin.__setattr__('isatty()', True)
    # setattr(sys.stdin, 'isatty', True)

    # test all cases of different redirection combinations
    sys.stdin = PseudoTTY(sys.stdin, True)
    sys.stdout = PseudoTTY(sys.stdout, True)
    ht.check_for_redirection()
    assert ht.reading_stdin is False and ht.redirecting_output is False

    sys.stdin = PseudoTTY(sys.stdin, False)
    sys.stdout = PseudoTTY(sys.stdout, True)
    ht.check_for_redirection()
    assert ht.reading_stdin is True and ht.redirecting_output is False

    sys.stdin = PseudoTTY(sys.stdin, True)
    sys.stdout = PseudoTTY(sys.stdout, False)
    ht.check_for_redirection()
    assert ht.reading_stdin is False and ht.redirecting_output is True

    sys.stdin = PseudoTTY(sys.stdin, False)
    sys.stdout = PseudoTTY(sys.stdout, False)
    ht.check_for_redirection()
    assert ht.reading_stdin is True and ht.redirecting_output is True

    # lastly check if all colors are set to ""
    assert ht.colors == {
        'red': "",
        'green': "",
        'yellow': "",
        'magenta': "",
        'cyan': "",
        'blue': "",
        'light_grey': "",
        'back_to_default': ""
    }


def test_manage_prioritized_params():
    test_initialize()

    # test exit params

    test_help = ["-h", '--help']
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.manage_prioritized_params(test_help)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    test_version = ["--version"]
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.manage_prioritized_params(test_version)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    test_event_table = ["--print-event-table"]
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ht.manage_prioritized_params(test_event_table)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    # test all prioritised params

    test_version = ["-v", "--verbose", "--no-config", "--generate-log-file"]
    ht.manage_prioritized_params(test_version)
    assert ht.verbose_mode is True
    assert ht.no_config is True
    assert ht.generate_log_file is True
    assert ht.logging.getLogger().disabled is False

    # error testing

    test_error = "asd"
    with pytest.raises(ValueError):
        ht.manage_prioritized_params(test_error)


# Todo: other methods test