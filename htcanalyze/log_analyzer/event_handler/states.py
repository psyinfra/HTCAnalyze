"""State Module."""
from abc import ABC


class State(ABC):
    _name: str

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def __eq__(self, other):
        return isinstance(self, other.__class__)

    def __hash__(self):
        """Use class name as hash to use states as dictionary keys."""
        return hash(self.__class__.name)


class JobState(State, ABC):
    _color: str = None

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color


class TerminationState(JobState, ABC):
    pass


class NormalTerminationState(TerminationState):

    def __init__(self):
        self.color = "green"
        self.name = "NORMAL_TERMINATION"


class AbnormalTerminationState(TerminationState):

    def __init__(self):
        self.color = "red"
        self.name = "ABNORMAL_TERMINATION"


class ExecutionState(JobState, ABC):

    def __init__(self):
        self.color = "blue"


class WaitingState(ExecutionState):

    def __init__(self):
        super().__init__()
        self.name = "WAITING"


class RunningState(ExecutionState):

    def __init__(self):
        super().__init__()
        self.name = "RUNNING"


class ErrorState(State, ABC):

    def __init__(self):
        self.color = "red"


class ErrorWhileReadingState(JobState, ErrorState):

    def __init__(self):
        super().__init__()
        self.name = "ERROR_WHILE_READING"


class InvalidHostAddressState(ErrorState):

    def __init__(self):
        super().__init__()
        self.name = "INVALID_HOST_ADDRESS"


class InvalidUserAddressState(ErrorState):

    def __init__(self):
        super().__init__()
        self.name = "INVALID_USER_ADDRESS"


class AbortedState(TerminationState, ErrorState):

    def __init__(self):
        super().__init__()
        self.name = "ABORTED"


class JobHeldState(ErrorState):

    def __init__(self):
        super().__init__()
        self.name = "JOB_HELD"


class ShadowExceptionState(ErrorState):

    def __init__(self):
        super().__init__()
        self.name = "SHADOW_EXCEPTION"
