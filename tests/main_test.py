
import pytest
from htcanalyze.main import HTCAnalyzeTerminationEvent
from htcanalyze.globals import NORMAL_EXECUTION, HTCANALYZE_ERROR


# To make a copy of stdin and stdout
class PseudoTTY(object):

    def __init__(self, underlying, isset):
        self.__underlying = underlying
        self.__isset = isset

    def __getattr__(self, name):
        return getattr(self.__underlying, name)

    def isatty(self):
        return self.__isset


# Todo: other methods test
