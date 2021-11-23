"""Test module."""


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