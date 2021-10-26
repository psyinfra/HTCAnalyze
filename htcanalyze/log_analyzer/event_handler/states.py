"""State Module."""
from abc import ABC


class State(ABC):
    pass


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


class AbnormalTerminationState(TerminationState):

    def __init__(self):
        self.color = "red"


class ExecutionState(JobState, ABC):

    def __init__(self):
        self.color = "blue"


class WaitingState(ExecutionState):
    pass


class RunningState(ExecutionState):
    pass


class ErrorState(State, ABC):

    def __init__(self):
        self.color = "red"


class ErrorWhileReadingState(JobState, ErrorState):
    pass


class InvalidHostAddressState(ErrorState):
    pass


class InvalidUserAddressState(ErrorState):
    pass


class AbortedState(TerminationState, ErrorState):
    pass


class JobHeldState(ErrorState):
    pass


class ShadowExceptionState(ErrorState):
    pass


